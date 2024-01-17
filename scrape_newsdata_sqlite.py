# Packages runterladen

!pip install openai
import os
from openai import AzureOpenAI
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

# Verbindung zu ChatGPT
os.environ['AZURE_OPENAI_KEY'] = '65ee6d36768e44b894d04c922e6cbe7a'
os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://mbeopenai.openai.azure.com/'

client = AzureOpenAI(
  api_key = os.getenv("AZURE_OPENAI_KEY"),
  api_version = "2023-05-15",
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Scraping Google News


# Artikel extrahieren mit BeautifulSoup
def extract_article_text(url, headers, max_tokens=3000):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        article_text = ''
        token_count = 0
        for paragraph_tag in soup.find_all('p'):
            paragraph_text = paragraph_tag.get_text()
            # Approximate the token count
            token_count += len(paragraph_text.split())
            if token_count > max_tokens:
                break
            article_text += ' ' + paragraph_text
        return article_text.strip()  # Remove leading/trailing whitespace
    except Exception as e:
        return f"Error extracting article text: {e}"

# Prompt an ChatGPT um Artikel zusammenzufassen
def summarize_news(article_text):
    if not article_text:
        return "N/A"
    prompt = f"Please provide a short summary for the following news text. The news text can be very noisy due to HTML extraction. In cases where the text either violates content policies, lacks relevant information, or JS is not enabled: simply only put 'N/A' without further explanations. News text: {article_text}"
    response = client.chat.completions.create(
        model="GPT35",
        messages=[
            {"role": "system", "content": "Assistant is a large language model trained by OpenAI."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# Alle Elemente (Datum, Überschrift, Quelle, Snippet und Artikel) aus Google News scrapen
def scrape_news_data(start_date, end_date, commodity, headers):
    date_range = f"cdr:1,cd_min:{start_date},cd_max:{end_date}"
    url = f"https://www.google.com/search?q={commodity}&tbm=nws&num=20&tbs={date_range}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    news_sources, news_titles, news_dates, news_snippets, news_articles, news_links = [], [], [], [], [], []
    for news_element in soup.select("div.SoaBEf"):
        news_url = news_element.find("a")["href"]
        news_links.append(news_url)
        news_titles.append(news_element.select_one("div.MBeuO").get_text())
        news_dates.append(news_element.select_one(".LfVVr").get_text())
        news_sources.append(news_element.select_one(".NUnG9d span").get_text())
        news_snippets.append(news_element.select_one(".GI74Re").get_text())
        news_articles.append(extract_article_text(news_url, headers))
    summaries = []
    for article in news_articles:
        summary = summarize_news(article)
        summaries.append(summary)
    df = pd.DataFrame({
        'source': news_sources,
        'title': news_titles,
        'timedate': news_dates,
        'snippet': news_snippets,
        'article': news_articles,
        'links': news_links,
        'summary': summaries
    })
    return df


# Wöchentlich 5 Nachrichten über den angegeneben Zeitraum
def scrape_weekly_news_data(start_date, end_date, commodity, headers):
    weekly_dfs = []

    # Iteriere über die Wochen im angegebenen Zeitraum
    current_date = datetime.strptime(start_date, "%m/%d/%Y")
    end_date = datetime.strptime(end_date, "%m/%d/%Y")
    while current_date <= end_date:
        week_start = current_date.strftime("%m/%d/%Y")
        week_end = (current_date + timedelta(days=6)).strftime("%m/%d/%Y")

        #Aktuelle Woche scrapen
        df_week = scrape_news_data(week_start, week_end, commodity, headers)
        weekly_dfs.append(df_week.head(5))  # Top 5 Nachrichten jede Woche
        current_date += timedelta(days=7)
    df_all = pd.concat(weekly_dfs, ignore_index=True)

    return df_all

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# Zeitraum
start_date = "12/01/2023"
end_date = "12/31/2023"

# Initialisiere die Anfrage und Speicherung in DFs
df_European_Economy = scrape_weekly_news_data(start_date, end_date, "European Economy", headers) #Hier die Wörter austauschen
df_European_Sugar = scrape_weekly_news_data(start_date, end_date, "European Sugar", headers)
df_Global_Sugar = scrape_weekly_news_data(start_date, end_date, "Global Sugar", headers)
df_Global_Economy = scrape_weekly_news_data(start_date, end_date, " Global Economy", headers)

#Tranformation der Dataframes
dataframe_names = ['Global_Sugar', 'European_Sugar', 'Global_Economy', 'European_Economy']

for name in dataframe_names:
    df = locals().get(f'df_{name}')
    if df is not None:
        if 'timedate' in df.columns:
          #Umwandlungen hier einfügen
            df['Date'] = pd.to_datetime(df['timedate'], format='%b %d, %Y') #Date Spalte konvertieren
            df.drop(columns=['timedate'], inplace=True)

import sqlite3

# Verbindung mit SQLite-Datenbank
db_path = "ZuckerboardGPT_12.db"
conn = sqlite3.connect(db_path)

# Hänge DataFrames an die Datenbank an
df_Global_Sugar.to_sql('News_USSugar', conn, index=False, if_exists='replace')
df_European_Sugar.to_sql('News_EUSugar', conn, index=False, if_exists='replace')
df_Global_Economy.to_sql('News_Makro', conn, index=False, if_exists='replace')
df_European_Economy.to_sql('News_MarkoEU', conn, index=False, if_exists='replace')

# Schließe die Verbindung zur Datenbank
conn.close()

