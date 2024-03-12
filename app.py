import streamlit as st
import requests
import csv
from datetime import datetime, timedelta
import pandas as pd
import altair as alt
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Fetch API keys from environment variables
AYLIEN_APP_ID = os.getenv('AYLIEN_APP_ID')
AYLIEN_API_KEY = os.getenv('AYLIEN_API_KEY')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Function to get authentication header for Aylien API
def get_aylien_auth_header():
    return {
        'X-Application-Id': AYLIEN_APP_ID,
        'X-Application-Key': AYLIEN_API_KEY
    }

# Function to fetch news stories from Aylien API
def fetch_news_stories(tickers):
    all_stories = []
    base_url = 'https://api.aylien.com/news/stories'
    start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%dT%H:%M:%SZ')  # past 5 years
    end_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

    headers = get_aylien_auth_header()

    for ticker in tickers:
        params = {
            'entities.stock_tickers': ticker,
            'published_at.start': start_date,
            'published_at.end': end_date,
            'language': 'en',
            'per_page': 100,
            'sort_by': 'published_at',
            'sort_direction': 'desc'
        }

        while True:
            response = requests.get(base_url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                stories = data.get('stories', [])
                all_stories.extend(stories)

                if 'links' in data and 'next' in data['links']:
                    params['cursor'] = data['links']['next']
                else:
                    break
            else:
                st.error(f"Failed to fetch stories for ticker {ticker}: {response.status_code} - {response.text}")
                break

    st.success(f"Total number of stories fetched for tickers {tickers}: {len(all_stories)}")
    return all_stories

# Function to fetch historical stock data from Alpha Vantage API
def fetch_stock_data(symbol):
    base_url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_API_KEY
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get('Time Series (Daily)', {})
    else:
        st.error(f"Failed to fetch historical stock data for {symbol}: {response.status_code} - {response.text}")
        return {}

# Function to save stock data to CSV file
def save_stock_data_to_csv(data, symbol, file_name='stock_data.csv'):
    with open(file_name, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])

        for date, info in data.items():
            writer.writerow([
                date, info.get('1. open'), info.get('2. high'),
                info.get('3. low'), info.get('4. close'), info.get('5. volume')
            ])

    st.success(f"Historical stock data for {symbol} has been written to {file_name}")

def main():
    st.title("Stock News and Historical Data Fetcher")

    symbol = st.text_input("Enter a stock symbol (e.g., AAPL):")

    if st.button("Fetch News Stories"):
        if not symbol:
            st.warning("Please enter a valid stock symbol.")
        else:
            news_stories = fetch_news_stories([symbol])
            st.table(news_stories)

    if st.button("Fetch Historical Stock Data"):
        if not symbol:
            st.warning("Please enter a valid stock symbol.")
        else:
            stock_data = fetch_stock_data(symbol)
            if stock_data:
                save_stock_data_to_csv(stock_data, symbol, f'{symbol}_stock_data.csv')
                df = pd.DataFrame(stock_data).T.reset_index()
                df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                
                # Convert Date column to datetime format
                df['Date'] = pd.to_datetime(df['Date'])
                
                # Plot historical stock data
                line_chart = alt.Chart(df).mark_line().encode(
                    x='Date',
                    y='Close',
                    tooltip=['Date', 'Close']
                ).properties(
                    width=800,
                    height=400
                ).interactive()

                st.altair_chart(line_chart, use_container_width=True)

if __name__ == '__main__':
    main()
