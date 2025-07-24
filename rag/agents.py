from rag.ollama_utils import run_gemma3n, generate_embedding
from rag.milvus_utils import list_indexes, search_embeddings, connect_milvus
from langdetect import detect
from langgraph.graph import StateGraph, END
import os

# --- State Definition ---
# The state is a dictionary with keys:
# 'user_query', 'source_lang', 'translated_query', 'index_name', 'section', 'search_query', 'context_chunks', 'evaluation', 'answer', 'citations'

def translation_node(state):
    user_query = state['user_query']
    try:
        source_lang = detect(user_query)
    except Exception:
        source_lang = 'en'
    if source_lang != 'en':
        prompt = f"Translate the following to English for a government search tool: {user_query}"
        translated_query = run_gemma3n(prompt)
    else:
        translated_query = user_query
    state['source_lang'] = source_lang
    state['translated_query'] = translated_query
    return state

def index_selection_node(state):
    query = state['translated_query']
    indexes = list_indexes()
    if not indexes:
        state['index_name'] = None
        return state
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
            state['index_name'] = name
            return state
    state['index_name'] = index_names[0]
    return state

def section_prediction_node(state):
    query = state['translated_query']
    index_name = state['index_name']
    if not index_name:
        state['section'] = None
        return state
    col = connect_milvus(index_name)
    try:
        all_sections = set()
        for entities in col.query(expr=None, output_fields=["section"]):
            section = entities.get("section")
            if section:
                all_sections.add(section)
        sections = list(sorted(all_sections))
    except Exception:
        sections = []
    if not sections:
        state['section'] = None
        return state
    prompt = (
        f"User query: '{query}'\n"
        f"Available website sections: {', '.join(sections)}\n"
        "Which section is most relevant? Respond with the section path only."
    )
    response = run_gemma3n(prompt)
    for s in sections:
        if s.lower() in response.lower():
            state['section'] = s
            return state
    state['section'] = sections[0]
    return state

def query_node(state):
    query = state['translated_query']
    index_name = state['index_name']
    section = state['section']
    prompt = f"Rewrite the following user question to be as concise and search-friendly as possible for a government document search: {query}"
    search_query = run_gemma3n(prompt)
    embedding = generate_embedding(search_query)
    expr = None
    if section:
        expr = f'section == "{section}"'
    results = search_embeddings(embedding, top_k=5, index_name=index_name, expr=expr)
    state['search_query'] = search_query
    state['context_chunks'] = results
    return state

def evaluation_node(state):
    query = state['search_query']
    context_chunks = state['context_chunks']
    context_text = "\n".join([c['text'] for c in context_chunks])
    prompt = (
        f"User question: {query}\n"
        f"Retrieved context: {context_text}\n"
        "Does the context fully answer the question? Respond 'yes' or 'no' and explain briefly."
    )
    response = run_gemma3n(prompt)
    state['evaluation'] = response
    return state

CONTACTS_FILE = "contacts.txt"

def load_contacts():
    contacts = []
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    contacts.append(line)
    return contacts

def contacts_node(state):
    # Load contacts and add to state
    state['contacts'] = load_contacts()
    return state

def response_node(state):
    query = state['search_query']
    context_chunks = state['context_chunks']
    evaluation = state['evaluation']
    section = state['section']
    contacts = state.get('contacts', [])
    context_text = "\n".join([c['text'] for c in context_chunks])
    citations = [f"Source: {c['url']} (Indexed: {c['date']})" for c in context_chunks]
    section_info = f"Section searched: {section}\n" if section else ""
    # Provide contacts as a resource, not as part of the answer unless needed
    contacts_instruction = (f"\nIf you determine the user needs to contact someone, you may use the following contact info: {', '.join(contacts)}" if contacts else "")
    prompt = (
        f"User question: {query}\n"
        f"Relevant information: {context_text}\n"
        f"Citations: {'; '.join(citations)}\n"
        f"Evaluation: {evaluation}\n"
        f"{section_info}"
        f"{contacts_instruction}"
        "You are a local government assistant for a rural community. When answering, always quote directly from the provided information using quotation marks whenever possible. For each fact or statement, include a citation to the source document (URL and date). If you cannot find an answer in the provided context, say so and suggest contacting the local office. Use clear, trustworthy, and professional language. Include next steps and who to contact if more help is needed."
    )
    max_retries = 2
    for _ in range(max_retries):
        try:
            response = run_gemma3n(prompt)
            if response and response.strip() and not response.startswith("[Error"):
                state['answer'] = response
                break
        except Exception:
            continue
    else:
        state['answer'] = ("Sorry, I was unable to generate an answer at this time. "
                          "Please try again or contact your local IT administrator.")
    state['citations'] = [c['url'] for c in context_chunks]
    return state

def translation_back_node(state):
    source_lang = state.get('source_lang', 'en')
    answer = state.get('answer', '')
    if source_lang != 'en' and answer:
        prompt = f"Translate the following answer back to {source_lang} for a government search tool user: {answer}"
        answer = run_gemma3n(prompt)
        state['answer'] = answer
    return state

# --- LangGraph Workflow ---
def rag_pipeline(user_query):
    # Initial state
    state = {
        'user_query': user_query,
        'source_lang': None,
        'translated_query': None,
        'index_name': None,
        'section': None,
        'search_query': None,
        'context_chunks': None,
        'evaluation': None,
        'answer': None,
        'citations': None,
        'contacts': None,
    }
    # Build the graph
    graph = StateGraph()
    graph.add_node('translation', translation_node)
    graph.add_node('index_selection', index_selection_node)
    graph.add_node('section_prediction', section_prediction_node)
    graph.add_node('query', query_node)
    graph.add_node('evaluation', evaluation_node)
    graph.add_node('contacts', contacts_node)
    graph.add_node('response', response_node)
    graph.add_node('translation_back', translation_back_node)
    # Edges
    graph.add_edge('translation', 'index_selection')
    graph.add_edge('index_selection', 'section_prediction')
    graph.add_edge('section_prediction', 'query')
    graph.add_edge('query', 'evaluation')
    graph.add_edge('evaluation', 'contacts')
    graph.add_edge('contacts', 'response')
    graph.add_edge('response', 'translation_back')
    graph.add_edge('translation_back', END)
    # Run the workflow
    result = graph.run(state)
    return result['answer'], result['citations'] 