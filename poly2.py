import pandas as pd
import requests
import streamlit as st
import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
import os

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY')

# Function to create a folder if it doesn't exist
def create_folder_if_not_exists(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

# Function to plot predictive graph
def plot_predictive_graph(df, y_pred_proba):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df['date'], y_pred_proba[:, 1], label='Probability of Going Up', color='blue')
    ax.plot(df['date'], y_pred_proba[:, 0], label='Probability of Going Down', color='red')
    ax.set_xlabel('Date')
    ax.set_ylabel('Probability')
    ax.set_title('Predictive Probabilities of Stock Direction')
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

# Streamlit UI
st.title("Stock Predictive Analysis")

symbol = st.text_input("Enter Stock Symbol (e.g., AAPL):")

if st.button("Analyze Stock"):
    # Get current date and time
    current_datetime = datetime.datetime.now()

    # Calculate start and end dates relative to the current time
    start_date = (current_datetime - datetime.timedelta(days=1000)).strftime('%Y-%m-%d')  # Start date is 100 days ago
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

        # Preprocessing
        X = df[['o', 'h', 'l', 'c', 'v']]  # Features
        y = df['c'] > df['o']  # Target variable (1 if closing price is higher than opening price, else 0)

        # Splitting data into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Training RandomForestClassifier
        clf = RandomForestClassifier(random_state=42)
        clf.fit(X_train, y_train)

        # Predictions
        y_pred_proba = clf.predict_proba(X)

        # Plot predictive graph
        plot_predictive_graph(df, y_pred_proba)

    else:
        st.error("Error fetching data. Please check the symbol or try again later.")
