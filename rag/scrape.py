import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
from .ollama_utils import generate_embedding, run_gemma3n
from .milvus_utils import insert_embeddings, register_index
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from docling.document_converter import DocumentConverter
except ImportError:
    DocumentConverter = None  # Docling must be installed

MAX_CONCURRENCY = 5
REQUEST_DELAY = 1  # seconds between requests to same domain
MAX_DEPTH = 2  # How deep to crawl
# Increase chunk size to better utilize Gemma 3n's 128K context window
CHUNK_SIZE = 8192  # Number of characters per chunk (was 512)
SUPPORTED_FILE_EXTS = [".pdf", ".xml", ".docx", ".xlsx", ".csv", ".html", ".htm"]
LOG_FILE = "search_index.log"


def log_admin(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {msg}\n")


def download_file(url, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)
    local_filename = os.path.join(dest_folder, url.split('/')[-1])
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename, None
    except Exception as e:
        return None, str(e)


def process_files_with_docling(file_paths, max_workers=4):
    if not DocumentConverter:
        return [], [(p, "Docling not installed") for p in file_paths]
    converter = DocumentConverter()
    results = []
    errors = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(converter.convert, path): path for path in file_paths}
        for future in as_completed(future_to_file):
            path = future_to_file[future]
            try:
                result = future.result()
                if hasattr(result, "status") and result.status == "SUCCESS":
                    text = result.document.export_to_markdown()
                    results.append((path, text))
                else:
                    errors.append((path, getattr(result, "status", "Unknown error")))
            except Exception as e:
                errors.append((path, str(e)))
    return results, errors


def chunk_text(text, chunk_size=CHUNK_SIZE):
    # Simple chunking by character count
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

async def fetch(session, url):
    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                return await response.text()
            else:
                log_admin(f"Non-200 status for {url}: {response.status}")
    except Exception as e:
        log_admin(f"Error fetching {url}: {e}")
    return None

async def fetch_image(session, url):
    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                return await response.read()
    except Exception as e:
        log_admin(f"Error fetching image {url}: {e}")
    return None

async def process_image(session, img_url):
    img_bytes = await fetch_image(session, img_url)
    if img_bytes:
        import base64
        b64 = base64.b64encode(img_bytes).decode()
        prompt = f"Describe the following image or extract any text from it. Image (base64): {b64}"
        description = run_gemma3n(prompt)
        return description
    return None

async def scrape_page(session, url, base_url, seen_urls, depth, file_queue, log_msgs):
    if url in seen_urls or depth > MAX_DEPTH:
        return []
    seen_urls.add(url)
    await asyncio.sleep(REQUEST_DELAY)
    html = await fetch(session, url)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    texts = [t for t in soup.stripped_strings]
    page_text = "\n".join(texts)
    image_descriptions = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            img_url = urljoin(url, src)
            desc = await process_image(session, img_url)
            if desc:
                image_descriptions.append(desc)
    full_text = page_text + ("\n" + "\n".join(image_descriptions) if image_descriptions else "")
    now = datetime.utcnow().isoformat()
    chunks = chunk_text(full_text)
    embeddings = []
    metadatas = []
    for chunk in chunks:
        emb = generate_embedding(chunk)
        if emb:
            embeddings.append(emb)
            metadatas.append({
                "text": chunk,
                "url": url,
                "date": now
            })
    # Find internal links and file links
    links = set()
    for a in soup.find_all("a", href=True):
        link = urljoin(url, a["href"])
        if any(link.lower().endswith(ext) for ext in SUPPORTED_FILE_EXTS):
            file_queue.append(link)
            log_msgs.append(f"Queued file for download: {link}")
        elif link.startswith(base_url):
            links.add(link)
    return [(embeddings, metadatas, links)]

async def crawl_and_index_async(start_url, index_name=None):
    """
    Crawl the website, download and process files, extract text/images, generate embeddings, and store in Milvus.
    Logs progress and errors to search_index.log.
    Returns a summary dict for admin panel feedback.
    """
    base_url = "{}://{}".format(urlparse(start_url).scheme, urlparse(start_url).netloc)
    seen_urls = set()
    to_crawl = [(start_url, 0)]
    all_embeddings = []
    all_metadatas = []
    file_queue = []
    log_msgs = []
    file_stats = {"found": 0, "downloaded": 0, "processed": 0, "failed": 0, "skipped": 0, "errors": []}
    temp_dir = "/tmp/website_files"
    async with aiohttp.ClientSession(headers={"User-Agent": "Gemma3nRAGBot/1.0"}) as session:
        while to_crawl:
            batch = to_crawl[:MAX_CONCURRENCY]
            to_crawl = to_crawl[MAX_CONCURRENCY:]
            tasks = [scrape_page(session, url, base_url, seen_urls, depth, file_queue, log_msgs) for url, depth in batch]
            results = await asyncio.gather(*tasks)
            for (url, depth), result in zip(batch, results):
                for embeddings, metadatas, links in result:
                    all_embeddings.extend(embeddings)
                    all_metadatas.extend(metadatas)
                    for link in links:
                        if link not in seen_urls:
                            to_crawl.append((link, depth + 1))
    # Download and process files
    file_stats["found"] = len(file_queue)
    downloaded_files = []
    for file_url in file_queue:
        file_path, err = download_file(file_url, temp_dir)
        if file_path:
            downloaded_files.append(file_path)
            file_stats["downloaded"] += 1
            log_msgs.append(f"Downloaded file: {file_url} -> {file_path}")
        else:
            file_stats["failed"] += 1
            file_stats["errors"].append((file_url, err))
            log_msgs.append(f"Failed to download file: {file_url} | Error: {err}")
    # Process files with Docling
    docling_results, docling_errors = process_files_with_docling(downloaded_files, max_workers=4)
    for path, text in docling_results:
        chunks = chunk_text(text)
        now = datetime.utcnow().isoformat()
        for chunk in chunks:
            emb = generate_embedding(chunk)
            if emb:
                all_embeddings.append(emb)
                all_metadatas.append({
                    "text": chunk,
                    "url": path,
                    "date": now
                })
        file_stats["processed"] += 1
        log_msgs.append(f"Processed file: {path}")
    for path, err in docling_errors:
        file_stats["failed"] += 1
        file_stats["errors"].append((path, err))
        log_msgs.append(f"Failed to process file: {path} | Error: {err}")
    # Index all embeddings
    if all_embeddings:
        insert_embeddings(all_embeddings, all_metadatas, index_name=index_name)
        log_msgs.append(f"Indexed {len(all_embeddings)} chunks from {len(seen_urls)} pages and {file_stats['processed']} files into index '{index_name or 'rag_documents'}'.")
    else:
        log_msgs.append(f"No content indexed for index '{index_name or 'rag_documents'}'.")
    # Write log
    for msg in log_msgs:
        log_admin(msg)
    # Return summary for admin panel
    return {
        "pages_crawled": len(seen_urls),
        "files_found": file_stats["found"],
        "files_downloaded": file_stats["downloaded"],
        "files_processed": file_stats["processed"],
        "files_failed": file_stats["failed"],
        "chunks_indexed": len(all_embeddings),
        "errors": file_stats["errors"]
    }

def crawl_and_index(url, index_name=None):
    """
    Synchronous entry point for crawling and indexing a website into a specific index.
    Returns summary for admin panel feedback.
    """
    return asyncio.run(crawl_and_index_async(url, index_name=index_name))


def create_and_register_index(index_name, description, domain):
    """
    Create and register a new index (collection) for multi-index RAG.
    """
    register_index(index_name, description, domain)
    print(f"[Scraper] Registered new index '{index_name}' with domain '{domain}'.") 