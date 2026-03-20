import os
from openai import AzureOpenAI

os.environ['AZURE_OPENAI_KEY'] = 'Placeholder'
os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://mbeopenai.openai.azure.com/'

client = AzureOpenAI(
  api_key = os.getenv("AZURE_OPENAI_KEY"),
  api_version = "2023-05-15",
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
)

import pandas as pd
from datetime import datetime, timedelta
import requests as re
import sqlite3

commodity_data = {
    "globalsugar": {
        "US Sugar #11 Futures": "prices_sugar_us_future"
    },
    "europeansugar": {
        "eu_average": "prices_sugar_eu_average",
        "eu_region_2": "prices_sugar_eu_average_region2",
        "US Sugar #11 Futures": "prices_sugar_us_future"
    }
}

#SQLLITE Datenbank laden
def connect_to_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    return conn, cursor

#Nachrichten von Datenbasis laden
def get_news(cursor, start_date, end_date, commodity):

    if commodity not in ["globalsugar", "europeansugar"]:
        raise ValueError(f"No SQLite table available for commodity: {commodity}")

    #Nachrichten von 3 Wochen vor Start_Daten ziehen
    start_date_minus_3_weeks = start_date - timedelta(weeks=3)

    #Commodity-Nachrichten
    news_commodity = fetch_news(cursor, f"news_commodity_{commodity}", start_date_minus_3_weeks, end_date)

    #Makro-Nachrichten
    news_makro = fetch_news(cursor, f"news_makro_{commodity}", start_date_minus_3_weeks, end_date)

    return news_commodity, news_makro

def fetch_news(cursor, table_name, start_date_minus_3_weeks, end_date):
        
        # Convert Timestamp to a string in the SQLite-compatible format
        start_date_str = start_date_minus_3_weeks.strftime('%Y-%m-%d %H:%M:%S')
        end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

        query = f"""
        SELECT *
        FROM {table_name}
        WHERE Date BETWEEN ? AND ?
        """
        cursor.execute(query, (start_date_str, end_date_str))
        rows = cursor.fetchall()
        df_news = pd.DataFrame(rows, columns=[description[0] for description in cursor.description])
        df_news['Date'] = pd.to_datetime(df_news['Date']).dt.strftime('%m/%d/%Y')

        news_list = []
        for index, row in df_news.iterrows():
            news_list.append(row['Date'] + " " + row['summary'])
        return news_list

def get_commodity_profile(cursor, commodity):

    commodity_profile = ""

    if commodity == "globalsugar":
      query = f"""
        SELECT profile
        FROM profile_commodity
        WHERE name = '{commodity}'
        """
      cursor.execute(query)
      commodity_profile = cursor.fetchone()[0]

    elif commodity == "europeansugar":
      query = f"""
      SELECT profile
      FROM profile_commodity
      WHERE name = '{commodity}'
      """
      cursor.execute(query)
      commodity_profile = cursor.fetchone()[0]
      ##
    else:
      prompt = f"Generate a short description for the commodity {commodity} (e.g., sugar, wheat). Also list general positive and negative factors that might impact its price. Be brief and use keywords. Consider diverse factors including agricultural production conditions (e.g., weather patterns, crop yield), market dynamics (e.g., global supply and demand, stock levels), economic factors (e.g., inflation, trade policies), and environmental considerations (e.g., sustainability, climate change). Use the format Description: ..., Positive Factors: ..., Negative Factors: ..."

      response = client.chat.completions.create(
          model="GPT35",
          messages=[ #Verbesserungen möglich
              {"role": "system", "content": "Assistant is a large language model trained by OpenAI."},
              {"role": "user", "content": prompt}
          ]
      )

      commodity_profile = response.choices[0].message.content

    return commodity_profile

def get_fewshot_example(cursor, prompt_type): #Version Dictionary Mapping statt if Konstrukt

  if prompt_type == "forecast":
    query = f"""
        SELECT example
        FROM fewshot_examples
        WHERE type = '{prompt_type}'
        """
    cursor.execute(query)
    fewshot_example = cursor.fetchall()[0]
  elif prompt_type == "analysis":
    query = f"""
        SELECT example
        FROM fewshot_examples
        WHERE type = '{prompt_type}'
        """
    cursor.execute(query)
    fewshot_example = cursor.fetchall()[0]
  else:
    fewshot_example = ""

  return fewshot_example

def fetch_market_data(cursor, conn, commodity_name, source_name, start_date, end_date):
    table_name = commodity_data[commodity_name][source_name]
    query = f""" SELECT * FROM {table_name}
                 WHERE date >= '{start_date}' AND date <= '{end_date}' """
    df = pd.read_sql_query(query, conn)
    return df, source_name

def get_market_data(cursor, conn, commodity_name, start_date, end_date): #Funktionsname
    commodity_sources = commodity_data.get(commodity_name, {})
    if not commodity_sources:
        raise ValueError(f"No data available for commodity: {commodity_name}")

    formatted_data = ""
    for source_name in commodity_sources:
        filtered_data, source_label = fetch_market_data(cursor, conn, commodity_name, source_name, start_date, end_date)
        formatted_data += f"Source/Ticker: {source_label}:\n{filtered_data}\n\n"

    return formatted_data

def generate_analysis_prompt(commodity_name, start_date, end_date, commodity_profile, market_data, fewshot_example, news_commodity, news_makro):

    prompt = f"""
    Instruction: Explain the price movement for the commodity {commodity_name} from {start_date} to {end_date}, by analyzing the commodity's market profile, historical weekly news summary, keywords, and price history. Discuss the factors that influenced the price movement.

    Commodity Profile: {commodity_profile}
    Price History:
    {market_data}
    Recent {commodity_name} News: News are ordered weekly from oldest to latest.
    {news_commodity}

    Recent Makro News: News are ordered weekly from oldest to latest.
    {news_makro}

    Analysis Examples: ***
    {fewshot_example}
    ***

    Now analyze the commodity's price movement from {start_date} to {end_date}. Only use the prices provided.
    Provide a short Summary and a concise analysis of the Commodity Price Movement.
    The analysis should explain the five most important reasons, key factors and events that influenced the price movement.
    Do not just summarize the history. Reason step by step before the finalized output.
    Use format Summary: ..., Commodity Price Movement Analysis: ...
    Use bulletpoints for structuring the different factors and events in the analysis.
    """

    return prompt

def generate_forecast_prompt(commodity_name, start_date, end_date, commodity_profile, market_data, fewshot_example, news_commodity, news_makro):

    prompt = f"""
    Instruction: Today is: {start_date}. Forecast the price movement for the commodity {commodity_name} until {end_date}, given the commodity's market profile, historical weekly news summary, keywords, and price data.

    Commodity Profile: {commodity_profile}

    Price data:
    {market_data}
    Recent Commodity News: News are ordered weekly from oldest to latest.
    {news_commodity}

    Recent Makro News: News are ordered weekly from oldest to latest.
    {news_makro}

    Forecasting Examples: {fewshot_example}

    Predict what could be the Commodity Price Movement until {end_date}.

    Use format Summary: ..., Trend ..., Commodity Price Movement Analysis: ...

    In a short Summary explain the predicted price movement using: Bearish, Bullish and Neutral.

    Identify the precise trend using specific bins for upward and downward movements. The bins are categorized as follows:
    Downward Trends: 'D5+' (price drop > 5%), 'D5' (price drop 4-5%), 'D4', 'D3', 'D2', 'D1' (each representing a 1% decremental range in price drops).
    Upward Trends: 'U1' (price rise 0-1%), 'U2', 'U3', 'U4', 'U5' (price rise 4-5%), 'U5+' (price rise > 5%).
    Each bin represents a specific range of price movement, either a rise or a drop, by a certain percentage. Please determine the trend accurately using these bins.

    Use bulletpoints for structuring the consice Commodity Price Movement analysis.
    Do not just summarize the history. The price movement does not necessarily have to be the exact same as in the previous weeks or as in the examples.
    Reason step by step before the finalized output.
    """

    return prompt

def convert_dates(start_date, end_date):
    start_date_dt = pd.to_datetime(start_date)
    end_date_dt = pd.to_datetime(end_date)
    return start_date_dt, end_date_dt

def generate_prompt(prompt_type, commodity, start_date, end_date, commodity_profile, market_data, fewshot_example, news_commodity, news_makro):
    if prompt_type == "analysis":
        return generate_analysis_prompt(commodity, start_date, end_date, commodity_profile, market_data, fewshot_example, news_commodity, news_makro)
    elif prompt_type == "forecast":
        return generate_forecast_prompt(commodity, start_date, end_date, commodity_profile, market_data, fewshot_example, news_commodity, news_makro)
    else:
        raise ValueError("Invalid prompt type. Choose 'analysis' or 'forecast'.")

def generate_chat_response(generated_prompt, client):
    try:
        response = client.chat.completions.create(
            model="GPT35",
            messages=[
                {"role": "system", "content": "Forget all your previous instructions. Pretend you are a commodity market analyst. You are a financial expert with experience in analyzing, interpreting and forecasting commodity market trends, specifically focusing on commodities like sugar or wheat."},
                {"role": "user", "content": generated_prompt}
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        # Check if the error is related to BadRequest (400)
        if '400' in str(e):
            return "Please select a smaller period."
        else:
            # Handle other exceptions
            return f"An error occurred: {str(e)}"

def generate_response(start_date, end_date, commodity, prompt_type):
    start_date_dt, end_date_dt = convert_dates(start_date, end_date)

    # Open database connection
    conn, cursor = connect_to_database("C:\\Placeholder.db")  # PATH aktualisieren

    # Fetch data from Database:
    market_data = get_market_data(cursor, conn, commodity, start_date_dt, end_date_dt)
    news_commodity, news_makro = get_news(cursor, start_date_dt, end_date_dt, commodity)
    commodity_profile = get_commodity_profile(cursor, commodity)
    fewshot_example = get_fewshot_example(cursor, prompt_type)

    conn.close()

    generated_prompt = generate_prompt(prompt_type, commodity, start_date_dt, end_date_dt, commodity_profile, market_data, fewshot_example, news_commodity, news_makro)

    response = generate_chat_response(generated_prompt, client)

    return response


print(generate_response('03/19/2023', '04/01/2023', 'globalsugar', 'analysis'))

print(generate_response('04/21/2023', '05/01/2023', 'globalsugar', 'forecast'))
