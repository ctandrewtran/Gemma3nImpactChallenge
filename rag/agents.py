from rag.ollama_utils import run_gemma3n, generate_embedding
from rag.milvus_utils import list_indexes, search_embeddings, connect_milvus
from langdetect import detect

# --- Translation Agent ---
def translation_agent(query):
    """
    Detect language and translate to English if needed using Gemma 3n.
    """
    try:
        lang = detect(query)
    except Exception:
        lang = 'en'
    if lang != 'en':
        prompt = f"Translate the following to English for a government search tool: {query}"
        return run_gemma3n(prompt)
    return query

# --- Section Prediction Agent ---
def section_prediction_agent(query, index_name):
    """
    Use Gemma 3n to predict the best section/path for the query from available sections in the index.
    """
    # Get all unique sections from the index (Milvus)
    col = connect_milvus(index_name)
    # Query all unique section values (may need to scan all entities)
    try:
        # This is a simple way; for large collections, optimize with a separate section registry
        all_sections = set()
        for entities in col.query(expr=None, output_fields=["section"]):
            section = entities.get("section")
            if section:
                all_sections.add(section)
        sections = list(sorted(all_sections))
    except Exception:
        sections = []
    if not sections:
        return None
    # Use LLM to pick the best section
    prompt = (
        f"User query: '{query}'\n"
        f"Available website sections: {', '.join(sections)}\n"
        "Which section is most relevant? Respond with the section path only."
    )
    response = run_gemma3n(prompt)
    for s in sections:
        if s.lower() in response.lower():
            return s
    return sections[0]  # fallback

# --- Index Selection Agent ---
def index_selection_agent(query):
    """
    Use Gemma 3n to select the best index for the query from available indexes.
    """
    indexes = list_indexes()
    if not indexes:
        return None
    index_names = list(indexes.keys())
    index_descs = [f"{name}: {meta['description']}" for name, meta in indexes.items()]
    prompt = (
        f"User query: '{query}'\n"
        f"Available indexes:\n" + "\n".join(index_descs) +
        "\nWhich index should be searched? Respond with the index name only."
    )
    response = run_gemma3n(prompt)
    for name in index_names:
        if name.lower() in response.lower():
            return name
    return index_names[0]

# --- Query Agent (Section-Aware) ---
def query_agent(query, index_name, section=None, top_k=5):
    """
    Rewrite query for search, generate embedding, search selected index, retrieve top chunks.
    If section is provided, filter search to that section.
    """
    prompt = f"Rewrite the following user question to be as concise and search-friendly as possible for a government document search: {query}"
    search_query = run_gemma3n(prompt)
    embedding = generate_embedding(search_query)
    expr = None
    if section:
        # Milvus expr for section filtering (exact match)
        expr = f'section == "{section}"'
    results = search_embeddings(embedding, top_k=top_k, index_name=index_name, expr=expr)
    return search_query, results

# --- Evaluation Agent ---
def evaluator_agent(query, context_chunks):
    """
    Use Gemma 3n to check if the retrieved context is sufficient. If not, suggest fallback or clarification.
    """
    context_text = "\n".join([c['text'] for c in context_chunks])
    prompt = (
        f"User question: {query}\n"
        f"Retrieved context: {context_text}\n"
        "Does the context fully answer the question? Respond 'yes' or 'no' and explain briefly."
    )
    response = run_gemma3n(prompt)
    return response

# --- Response Agent ---
def response_agent(query, context_chunks, evaluation, section=None):
    """
    Generate a final answer with citations/links, trust-building language, and next steps.
    """
    context_text = "\n".join([c['text'] for c in context_chunks])
    citations = [f"Source: {c['url']} (Indexed: {c['date']})" for c in context_chunks]
    section_info = f"Section searched: {section}\n" if section else ""
    prompt = (
        f"User question: {query}\n"
        f"Relevant information: {context_text}\n"
        f"Citations: {'; '.join(citations)}\n"
        f"Evaluation: {evaluation}\n"
        f"{section_info}"
        "Write a clear, trustworthy answer for a user. You are acting on behalf of local government, keep your tone professional and informative. Include citations/links, next steps, and who to contact if more help is needed."
    )
    return run_gemma3n(prompt)

# --- .gov URL Enforcement ---
def is_gov_url(url):
    """
    Enforce that only .gov URLs are accepted for indexing.
    """
    return url.lower().endswith('.gov') or '.gov/' in url.lower()

# --- Main RAG Pipeline (Section-Aware) ---
def rag_pipeline(user_query):
    """
    Full agentic RAG pipeline: translation, index selection, section prediction, query, evaluation, response.
    Returns the final answer and citations.
    """
    # 1. Translate if needed
    translated_query = translation_agent(user_query)
    # 2. Select index
    index_name = index_selection_agent(translated_query)
    if not index_name:
        return "No search indexes available.", []
    # 3. Predict section
    section = section_prediction_agent(translated_query, index_name)
    # 4. Query (section-aware)
    search_query, context_chunks = query_agent(translated_query, index_name, section=section)
    # 5. Evaluate (use search_query)
    evaluation = evaluator_agent(search_query, context_chunks)
    # 6. Respond (use search_query)
    answer = response_agent(search_query, context_chunks, evaluation, section=section)
    # 7. Collect citations
    citations = [c['url'] for c in context_chunks]
    return answer, citations

# NOTE: During indexing, ensure 'section' (URL path) is stored in metadata for each chunk. 