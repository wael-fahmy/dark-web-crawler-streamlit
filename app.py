# import streamlit as st
# import requests
# from bs4 import BeautifulSoup
# import re
# import sqlite3
# import pandas as pd
# import matplotlib.pyplot as plt
# from wordcloud import WordCloud
# from nltk.corpus import stopwords
# from nltk.tokenize import word_tokenize
# from collections import Counter
# from cryptography.fernet import Fernet
# import nltk
# import time
# import os
# if 'df' not in st.session_state:
#     st.session_state.df = None
# if 'encrypted_file' not in st.session_state:
#     st.session_state.encrypted_file = None
# # NLTK setup
# nltk.download('punkt')
# nltk.download('stopwords')

# # --- Config ---
# DB_FILE = 'ioc_results.db'
# CSV_FILE = 'ioc_results.csv'
# FERNET_KEY_FILE = 'fernet.key'
# FERNET_FILE = 'ioc_results.csv.fernet'
# PROXIES = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}

# st.set_page_config(page_title="Dark Web Crawler", layout="wide")

# st.title("🕵️ Passive Dark Web Crawler GUI")
# st.markdown("Crawl .onion sites passively over Tor, extract CTI keywords, visualize results, and export data.")

# # --- Sidebar Inputs ---
# st.sidebar.header("Crawler Settings")

# # Onion Sites Input
# onion_sites_input = st.sidebar.text_area(
#     "Enter .onion sites (one per line):",
#     "http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion\n"
#     "http://facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion"
# )
# onion_sites = [site.strip() for site in onion_sites_input.splitlines() if site.strip()]

# # Keywords Input
# keywords_input = st.sidebar.text_input(
#     "Enter keywords (comma-separated):",
#     "password,credential,exploit,leak,malware,ransomware,botnet"
# )
# KEYWORDS = [kw.strip().lower() for kw in keywords_input.split(",") if kw.strip()]

# # Start Crawling Button
# start_crawl = st.sidebar.button("🚀 Start Crawling")

# # --- Crawler Logic ---
# if start_crawl:
#     # Setup DB
#     if os.path.exists(DB_FILE):
#         os.remove(DB_FILE)
#     conn = sqlite3.connect(DB_FILE)
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS iocs (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             url TEXT,
#             keyword TEXT,
#             context TEXT,
#             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
#         )
#     ''')
#     conn.commit()

#     st.info("Starting crawl...")
#     progress = st.progress(0)
#     log_area = st.empty()

#     for i, url in enumerate(onion_sites):
#         try:
#             log_area.write(f"Crawling: {url}")
#             response = requests.get(url, proxies=PROXIES, timeout=30)
#             soup = BeautifulSoup(response.text, 'html.parser')
#             text = soup.get_text(separator=' ', strip=True)

#             for keyword in KEYWORDS:
#                 pattern = re.compile(rf'{re.escape(keyword)}', re.IGNORECASE)
#                 matches = pattern.finditer(text)
#                 for match in matches:
#                     idx = match.start()
#                     snippet = text[max(0, idx - 40): idx + 60]
#                     cursor.execute('INSERT INTO iocs (url, keyword, context) VALUES (?, ?, ?)',
#                                    (url, keyword, snippet))
#                     log_area.write(f"✅ Found keyword: **{keyword}** in {url}")

#             conn.commit()
#         except Exception as e:
#             log_area.write(f"❌ Failed to crawl {url}: {e}")

#         progress.progress((i + 1) / len(onion_sites))
#         time.sleep(2)

#     # Export CSV
#     df = pd.read_sql_query("SELECT * FROM iocs", conn)
#     st.session_state.df = df
#     df.to_csv(CSV_FILE, index=False)
#     st.success("Crawling completed!")

#     # Display Results
#     st.subheader("🔍 Extracted IOCs")
#     st.dataframe(df)

#     # Visualization
#     if not df.empty:
#         st.subheader("📊 Keyword Frequency")
#         keyword_counts = df['keyword'].value_counts()
#         st.bar_chart(keyword_counts)

#         st.subheader("☁️ Word Cloud")
#         wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(keyword_counts.to_dict())
#         fig, ax = plt.subplots(figsize=(10, 5))
#         ax.imshow(wordcloud, interpolation='bilinear')
#         ax.axis('off')
#         st.pyplot(fig)

#         # NLP Token Analysis
#         st.subheader("🧠 NLP Token Analysis")
#         text_blob = ' '.join(df['context'].dropna().astype(str))
#         tokens = word_tokenize(text_blob.lower())
#         filtered = [t for t in tokens if t.isalnum() and t not in stopwords.words('english')]
#         top_tokens = Counter(filtered).most_common(20)
#         st.table(pd.DataFrame(top_tokens, columns=["Token", "Count"]))

#         # Encrypt CSV
#         key = Fernet.generate_key()
#         with open(FERNET_KEY_FILE, 'wb') as f:
#             f.write(key)
#         fernet = Fernet(key)
#         with open(CSV_FILE, 'rb') as f:
#             encrypted = fernet.encrypt(f.read())
#         with open(FERNET_FILE, 'wb') as f:
#             f.write(encrypted)
#         st.success("CSV encrypted successfully.")
#         st.session_state.encrypted_file = FERNET_FILE
#         # Download Buttons
#         with open(CSV_FILE, 'rb') as f:
#             st.download_button("⬇️ Download CSV", f, file_name="ioc_results.csv", key="csv_download_main")
#         with open(FERNET_FILE, 'rb') as f:
#             st.download_button("🔐 Download Encrypted CSV (.fernet)", f, file_name="ioc_results.csv.fernet", key="fernet_download_main")
#     else:
#         st.warning("No keywords found in the crawled pages.")
# # --- Display previous session results ---
# if st.session_state.df is not None:
#     st.subheader("🔍 Extracted IOCs")
#     st.dataframe(st.session_state.df)

#     st.subheader("📊 Keyword Frequency")
#     keyword_counts = st.session_state.df['keyword'].value_counts()
#     st.bar_chart(keyword_counts)

#     st.subheader("☁️ Word Cloud")
#     wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(keyword_counts.to_dict())
#     fig, ax = plt.subplots(figsize=(10, 5))
#     ax.imshow(wordcloud, interpolation='bilinear')
#     ax.axis('off')
#     st.pyplot(fig)

#     st.subheader("🧠 NLP Token Analysis")
#     text_blob = ' '.join(st.session_state.df['context'].dropna().astype(str))
#     tokens = word_tokenize(text_blob.lower())
#     filtered = [t for t in tokens if t.isalnum() and t not in stopwords.words('english')]
#     top_tokens = Counter(filtered).most_common(20)
#     st.table(pd.DataFrame(top_tokens, columns=["Token", "Count"]))

#     with open(CSV_FILE, 'rb') as f:
#         st.download_button("⬇️ Download CSV", f, file_name="ioc_results.csv", key="csv_download_restore")
#     if st.session_state.encrypted_file and os.path.exists(st.session_state.encrypted_file):
#         with open(st.session_state.encrypted_file, 'rb') as f:
#             st.download_button("🔐 Download Encrypted CSV (.fernet)", f, file_name="ioc_results.csv.fernet", key="fernet_download_restore")
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

# --- Init ---
nltk.download('punkt')
nltk.download('stopwords')

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

# --- Sidebar ---
st.sidebar.header("Crawler Settings")

onion_sites_input = st.sidebar.text_area(
    "Enter .onion sites (one per line):",
    "http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion\n"
    "http://facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion"
)
onion_sites = [s.strip() for s in onion_sites_input.splitlines() if s.strip()]

keywords_input = st.sidebar.text_input(
    "Enter keywords (comma-separated):",
    "password,credential,exploit,leak,malware,ransomware,botnet"
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

    with open(CSV_FILE, 'rb') as f:
        st.download_button("⬇️ Download CSV", f, file_name="ioc_results.csv", key="csv_download")

    if encrypted_file and os.path.exists(encrypted_file):
        with open(encrypted_file, 'rb') as f:
            st.download_button("🔐 Download Encrypted CSV (.fernet)", f, file_name="ioc_results.csv.fernet", key="fernet_download")

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

    for i, url in enumerate(onion_sites):
        try:
            log_area.write(f"Crawling: {url}")
            response = requests.get(url, proxies=PROXIES, timeout=30)
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
        time.sleep(2)

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
