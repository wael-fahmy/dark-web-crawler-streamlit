
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from cryptography.fernet import Fernet
import nltk
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib
# --- Init ---
# nltk data already downloaded in Docker image
#nltk.download('punkt', force=True)
#nltk.download('stopwords', force=True)

if 'df' not in st.session_state:
    st.session_state.df = None
if 'encrypted_file' not in st.session_state:
    st.session_state.encrypted_file = None

# --- Config ---
DB_FILE = 'ioc_results.db'
CSV_FILE = 'ioc_results.csv'
FERNET_FILE = 'ioc_results.csv.fernet'
FERNET_KEY_FILE = 'fernet.key'
PROXIES = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}

st.set_page_config(page_title="Dark Web Crawler", layout="wide")
st.title("🕵️ Passive Dark Web Crawler GUI")
st.markdown("Crawl .onion sites passively over Tor, extract CTI keywords, visualize results, and export data.")
# --- Auth Config ---
ADMIN_HASH_SHA256 = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"  # hash of "admin123"
SESSION_TIMEOUT = 600  # 10 minutes in seconds
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'login_time' not in st.session_state:
    st.session_state.login_time = None
# Check if session expired
if st.session_state.authenticated:
    current_time = time.time()
    if st.session_state.login_time and (current_time - st.session_state.login_time > SESSION_TIMEOUT):
        st.session_state.authenticated = False
        st.session_state.login_time = None
        st.warning("🔒 Session expired. Please log in again.")
        st.rerun()
        
with st.sidebar.expander("🔐 Admin Login"):
    if not st.session_state.authenticated:
        password_input = st.text_input("Enter admin password", type="password", key="password_input")
        if st.button("Login"):
            hashed_input = hashlib.sha256(password_input.encode()).hexdigest()
            if hashed_input == ADMIN_HASH_SHA256:
                st.session_state.authenticated = True
                st.session_state.login_time = time.time()
                st.success("✅ Logged in as Admin")
                st.rerun()
            else:
                st.error("❌ Incorrect password")
    else:
        st.markdown("**✅ Logged in as Admin**")
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.login_time = None
            st.rerun()
# --- Sidebar ---
st.sidebar.header("Crawler Settings")
def sanitize_onion_url(url):
    url = url.strip()
    if url.startswith("https://"):
        url = "http://" + url[len("https://"):]
    if not url.startswith("http://"):
        url = "http://" + url
    if url.endswith("/"):
        url = url[:-1]
    return url
onion_sites_input = st.sidebar.text_area(
    "Enter .onion sites (one per line):",
    "http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion\n"
    "http://facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion"
    
)
onion_sites = [s.strip() for s in onion_sites_input.splitlines() if s.strip()]
onion_sites = [sanitize_onion_url(u) for u in onion_sites if ".onion" in u]
keywords_input = st.sidebar.text_input(
    "Enter keywords (comma-separated):",
    "ai,new,protection,email,page,ad,forgot,phone,peace,password,credential,exploit,leak,malware,ransomware,botnet,privacy,tor,safe,search,anonymous,security,cybercrime,cybersecurity,phishing,scam,bitcoin,darkweb,darknet,cyberattack,cyberthreats,cybersecurityawareness,cyberintelligence,cyberespionage,cyberwarfare,cyberdefense,cybercrimeinvestigation,cybercrimeprevention,cybercrimesolutions,cybercrimeanalysis,cybercrimereporting"
)
KEYWORDS = [kw.strip().lower() for kw in keywords_input.split(",") if kw.strip()]

start_crawl = st.sidebar.button("🚀 Start Crawling")

# --- Result Rendering ---
def render_results(df, encrypted_file):
    st.subheader("🔍 Extracted IOCs")
    st.dataframe(df)

    st.subheader("📊 Keyword Frequency")
    keyword_counts = df['keyword'].value_counts()
    st.bar_chart(keyword_counts)

    st.subheader("☁️ Word Cloud")
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(keyword_counts.to_dict())
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

    st.subheader("🧠 NLP Token Analysis")
    text_blob = ' '.join(df['context'].dropna().astype(str))
    tokens = word_tokenize(text_blob.lower())
    filtered = [t for t in tokens if t.isalnum() and t not in stopwords.words('english')]
    top_tokens = Counter(filtered).most_common(20)
    st.table(pd.DataFrame(top_tokens, columns=["Token", "Count"]))

    if encrypted_file and os.path.exists(encrypted_file):
        with open(encrypted_file, 'rb') as f:
            st.download_button("🔐 Download Encrypted CSV (.fernet)", f, file_name="ioc_results.csv.fernet", key="fernet_download")

    if st.session_state.authenticated:
        with open(CSV_FILE, 'rb') as f:
            st.download_button("⬇️ Download CSV (Admin Only)", f, file_name="ioc_results.csv", key="csv_download")

        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'rb') as f:
                st.download_button("💾 Download SQLite DB", f, file_name="ioc_results.db", key="db_download")

        if os.path.exists(FERNET_KEY_FILE):
            with open(FERNET_KEY_FILE, 'rb') as f:
                st.download_button("🔑 Download Fernet Key", f, file_name="fernet.key", key="key_download")



# --- Crawler Logic ---
if start_crawl:
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS iocs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            keyword TEXT,
            context TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    st.info("Starting crawl...")
    progress = st.progress(0)
    log_area = st.empty()

  # Use retry-enabled session
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=3, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))

    for i, url in enumerate(onion_sites):
        try:
            log_area.write(f"Crawling: {url}")
            response = session.get(url, proxies=PROXIES, timeout=60)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)

            for keyword in KEYWORDS:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches = pattern.finditer(text)
                for match in matches:
                    idx = match.start()
                    snippet = text[max(0, idx - 40): idx + 60]
                    cursor.execute('INSERT INTO iocs (url, keyword, context) VALUES (?, ?, ?)',
                                (url, keyword, snippet))
                    log_area.write(f"✅ Found keyword: **{keyword}** in {url}")
            conn.commit()
        except Exception as e:
            log_area.write(f"❌ Failed to crawl {url}: {e}")

        progress.progress((i + 1) / len(onion_sites))
        time.sleep(3)


    # Read and export
    df = pd.read_sql_query("SELECT * FROM iocs", conn)
    df.to_csv(CSV_FILE, index=False)
    st.success("Crawling completed.")

    # Encrypt
    key = Fernet.generate_key()
    with open(FERNET_KEY_FILE, 'wb') as f:
        f.write(key)
    fernet = Fernet(key)
    with open(CSV_FILE, 'rb') as f:
        encrypted = fernet.encrypt(f.read())
    with open(FERNET_FILE, 'wb') as f:
        f.write(encrypted)

    # Save in session
    st.session_state.df = df
    st.session_state.encrypted_file = FERNET_FILE

# --- Restore or Show ---
if st.session_state.df is not None:
    render_results(st.session_state.df, st.session_state.encrypted_file)
