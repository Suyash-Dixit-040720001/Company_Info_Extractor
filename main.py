# pip install requirements


import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from googlesearch import search as google_search
import json
import os
import re

st.set_page_config(page_title="📊 Company Info Extractor", layout="centered")
st.title("🏢 Company Info Extractor")

# --- User Inputs ---
industry = st.text_input("Enter Industry", "Home Healthcare")
location = st.text_input("Enter Location (e.g., USA, California, Texas)", "USA")
num_results = st.slider("Number of Google Results to Fetch", 1, 100, 10)
num_pages_oc = st.slider("Number of OpenCorporates Pages to Query", 1, 100, 2)

# Mapping for known US states
state_code_map = {"Colorado": "us_co", "California": "us_ca", "New York": "us_ny", "Texas": "us_tx"}
state_code = state_code_map.get(location.strip(), None)

# --- Google API Config ---
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = st.secrets.get("GOOGLE_CSE_ID") or os.getenv("GOOGLE_CSE_ID")

# --- Search OpenCorporates ---
def search_opencorporates(industry, state_code=None, pages=2):
    results = []
    for page in range(1, pages+1):
        resp = requests.get(
            "https://api.opencorporates.com/v0.4/companies/search",
            params={"q": industry, "page": page, **({"jurisdiction_code": state_code} if state_code else {})}
        )
        if resp.ok:
            data = resp.json().get("results", {}).get("companies", [])
            if not data and page==1 and industry.lower()!="health":
                return search_opencorporates("Health", state_code, pages)
            for itm in data:
                c = itm.get("company", {})
                results.append({
                    "Company Name": c.get("name"),
                    "Company Website": c.get("homepage_url"),
                    "Industry": industry,
                    "HQ State": c.get("jurisdiction_code", location),
                    "HQ City": c.get("registered_address",{}).get("locality",""),
                    "Year Founded": c.get("incorporation_date",""),
                    "Product/Service":"","Employee Count":"","Revenue":"","LinkedIn":""
                })
    return pd.DataFrame(results)

# --- Improved Google Search to Capture Company Info Only ---
def search_google(industry, location, num_results):
    query = f"{industry} companies in {location} site:crunchbase.com OR site:linkedin.com OR site:owler.com"
    urls = list(google_search(query, num_results=num_results))
    results = []
    for url in urls:
        if any(domain in url for domain in ["linkedin.com/company", "crunchbase.com/organization", "owler.com/company"]):
            try:
                r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                title = soup.title.string.strip() if soup.title else url
                desc = ""
                m = soup.find('meta', attrs={'name':'description'}) or soup.find('meta', attrs={'property':'og:description'})
                if m: desc = m.get('content','').strip()
                city, state, year = "", location, ""
                linkedin_url = url if "linkedin.com" in url else ""
                company_website = ""

                # Try extracting official website from LinkedIn page
                if "linkedin.com/company" in url:
                    try:
                        website_tag = soup.find('a', attrs={"data-control-name": "page_details_module_website_external_link"})
                        if website_tag:
                            company_website = website_tag['href']
                    except: pass

                for tag in soup.find_all('script', type='application/ld+json'):
                    try:
                        d = json.loads(tag.string)
                        org = d if d.get('@type')=='Organization' else next((x for x in d if x.get('@type')=='Organization'), None) if isinstance(d, list) else None
                        if org:
                            addr = org.get('address', {})
                            city = addr.get('addressLocality', '')
                            state = addr.get('addressRegion', location)
                            year = org.get('foundingDate', '')
                            break
                    except: pass
                results.append({
                    "Company Name": title.replace('| LinkedIn', '').strip(),
                    "Company Website": company_website,
                    "Industry": industry,
                    "HQ State": state,
                    "HQ City": city,
                    "Year Founded": year,
                    "Product/Service": desc,
                    "Employee Count": "",
                    "Revenue": "",
                    "LinkedIn": linkedin_url
                })
            except: pass
    return pd.DataFrame(results)

# --- Utility to extract structured info ---
def extract_info_from_text(text):
    revenue = ""
    employees = ""
    founded = ""
    rev_match = re.search(r"(revenue|annual revenue)[^\d$]*(\$?\d+[\d,\.]*\s*(million|billion)?)", text, re.IGNORECASE)
    if rev_match:
        revenue = rev_match.group(2)
    emp_match = re.search(r"(\d{2,6})\s*(employees|people)", text, re.IGNORECASE)
    if emp_match:
        employees = emp_match.group(1)
    year_match = re.search(r"(founded in|since)\s*(\d{4})", text, re.IGNORECASE)
    if year_match:
        founded = year_match.group(2)
    return revenue, employees, founded

def get_linkedin_url(company_name):
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return ""
    query = f"{company_name} LinkedIn site:linkedin.com"
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}"
    try:
        resp = requests.get(url)
        items = resp.json().get('items', [])
        for item in items:
            link = item.get('link', '')
            if 'linkedin.com/company/' in link or 'linkedin.com/' in link:
                return link
    except:
        return ""
    return ""

# --- Enrichment using Google Programmable Search API ---
def enrich_with_google_custom_search(df):
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        st.warning("Google API key or CSE ID not configured.")
        return df

    enriched = []
    for _, row in df.iterrows():
        company_name = row['Company Name']
        query = f"{company_name} number of employees revenue founded site:{row['Company Website']}"
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}"
        try:
            resp = requests.get(url)
            items = resp.json().get('items', [])
            if items:
                snippet = items[0].get('snippet', '')
                row['Product/Service'] = snippet[:250]
                revenue, employees, founded = extract_info_from_text(snippet)
                if revenue:
                    row['Revenue'] = revenue
                if employees:
                    row['Employee Count'] = employees
                if founded:
                    row['Year Founded'] = founded
        except Exception as e:
            print(f"Google enrichment failed for {company_name}: {e}")
        if not row.get('LinkedIn'):
            row['LinkedIn'] = get_linkedin_url(company_name)
        enriched.append(row)
    return pd.DataFrame(enriched)

# --- Main ---
if st.button("🔍 Search Companies"):
    st.info(f"Searching '{industry}' in '{location}'...")
    df1 = search_opencorporates(industry, state_code, num_pages_oc)
    st.write(f"OpenCorporates found: {len(df1)}")
    df2 = search_google(industry, location, num_results)
    st.write(f"Google found: {len(df2)}")
    df_all = pd.concat([df1, df2], ignore_index=True)
    df_all = enrich_with_google_custom_search(df_all)

    if df_all.empty:
        st.warning("No companies found.")
    else:
        st.success(f"Found {len(df_all)} companies")
        st.dataframe(df_all)
        st.download_button("Download CSV", df_all.to_csv(index=False).encode(), "companies.csv", "text/csv")
