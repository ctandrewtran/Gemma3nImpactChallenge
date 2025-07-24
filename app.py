import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, ctx
import time
from admin import scheduler
from rag.ollama_utils import run_gemma3n
import os
from rag.agents import rag_pipeline
from rag.agents import rag_pipeline_stream

external_scripts = [
    "https://unpkg.com/dash.nprogress@latest/dist/dash.nprogress.js"
]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], external_scripts=external_scripts)

# Simple in-memory user session (stub)
USER = {"username": "admin", "password": "password"}

# Simple in-memory config (replace with persistent storage as needed)
CONFIG = {
    "url": None,
    "chat_title": None
}

# Store last crawl/index summary for admin feedback
LAST_INDEX_SUMMARY = {"pages_crawled": 0, "files_found": 0, "files_downloaded": 0, "files_processed": 0, "files_failed": 0, "chunks_indexed": 0, "errors": []}

# Store user feedback in memory (can be extended to SQLite)
USER_FEEDBACK = {"helpful": 0, "not_helpful": 0}

def generate_friendly_title(url):
    # Use Gemma 3n via Ollama to generate a friendly, trustworthy tool name
    prompt = f"Generate a friendly, trustworthy tool name for a local government search tool for the website: {url}. The name should be short, clear, and inspire trust."
    try:
        title = run_gemma3n(prompt)
        # Clean up Gemma's response (strip quotes, whitespace, etc.)
        if title:
            title = title.strip().strip('"')
            # Basic sanity check: fallback if Gemma returns something odd
            if 3 <= len(title) <= 60:
                return title
    except Exception as e:
        print(f"[Gemma] Error generating title: {e}")
    # Fallback: extract domain and make a friendly title
    import re
    match = re.search(r"https?://([\w.-]+)", url)
    if match:
        domain = match.group(1)
        name = domain.split(".")[0].replace("-", " ").title()
        return f"{name} Deep Search Tool"
    return "Local Deep Search Tool"

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# --- First-Time Setup Wizard ---
def setup_wizard_layout(step=1, url_val=None, title_val=None):
    steps = [
        html.Li("1. Enter the website URL you want to search."),
        html.Li("2. Confirm or edit the name for your search tool."),
        html.Li("3. (Optional) Set up a schedule for automatic updates."),
        html.Li("4. Start your first search index build!"),
    ]
    return dbc.Container([
        html.H2("First-Time Setup"),
        html.Ol(steps, className="mb-4"),
        html.Div([
            html.Div([
                dbc.Label("Website URL to Scrape"),
                dbc.Input(id="setup-url", type="text", placeholder="https://example.com", value=url_val or ""),
                dbc.Button("Next", id="setup-url-next", color="primary", className="mt-2"),
            ], id="setup-step1", style={"display": "block" if step == 1 else "none"}),
            html.Div([
                dbc.Label("Name for your search tool"),
                dbc.Input(id="setup-title", type="text", value=title_val or "", style={"fontSize": "1.2em"}),
                html.Small("This is what your users will see at the top of the search page."),
                dbc.Button("Next", id="setup-title-next", color="primary", className="mt-2"),
            ], id="setup-step2", style={"display": "block" if step == 2 else "none"}),
            html.Div([
                dbc.Label("(Optional) Schedule (Cron Expression)"),
                dbc.Input(id="setup-cron", type="text", placeholder="0 2 * * *"),
                dbc.Label("Timezone"),
                dbc.Input(id="setup-tz", type="text", placeholder="America/New_York"),
                dbc.Button("Next", id="setup-sched-next", color="primary", className="mt-2"),
            ], id="setup-step3", style={"display": "block" if step == 3 else "none"}),
            html.Div([
                dbc.Button("Start First Index Build", id="setup-start-btn", color="success", className="me-2"),
                dbc.Button("Go to Admin Panel", id="setup-skip-btn", color="link"),
            ], id="setup-step4", style={"display": "block" if step == 4 else "none"}),
        ]),
        html.Div(id="setup-msg", className="mt-3 text-success"),
    ], className="mt-4")

# --- Admin Panel Layout ---
def admin_panel_layout():
    # Tabs: Main admin, Search Index Logs
    return dbc.Container([
        html.H2("Admin Panel"),
        dcc.Tabs(id="admin-tabs", value="main", children=[
            dcc.Tab(label="Main", value="main", children=[
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Website URL to Scrape"),
                        dbc.Input(id="admin-url", type="text", placeholder="https://example.com", value=CONFIG["url"] or ""),
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Schedule (Cron Expression)"),
                        dbc.Input(id="admin-cron", type="text", placeholder="0 2 * * *"),
                        html.Small("e.g., 0 2 * * * for 2am daily"),
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Timezone"),
                        dbc.Input(id="admin-tz", type="text", placeholder="America/New_York"),
                        html.Small("e.g., America/New_York, Europe/London, Asia/Kolkata"),
                    ], width=4),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Manual Refresh", id="admin-refresh-btn", color="primary", className="me-2"),
                        dbc.Button("Schedule Refresh", id="admin-sched-btn", color="secondary"),
                    ], width=8),
                ], className="mb-3"),
                html.Hr(),
                html.H5("Scraping Progress"),
                dcc.Interval(id="progress-interval", interval=2000, n_intervals=0),
                dbc.Progress(id="progress-bar", value=0, striped=True, animated=True, style={"height": "30px"}),
                html.Div(id="progress-status", className="mt-2"),
                html.Div(id="progress-last-run", className="mt-1 text-muted"),
                html.Hr(),
                html.H5("Last Indexing Summary"),
                html.Div(id="index-summary"),
                html.Hr(),
                dbc.Button("Go to Chat", id="goto-chat-btn", color="link"),
            ]),
            dcc.Tab(label="Search Index Logs", value="logs", children=[
                html.H5("Search Index Logs (last 100 lines)"),
                dbc.Button("Refresh Logs", id="refresh-logs-btn", color="secondary", className="mb-2"),
                html.Div(id="log-display", style={"maxHeight": "400px", "overflowY": "scroll", "background": "#222", "color": "#eee", "fontFamily": "monospace", "padding": "1em", "borderRadius": "5px"}),
            ]),
        ]),
    ], className="mt-4")

# --- Login Layout ---
def login_layout():
    return dbc.Container([
        html.H2("Admin Login"),
        dbc.Input(id="login-username", type="text", placeholder="Username", className="mb-2"),
        dbc.Input(id="login-password", type="password", placeholder="Password", className="mb-2"),
        dbc.Button("Login", id="login-btn", color="primary"),
        html.Div(id="login-msg", className="mt-2 text-danger"),
    ], className="mt-4")

# --- Chat Layout with Feedback ---
def chat_layout():
    primary_color = "#2a5298"
    card_style = {
        "background": "#fff",
        "borderRadius": "16px",
        "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
        "padding": "2em",
        "maxWidth": "700px",
        "margin": "2em auto"
    }
    header_style = {
        "background": primary_color,
        "color": "#fff",
        "padding": "1em",
        "borderRadius": "12px 12px 0 0",
        "fontSize": "2em",
        "fontWeight": "bold",
        "textAlign": "center"
    }
    input_style = {
        "width": "100%",
        "fontSize": "1.3em",
        "borderRadius": "8px",
        "border": f"2px solid {primary_color}",
        "padding": "0.5em"
    }
    button_style = {
        "width": "100%",
        "fontSize": "1.2em",
        "background": primary_color,
        "color": "#fff",
        "border": "none",
        "borderRadius": "8px"
    }
    return dbc.Card([
        html.Div(CONFIG["chat_title"] or "Local Information Search", style=header_style),
        html.Div([
            html.P("This tool helps you find information from your local website. No data leaves your device. Your privacy and trust are important to us."),
            html.P("Type your question or what you are looking for below. For example: 'When is the next town meeting?' or 'How do I get a building permit?'"),
            dbc.Row([
                dbc.Col([
                    dcc.Input(id="chat-query", type="text", placeholder="Type your question here...", style=input_style, aria_label="Search input"),
                ], width=8),
                dbc.Col([
                    dbc.Button("Search", id="chat-submit", color="primary", size="lg", style=button_style, n_clicks=0, **{"aria-label": "Submit search"}),
                ], width=2),
            ], className="mb-3"),
            html.Div(id="chat-response", style={"fontSize": "1.2em", "marginTop": "2em"}),
            # Feedback buttons (shown after answer)
            html.Div(id="chat-feedback-area", style={"marginTop": "1em"}),
            html.Hr(),
            dbc.Button("Go to Admin Panel", id="goto-admin-btn", color="link", **{"aria-label": "Go to admin panel"}),
        ], style={"padding": "2em", "background": "#f8f9fa", "borderRadius": "0 0 12px 12px"})
    ], style=card_style)

# --- Routing ---
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    # Show setup wizard if no URL is set
    if not CONFIG["url"]:
        return setup_wizard_layout(step=1)
    if pathname == "/chat":
        return chat_layout()
    return admin_panel_layout()

# --- Setup Wizard Callbacks ---
@app.callback(
    Output('setup-step1', 'style'),
    Output('setup-step2', 'style'),
    Output('setup-step3', 'style'),
    Output('setup-step4', 'style'),
    Output('setup-title', 'value'),
    Input('setup-url-next', 'n_clicks'),
    Input('setup-title-next', 'n_clicks'),
    Input('setup-sched-next', 'n_clicks'),
    State('setup-url', 'value'),
    State('setup-title', 'value'),
    State('setup-cron', 'value'),
    State('setup-tz', 'value'),
    prevent_initial_call=True)
def setup_wizard_steps(url_next, title_next, sched_next, url, title, cron, tz):
    # Step 1: URL entered
    if ctx.triggered_id == 'setup-url-next' and url:
        friendly_title = generate_friendly_title(url)
        CONFIG["url"] = url
        CONFIG["chat_title"] = friendly_title
        return {"display": "none"}, {"display": "block"}, {"display": "none"}, {"display": "none"}, friendly_title
    # Step 2: Title confirmed/edited
    if ctx.triggered_id == 'setup-title-next' and title:
        CONFIG["chat_title"] = title
        return {"display": "none"}, {"display": "none"}, {"display": "block"}, {"display": "none"}, title
    # Step 3: Schedule (optional)
    if ctx.triggered_id == 'setup-sched-next':
        if cron and url:
            scheduler.schedule_refresh(cron, url, timezone_str=tz)
        return {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "block"}, title
    # Default: show step 1
    return {"display": "block"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, ""

@app.callback(
    Output('setup-msg', 'children'),
    Output('url', 'pathname', allow_duplicate=True),
    Input('setup-start-btn', 'n_clicks'),
    Input('setup-skip-btn', 'n_clicks'),
    State('setup-url', 'value'),
    prevent_initial_call=True)
def setup_start_or_skip(start, skip, url):
    if ctx.triggered_id == 'setup-start-btn' and url:
        scheduler.trigger_refresh(url)
        return "Started first index build! You can monitor progress in the Admin Panel.", "/"
    if ctx.triggered_id == 'setup-skip-btn':
        return "", "/"
    return "", dash.no_update

# --- Navigation ---
@app.callback(Output('url', 'pathname', allow_duplicate=True),
              Input('goto-chat-btn', 'n_clicks'),
              Input('goto-admin-btn', 'n_clicks'),
              prevent_initial_call=True)
def nav_buttons(chat, admin):
    if ctx.triggered_id == 'goto-chat-btn':
        return "/chat"
    if ctx.triggered_id == 'goto-admin-btn':
        return "/"
    return dash.no_update

# --- Manual Refresh (update summary) ---
@app.callback(Output('admin-refresh-btn', 'disabled'),
              Input('admin-refresh-btn', 'n_clicks'),
              State('admin-url', 'value'),
              prevent_initial_call=True)
def manual_refresh(n, url):
    global LAST_INDEX_SUMMARY
    if n and url:
        from rag.scrape import crawl_and_index
        LAST_INDEX_SUMMARY = crawl_and_index(url)
        return True
    return False

# --- Schedule Refresh ---
@app.callback(Output('admin-sched-btn', 'disabled'),
              Input('admin-sched-btn', 'n_clicks'),
              State('admin-cron', 'value'),
              State('admin-url', 'value'),
              State('admin-tz', 'value'),
              prevent_initial_call=True)
def schedule_refresh(n, cron, url, tz):
    if n and cron and url:
        ok = scheduler.schedule_refresh(cron, url, timezone_str=tz)
        return ok
    return False

# --- Progress Polling ---
@app.callback(
    Output('progress-bar', 'value'),
    Output('progress-bar', 'label'),
    Output('progress-status', 'children'),
    Output('progress-last-run', 'children'),
    Input('progress-interval', 'n_intervals'))
def update_progress(n):
    prog = scheduler.get_progress()
    percent = int(prog['progress'] * 100)
    label = f"{percent}%" if prog['status'] != 'idle' else ""
    status = f"Status: {prog['status'].capitalize()} - {prog['message']}"
    last = f"Last run: {prog['last_run']}" if prog['last_run'] else ""
    return percent, label, status, last

# --- Login (stub, not secure) ---
@app.callback(Output('login-msg', 'children'),
              Input('login-btn', 'n_clicks'),
              State('login-username', 'value'),
              State('login-password', 'value'),
              prevent_initial_call=True)
def login(n, username, password):
    if n and username and password:
        if username == USER['username'] and password == USER['password']:
            return "Login successful! (stub, not secure)"
        else:
            return "Invalid credentials."
    return ""

# --- Chat Search Callback (wired to section-aware RAG pipeline) ---
@app.callback(
    Output('chat-response', 'children'),
    Output('chat-feedback-area', 'children'),
    Input('chat-submit', 'n_clicks'),
    State('chat-query', 'value'),
    prevent_initial_call=True)
def chat_search(n, query):
    if n and query:
        from dash import no_update
        node_status = {
            'translation': 'Translating (if needed)...',
            'index_selection': 'Selecting best index...',
            'section_prediction': 'Predicting relevant section...',
            'query': 'Extracting info...',
            'evaluation': 'Reviewing answer...',
            'contacts': 'Loading contact info...',
            'response': 'Composing response...',
            'translation_back': 'Translating answer back to your language...'
        }
        answer = None
        citations = None
        for update in rag_pipeline_stream(query):
            node = list(update.keys())[0]
            state = update[node]
            # Show progress message for this node
            if node != 'translation_back':
                yield html.Div([
                    html.P(node_status.get(node, f"Running {node}...")),
                    dcc.Loading(type="circle")
                ]), ""
            # If this is the response node, show the answer preview
            if node == 'response' and 'answer' in state:
                answer = state['answer']
                citations = state.get('citations', [])
        # Final answer
        if answer is not None:
            feedback_buttons = html.Div([
                html.Span("Was this helpful? ", style={"marginRight": "1em"}),
                dbc.Button("Yes", id="feedback-yes", color="success", n_clicks=0, style={"marginRight": "0.5em"}, **{"aria-label": "Mark answer as helpful"}),
                dbc.Button("No", id="feedback-no", color="danger", n_clicks=0, **{"aria-label": "Mark answer as not helpful"})
            ], role="group", aria_label="Feedback buttons")
            yield (
                html.Div([
                    html.P("Here's what I found for your question:"),
                    html.Div(answer, style={"marginBottom": "1em"}),
                    html.Hr(),
                    html.P("Sources consulted:"),
                    html.Ul([html.Li(html.A(c, href=c, target="_blank")) for c in citations]) if citations else html.P("No sources found."),
                    html.P("If you need more help, please contact your local office.", style={"marginTop": "1em", "fontStyle": "italic"})
                ]),
                feedback_buttons
            )
        else:
            yield html.Div([html.P("Sorry, something went wrong. Please try again or contact your local office.")]), ""
    yield "", ""

# --- Feedback Button Callbacks ---
@app.callback(
    Output('chat-feedback-area', 'children', allow_duplicate=True),
    Input('feedback-yes', 'n_clicks'),
    Input('feedback-no', 'n_clicks'),
    prevent_initial_call=True)
def handle_feedback(yes, no):
    # Only increment if button was clicked
    changed = ctx.triggered_id
    if changed == 'feedback-yes':
        USER_FEEDBACK["helpful"] += 1
        msg = html.Span("Thank you for your feedback!", style={"color": "#2a5298", "fontWeight": "bold"})
    elif changed == 'feedback-no':
        USER_FEEDBACK["not_helpful"] += 1
        msg = html.Span("Thank you for your feedback! We'll use this to improve.", style={"color": "#a00", "fontWeight": "bold"})
    else:
        msg = ""
    return msg

# --- Show last index summary ---
@app.callback(
    Output('index-summary', 'children', allow_duplicate=True),
    Input('progress-interval', 'n_intervals'))
def show_index_summary(n):
    s = LAST_INDEX_SUMMARY
    errors = s.get("errors", [])
    total = USER_FEEDBACK["helpful"] + USER_FEEDBACK["not_helpful"]
    percent = (USER_FEEDBACK["helpful"] / total * 100) if total else 0
    feedback_metrics = html.Div([
        html.H6("User Feedback Metrics", style={"marginTop": "1em"}),
        html.P(f"Helpful: {USER_FEEDBACK['helpful']} | Not Helpful: {USER_FEEDBACK['not_helpful']} | % Helpful: {percent:.1f}%")
    ])
    return html.Div([
        html.P(f"Pages crawled: {s.get('pages_crawled', 0)} | Files found: {s.get('files_found', 0)} | Downloaded: {s.get('files_downloaded', 0)} | Processed: {s.get('files_processed', 0)} | Failed: {s.get('files_failed', 0)} | Chunks indexed: {s.get('chunks_indexed', 0)}"),
        html.Ul([html.Li(f"{e[0]}: {e[1]}") for e in errors]) if errors else html.P("No errors."),
        feedback_metrics
    ])

@app.callback(
    Output('log-display', 'children'),
    Input('refresh-logs-btn', 'n_clicks'),
    prevent_initial_call=True)
def refresh_logs(n):
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-100:]
        return html.Pre("".join(lines))
    return html.Pre("No logs found.")

if __name__ == '__main__':
    app.run_server(debug=True) 