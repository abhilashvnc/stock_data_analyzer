import yfinance as yf
import streamlit as st
import google.generativeai as genai
from groq import Groq
from ollama import Client
import streamlit.components.v1 as components
import json

# ==============================
# PROVIDER AUTH CONFIG
# ==============================
# Describes what each provider needs for auth
PROVIDER_AUTH = {
    "Ollama": {
        "type": "userpass",
        "fields": {"username": "Username", "password": "Password"},
        "host_field": True,
        "default_host": "http://ollama-api.lxa.com",
    },
    "Gemini": {
        "type": "apikey",
        "fields": {"api_key": "API Key"},
        "host_field": False,
    },
    "Groq": {
        "type": "apikey",
        "fields": {"api_key": "API Key"},
        "host_field": False,
    },
}

PROVIDERS = list(PROVIDER_AUTH.keys())


# ==============================
# SESSION STATE BOOTSTRAP
# ==============================
def init_session():
    if "provider_sessions" not in st.session_state:
        # Each provider gets its own auth + client state
        st.session_state.provider_sessions = {
            p: {
                "authenticated": False,
                "client": None,
                "credentials": {},       # stored creds for this provider
                "model_list": [],
                "show_auth": True,       # whether auth form is visible
            }
            for p in PROVIDERS
        }
    if "active_provider" not in st.session_state:
        st.session_state.active_provider = PROVIDERS[0]
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_key" not in st.session_state:
        st.session_state.chat_key = ""
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = {}
    # Flag set by localStorage restore
    if "ls_loaded" not in st.session_state:
        st.session_state.ls_loaded = False


# ==============================
# LOCALSTORAGE BRIDGE
# Persists credentials across page refreshes.
# We write a JSON blob to localStorage and read it back on load.
# Only non-secret keys like host are stored in plain text;
# passwords/api keys are stored as-is since this is local to the user's browser.
# ==============================
LS_KEY = "stock_analyst_sessions"

def localstorage_save(provider_sessions):
    """Save credentials (not clients) to localStorage."""
    saveable = {}
    for p, s in provider_sessions.items():
        if s["authenticated"]:
            saveable[p] = {
                "credentials": s["credentials"],
                "authenticated": True,
            }
    payload = json.dumps(saveable).replace("`", "\\`")
    components.html(f"""
        <script>
            localStorage.setItem('{LS_KEY}', `{payload}`);
        </script>
    """, height=0)


def localstorage_load_component():
    """
    Inject JS that reads localStorage and posts back to Streamlit
    via query params. We use a hidden form submit trick.
    Only runs once per session (ls_loaded guard).
    """
    if st.session_state.ls_loaded:
        return

    components.html(f"""
        <script>
            const data = localStorage.getItem('{LS_KEY}');
            if (data) {{
                const encoded = encodeURIComponent(data);
                // Pass via URL fragment — Streamlit reads st.query_params
                const url = new URL(window.parent.location.href);
                url.searchParams.set('_ls_creds', encoded);
                window.parent.history.replaceState({{}}, '', url.toString());
                window.parent.location.reload();
            }}
        </script>
    """, height=0)


def restore_from_query_params():
    """
    If query params contain _ls_creds, restore sessions from them,
    then silently re-authenticate each provider.
    """
    if st.session_state.ls_loaded:
        return

    raw = st.query_params.get("_ls_creds", None)
    if not raw:
        st.session_state.ls_loaded = True
        return

    try:
        saved = json.loads(raw)
        for p, data in saved.items():
            if p in st.session_state.provider_sessions and data.get("authenticated"):
                creds = data["credentials"]
                client, error = build_client(p, creds)
                if client:
                    sess = st.session_state.provider_sessions[p]
                    sess["authenticated"] = True
                    sess["client"] = client
                    sess["credentials"] = creds
                    sess["show_auth"] = False
                    sess["model_list"] = fetch_models(p, client)
    except Exception:
        pass

    # Clean the URL
    st.query_params.clear()
    st.session_state.ls_loaded = True


# ==============================
# BUILD CLIENT
# ==============================
def build_client(provider, creds):
    """
    Attempt to build and validate a client for the given provider.
    Returns (client, None) on success, (None, error_string) on failure.
    """
    try:
        if provider == "Ollama":
            host     = creds.get("host", "http://localhost:11434")
            username = creds.get("username", "")
            password = creds.get("password", "")
            auth     = (username, password) if username else None
            client   = Client(host=host, auth=auth)
            client.list()   # validation call
            return client, None

        elif provider == "Gemini":
            api_key = creds.get("api_key", "")
            genai.configure(api_key=api_key)
            list(genai.list_models())   # validation call
            return "gemini_configured", None  # genai is global, no client object

        elif provider == "Groq":
            api_key = creds.get("api_key", "")
            client  = Groq(api_key=api_key)
            client.models.list()    # validation call
            return client, None

    except Exception as e:
        return None, str(e)


# ==============================
# FETCH MODELS
# ==============================
def fetch_models(provider, client):
    try:
        if provider == "Ollama":
            result = client.list()
            return [m.model for m in result.models]

        elif provider == "Gemini":
            models = genai.list_models()
            return [
                m.name.replace("models/", "")
                for m in models
                if "generateContent" in m.supported_generation_methods
            ]

        elif provider == "Groq":
            result = client.models.list()
            return sorted([m.id for m in result.data])

    except Exception as e:
        st.sidebar.error(f"Model fetch failed: {e}")
        return []


# ==============================
# AI RESPONSE
# ==============================
def get_ai_response(provider, client, model, messages):
    if provider == "Ollama":
        response = client.chat(model=model, messages=messages)
        return response["message"]["content"]

    elif provider == "Gemini":
        gemini_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=messages[0]["content"]
        )
        history = []
        for m in messages[1:-1]:
            history.append({
                "role": "user" if m["role"] == "user" else "model",
                "parts": [m["content"]]
            })
        chat = gemini_model.start_chat(history=history)
        return chat.send_message(messages[-1]["content"]).text

    elif provider == "Groq":
        response = client.chat.completions.create(
            model=model, messages=messages
        )
        return response.choices[0].message.content


# ==============================
# AUTH FORM (sidebar)
# ==============================
def render_auth_form(provider):
    sess   = st.session_state.provider_sessions[provider]
    config = PROVIDER_AUTH[provider]
    creds  = sess["credentials"].copy()

    with st.sidebar.form(key=f"auth_form_{provider}"):
        st.markdown(f"**Connect to {provider}**")

        if config.get("host_field"):
            creds["host"] = st.text_input(
                "Host URL",
                value=creds.get("host", config.get("default_host", "")),
            )

        if config["type"] == "userpass":
            creds["username"] = st.text_input(
                "Username", value=creds.get("username", "")
            )
            creds["password"] = st.text_input(
                "Password", value=creds.get("password", ""), type="password"
            )
        elif config["type"] == "apikey":
            creds["api_key"] = st.text_input(
                "API Key", value=creds.get("api_key", ""), type="password"
            )

        connect_clicked = st.form_submit_button("🔌 Connect", use_container_width=True)

    if connect_clicked:
        with st.spinner(f"Connecting to {provider}..."):
            new_client, error = build_client(provider, creds)

        if error:
            st.sidebar.error(f"❌ {error}")
        else:
            # Only now replace old credentials and client
            sess["client"]        = new_client
            sess["credentials"]   = creds
            sess["authenticated"] = True
            sess["show_auth"]     = False
            sess["model_list"]    = fetch_models(provider, new_client)
            localstorage_save(st.session_state.provider_sessions)
            st.rerun()


# ==============================
# MODEL SECTION (sidebar)
# ==============================
def render_model_section(provider):
    sess = st.session_state.provider_sessions[provider]

    # Small "change credentials" link
    col1, col2 = st.sidebar.columns([3, 1])
    col1.success(f"✅ Connected")
    if col2.button("🔑", help="Change credentials", key=f"show_auth_{provider}"):
        sess["show_auth"] = True
        st.rerun()

    # Logout
    if st.sidebar.button("🚪 Logout", key=f"logout_{provider}", use_container_width=True):
        sess["authenticated"] = False
        sess["client"]        = None
        sess["credentials"]   = {}
        sess["model_list"]    = []
        sess["show_auth"]     = True
        localstorage_save(st.session_state.provider_sessions)
        st.rerun()

    # Model dropdown + refresh side by side
    model_list = sess.get("model_list", [])

    col_m, col_r = st.sidebar.columns([4, 1])
    with col_m:
        if model_list:
            previous = st.session_state.selected_model.get(provider)
            default_idx = model_list.index(previous) if previous in model_list else 0
            chosen = st.selectbox(
                "Model", model_list,
                index=default_idx,
                key=f"model_select_{provider}"
            )
            st.session_state.selected_model[provider] = chosen
        else:
            st.warning("No models found.")
            st.session_state.selected_model[provider] = None

    with col_r:
        st.markdown("<br>", unsafe_allow_html=True)   # vertical align
        if st.button("🔄", help="Refresh model list", key=f"refresh_{provider}"):
            sess["model_list"] = fetch_models(provider, sess["client"])
            st.rerun()


# ==============================
# STOCK DATA + CONTEXT
# ==============================
@st.cache_data(ttl=300)
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info  = stock.info

    def safe(fn):
        try: return fn()
        except: return "N/A"

    rec_summary = safe(lambda: stock.recommendations.tail(5).to_string())
    news_text   = safe(lambda: "\n".join(
        f"- {n['content']['title']}" for n in (stock.news or [])[:5]
    ))
    fin_text    = safe(lambda: stock.financials.iloc[:, :2].to_string())
    cf_text     = safe(lambda: stock.cashflow.iloc[:, :2].to_string())
    bs_text     = safe(lambda: stock.balance_sheet.iloc[:, :2].to_string())

    return info, rec_summary, news_text, fin_text, cf_text, bs_text


def build_context(info, rec_summary, news_text, fin_text, cf_text, bs_text):
    def g(k): return info.get(k) or "N/A"
    return f"""
You are a professional stock analyst specializing in Indian equities.
Answer ONLY based on the data provided. If something is missing, say so clearly.

===== COMPANY OVERVIEW =====
Name: {g('longName')} | Sector: {g('sector')} | Industry: {g('industry')}
Exchange: {g('exchange')} | Currency: {g('currency')}

===== PRICE & MARKET =====
Price: {g('currentPrice')} | 52W High: {g('fiftyTwoWeekHigh')} | 52W Low: {g('fiftyTwoWeekLow')}
Market Cap: {g('marketCap')} | Enterprise Value: {g('enterpriseValue')} | Beta: {g('beta')}

===== VALUATION =====
Trailing PE: {g('trailingPE')} | Forward PE: {g('forwardPE')} | PEG: {g('pegRatio')}
P/B: {g('priceToBook')} | P/S: {g('priceToSalesTrailing12Months')}

===== PROFITABILITY =====
Profit Margin: {g('profitMargins')} | Op Margin: {g('operatingMargins')}
ROE: {g('returnOnEquity')} | ROA: {g('returnOnAssets')}
EBITDA: {g('ebitda')} | FCF: {g('freeCashflow')}

===== GROWTH =====
Revenue Growth: {g('revenueGrowth')} | Earnings Growth: {g('earningsGrowth')}
Revenue TTM: {g('totalRevenue')}

===== FINANCIAL HEALTH =====
D/E: {g('debtToEquity')} | Current Ratio: {g('currentRatio')} | Quick Ratio: {g('quickRatio')}
Cash: {g('totalCash')} | Debt: {g('totalDebt')}

===== DIVIDENDS =====
Yield: {g('dividendYield')} | Rate: {g('dividendRate')} | Payout: {g('payoutRatio')}

===== ANALYST OPINION =====
Recommendation: {g('recommendationKey')} | Target Mean: {g('targetMeanPrice')}
Target High: {g('targetHighPrice')} | Target Low: {g('targetLowPrice')}
Analysts: {g('numberOfAnalystOpinions')}

Recent Recommendations:
{rec_summary}

===== RECENT NEWS =====
{news_text}

===== INCOME STATEMENT =====
{fin_text}

===== CASH FLOW =====
{cf_text}

===== BALANCE SHEET =====
{bs_text}

===== BUSINESS SUMMARY =====
{g('longBusinessSummary')}
"""


# ==============================
# MAIN APP
# ==============================
st.set_page_config(page_title="AI Stock Analyst", page_icon="📈")
init_session()
restore_from_query_params()         # restore creds from localStorage on fresh load

# Only inject localStorage reader if not yet loaded
if not st.session_state.ls_loaded:
    localstorage_load_component()
    st.stop()                        # wait for reload with query params

st.title("📈 AI Stock Analyst")

# ---- SIDEBAR ----
with st.sidebar:
    st.header("🤖 Model Settings")

    provider = st.selectbox("Provider", PROVIDERS, key="provider_select")
    st.session_state.active_provider = provider

    sess = st.session_state.provider_sessions[provider]

    if not sess["authenticated"] or sess["show_auth"]:
        render_auth_form(provider)
    else:
        render_model_section(provider)

# ---- MAIN AREA ----
active   = st.session_state.active_provider
sess     = st.session_state.provider_sessions[active]
model    = st.session_state.selected_model.get(active)

if not sess["authenticated"]:
    st.info("👈 Connect to a provider in the sidebar to get started.")
    st.stop()

ticker_input = st.text_input("Enter Stock Ticker (e.g. RELIANCE, TCS, INFY)")

if ticker_input and model:
    ticker = ticker_input.upper().strip()
    if not ticker.endswith(".NS"):
        ticker += ".NS"

    with st.spinner("Fetching stock data..."):
        info, rec_summary, news_text, fin_text, cf_text, bs_text = get_stock_data(ticker)

    if not info or len(info.keys()) <= 1:
        st.error("❌ Invalid ticker or no data found.")
        st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("Price",    f"₹{info.get('currentPrice', 'N/A')}")
    col2.metric("52W High", f"₹{info.get('fiftyTwoWeekHigh', 'N/A')}")
    col3.metric("52W Low",  f"₹{info.get('fiftyTwoWeekLow', 'N/A')}")
    st.success(f"**{info.get('longName')}** | {info.get('sector')}")

    context  = build_context(info, rec_summary, news_text, fin_text, cf_text, bs_text)
    chat_key = f"{ticker}_{active}_{model}"

    if st.session_state.chat_key != chat_key:
        st.session_state.messages  = [{"role": "system", "content": context}]
        st.session_state.chat_key  = chat_key

    for msg in st.session_state.messages[1:]:
        st.chat_message(msg["role"]).write(msg["content"])

    user_input = st.chat_input("Ask about financials, valuation, risks, growth...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        with st.spinner(f"{active} / {model}..."):
            try:
                ai_reply = get_ai_response(
                    active, sess["client"], model, st.session_state.messages
                )
            except Exception as e:
                ai_reply = f"⚠️ {active} error: {e}"

        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        st.chat_message("assistant").write(ai_reply)

elif ticker_input and not model:
    st.warning("⚠️ No model selected. Refresh the model list in the sidebar.")