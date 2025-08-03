# Use slim Python base
FROM python:3.10-slim

# Install OS-level dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tor curl gnupg2 libnss3 libevent-dev \
    && rm -rf /var/lib/apt/lists/*

# Set workdir and copy code
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data (ensure it's stored in standard location)
RUN python -m nltk.downloader punkt stopwords

# Set NLTK data path environment variable
ENV NLTK_DATA=/usr/local/nltk_data

# Minimal Tor configuration
RUN echo "SOCKSPort 9050" > /etc/tor/torrc

# Expose Streamlit port
EXPOSE 8501

# Run both Tor and Streamlit in one process
CMD ["sh", "-c", "tor & streamlit run app.py --server.enableCORS false --server.address 0.0.0.0"]
