📘 README: Company Info Extractor
🧾 Overview
Company Info Extractor is a Streamlit-based web application that helps users find and compile key business information about companies in a given industry and location.

The tool aggregates and enriches company data from:

OpenCorporates API

Google Search

LinkedIn

Google Programmable Search (CSE API)

🚀 Features
🔍 Search by Industry & Location
Get companies related to a specific industry in a given region (e.g., “Home Healthcare in USA”).

📑 Data Sources Used:

OpenCorporates: Fetches registered businesses and basic metadata.

Google Search: Scrapes LinkedIn, Crunchbase, and Owler pages for company summaries.

Google Programmable Search API: Extracts details like revenue, employee count, and founding year using structured snippets.

🧠 Smart Extraction with Regex:

Auto-detects phrases for revenue, team size, and founding year from company descriptions/snippets.

📎 LinkedIn URL Enrichment:

Searches and appends company LinkedIn profiles if not available in scraped data.

💾 Export:

View results in an interactive table

Download the full dataset as a CSV

🛠️ How to Use
Run the app using Streamlit:

bash
streamlit run app.py
Provide input:

Industry: e.g., Home Healthcare

Location: e.g., USA, California

Number of Google Results: how many links to process

Number of OpenCorporates Pages: how many pages to search (each page = ~10 companies)

Click "🔍 Search Companies"

Results will be displayed and enriched live

Download CSV using the export button

🔐 API Key Setup
You must provide the following keys as Streamlit secrets or environment variables:

toml
# .streamlit/secrets.toml
GOOGLE_API_KEY = "your_google_api_key"
GOOGLE_CSE_ID = "your_custom_search_engine_id"
OR set them via environment variables:

bash
export GOOGLE_API_KEY=your_google_api_key
export GOOGLE_CSE_ID=your_custom_search_engine_id
