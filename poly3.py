import pandas as pd
import requests
import streamlit as st
import datetime
import altair as alt
from dotenv import load_dotenv
import os
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import numpy as np

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY')

# Function to create a folder if it doesn't exist
def create_folder_if_not_exists(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

# Streamlit UI
st.title("Stock Historical Data and Forecast")

symbol = st.text_input("Enter Stock Symbol (e.g., AAPL):")

if st.button("Get Historical Data"):
    # Get current date and time
    current_datetime = datetime.datetime.now()

    # Calculate start and end dates relative to the current time
    start_date = (current_datetime - datetime.timedelta(days=1000)).strftime('%Y-%m-%d')
    end_date = current_datetime.strftime('%Y-%m-%d')

    url = f'https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}?apiKey={API_KEY}'

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        results = data['results']

        # Create DataFrame
        df = pd.DataFrame(results)

        # Convert timestamp to datetime and to ordinal for regression
        df['date'] = pd.to_datetime(df['t'], unit='ms')
        df['date_ordinal'] = df['date'].map(datetime.datetime.toordinal)

        # Create folder if not exists
        folder_name = 'historical_data'
        create_folder_if_not_exists(folder_name)

        # Save to CSV
        filename = f"{folder_name}/{symbol}_historical_data.csv"
        df.to_csv(filename, index=False)

        # Display data
        st.write(df)
        st.success(f"Data saved to {filename}")

        # Train a linear regression model
        X = df[['date_ordinal']]
        y = df['c']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = LinearRegression()
        model.fit(X_train, y_train)

        # Create future dates for forecasting
        future_dates = pd.date_range(start=df['date'].max(), periods=90).to_pydatetime()
        future_dates_ordinal = [date.toordinal() for date in future_dates]

        # Generate predictions
        predictions = model.predict(np.array(future_dates_ordinal).reshape(-1, 1))
        forecast_df = pd.DataFrame({
            'date': future_dates,
            'prediction': predictions
        })

        # Assuming a simple constant standard error for confidence intervals (not statistically accurate)
        std_error = np.std(y_test - model.predict(X_test))
        forecast_df['lower'] = forecast_df['prediction'] - 1.96 * std_error
        forecast_df['upper'] = forecast_df['prediction'] + 1.96 * std_error

        # Plot historical data
        historical_chart = alt.Chart(df).mark_line().encode(
            x='date:T',
            y=alt.Y('c:Q', axis=alt.Axis(title='Stock Price', titleColor='black')),
            color=alt.value('black')
        ).properties(
            title=f"{symbol} Stock Price Over Time"
        )

        # Plot prediction line and confidence intervals
        prediction_chart = alt.Chart(forecast_df).mark_line(color='red').encode(
            x='date:T',
            y=alt.Y('prediction:Q', axis=alt.Axis(title='Stock Price', titleColor='red'))
        )

        confidence_area = alt.Chart(forecast_df).mark_area(opacity=0.3, color='lightgrey').encode(
            x='date:T',
            y=alt.Y('lower:Q', axis=alt.Axis(title='Stock Price', titleColor='grey')),
            y2=alt.Y2('upper:Q')
        )

        # Combine charts
        combined_chart = alt.layer(historical_chart, prediction_chart, confidence_area).resolve_scale(y='independent')

        # Display the combined chart
        st.altair_chart(combined_chart, use_container_width=True)
    else:
        st.error("Error fetching data. Please check the symbol or try again later.")
