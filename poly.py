import pandas as pd
import requests
import streamlit as st
import datetime
import altair as alt
from dotenv import load_dotenv
import os

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY')

# Function to create a folder if it doesn't exist
def create_folder_if_not_exists(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

# Streamlit UI
st.title("Stock Historical Data")

symbol = st.text_input("Enter Stock Symbol (e.g., AAPL):")

if st.button("Get Historical Data"):
    # Get current date and time
    current_datetime = datetime.datetime.now()

    # Calculate start and end dates relative to the current time
    start_date = (current_datetime - datetime.timedelta(days=100)).strftime('%Y-%m-%d')  # Start date is 100 days ago
    end_date = current_datetime.strftime('%Y-%m-%d')  # End date is today

    url = f'https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}?apiKey={API_KEY}'

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        results = data['results']

        # Create DataFrame
        df = pd.DataFrame(results)

        # Convert timestamp to datetime
        df['date'] = pd.to_datetime(df['t'], unit='ms')

        # Create folder if not exists
        folder_name = 'historical_data'
        create_folder_if_not_exists(folder_name)

        # Save to CSV
        filename = f"{folder_name}/{symbol}_historical_data.csv"
        df.to_csv(filename, index=False)

        # Display data
        st.write(df)
        st.success(f"Data saved to {filename}")

        # Create chart with Altair
        base = alt.Chart(df).encode(x='date:T')

        # Line chart for closing prices
        line_chart = base.mark_line().encode(
            y='c:Q',
            color=alt.condition(
                alt.datum.o > alt.datum.c,
                alt.value("green"),
                alt.value("red")
            )
        ).properties(title=f"{symbol} Closing Prices")

        # Volume chart
        volume_chart = base.mark_bar(opacity=0.5).encode(
            y='v:Q'
        ).properties(title="Trading Volume")

        # Combine both charts
        combined_chart = alt.layer(line_chart, volume_chart).resolve_scale(y='independent')

        # Display combined chart
        st.altair_chart(combined_chart, use_container_width=True)

    else:
        st.error("Error fetching data. Please check the symbol or try again later.")
