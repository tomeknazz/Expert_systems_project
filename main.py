import json
import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import requests

API_BASE_URL = "https://e6uw49pbah.execute-api.us-east-1.amazonaws.com/dev/weather/batch"
AUTH_TOKEN = "STUDENT_TOKEN_2026"
STATION_ID = "GDN_01"


def setup_storage():
    """Creates local folder structure for data layers."""
    directories = ['data/raw', 'data/processed', 'data/curated', 'outputs']
    for d in directories:
        os.makedirs(d, exist_ok=True)


# 1. DATA INGESTION
def fetch_and_store_raw_data(limit=200):
    """Fetches data from REST API and persists raw format."""
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    params = {
        "station_id": STATION_ID,
        "limit": limit
    }

    print(f"Fetching raw data from API for station {STATION_ID}...")
    response = requests.get(API_BASE_URL, headers=headers, params=params)

    if response.status_code != 200:
        print(f"API Error: {response.status_code} - {response.text}")
        return pd.DataFrame()

    data = response.json()

    # Persist raw data (JSON format)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_filepath = f'data/raw/raw_weather_{timestamp_str}.json'

    with open(raw_filepath, 'w') as f:
        json.dump(data, f)
    print(f"Raw data persisted to {raw_filepath}")

    # Extract required fields using the correct 'records' key from the JSON response
    measurements = data.get('records', [])

    if not measurements:
        print("No measurements found in API response.")
        return pd.DataFrame()

    df = pd.DataFrame(measurements)
    # Focus only on the required columns for anomaly detection
    return df[['timestamp', 'temperature']]


# 2. DATA PROCESSING & ANOMALY DETECTION
def process_data(df, window_size=24, z_score_threshold=2.0):
    """Normalizes timestamps, applies rolling statistics, and detects anomalies."""
    if df.empty:
        return df

    # Timestamp normalization
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)

    # Calculate rolling statistics only from previous measurements
    # so the current point is compared against historical context.
    history = df['temperature'].shift(1)
    df['rolling_mean'] = history.rolling(window=window_size, min_periods=1).mean().fillna(df['temperature'])
    df['rolling_std'] = history.rolling(window=window_size, min_periods=2).std()

    # Avoid division by zero
    df['rolling_std'] = df['rolling_std'].bfill().fillna(0.1).replace(0, 0.1)

    # Calculate Z-score
    df['z_score'] = (df['temperature'] - df['rolling_mean']) / df['rolling_std']

    # Flag anomalies based on threshold
    df['is_anomaly'] = df['z_score'].abs() > z_score_threshold

    # Save processed dataset
    processed_path = 'data/processed/processed_weather.csv'
    df.to_csv(processed_path, index=False)
    print(f"Processed data saved to {processed_path}")

    anomaly_count = int(df['is_anomaly'].sum())
    print(f"Detected anomalies: {anomaly_count} / {len(df)} records (threshold={z_score_threshold}, window={window_size})")

    if anomaly_count == 0:
        preview = df.assign(abs_z=df['z_score'].abs()).nlargest(min(5, len(df)), 'abs_z')
        print("No rows exceeded the anomaly threshold. Top candidates:")
        print(preview[['timestamp', 'temperature', 'rolling_mean', 'rolling_std', 'z_score']].to_string(index=False))

    return df


# 3. OUTPUT GENERATION
def generate_outputs(df):
    """Creates curated tables and plots visualizations."""
    if df.empty:
        print("No data to generate outputs.")
        return

    # Create curated anomaly table
    anomaly_table = df[df['is_anomaly']].copy()

    curated_path = 'data/curated/anomaly_table.csv'
    anomaly_table.to_csv(curated_path, index=False)
    print(f"Curated anomaly table saved to {curated_path}")

    if anomaly_table.empty:
        # Show the strongest candidates on the chart so the output is still useful
        # even when the chosen threshold is too strict for the current dataset.
        highlight_table = df.assign(abs_z=df['z_score'].abs()).nlargest(min(5, len(df)), 'abs_z')
        highlight_color = 'orange'
        highlight_label = 'Top candidates'
        print("No anomalies to plot; highlighting strongest candidates instead.")
    else:
        highlight_table = anomaly_table
        highlight_color = 'red'
        highlight_label = 'Anomaly'

    # Generate Chart
    plt.figure(figsize=(14.0, 7.0))  # type: ignore[arg-type]

    # Normal points
    normal_data = df[~df['is_anomaly']]
    plt.plot(df['timestamp'], df['temperature'], color='blue', label='Temperature Trend', alpha=0.4)
    plt.scatter(normal_data['timestamp'], normal_data['temperature'], color='blue', s=15, label='Normal')

    # Anomalies
    plt.scatter(highlight_table['timestamp'], highlight_table['temperature'], color=highlight_color, s=60,
                edgecolors='black', label=highlight_label, zorder=5)
    for _, row in highlight_table.iterrows():
        plt.annotate(f"{row['z_score']:.2f}", (row['timestamp'], row['temperature']), textcoords="offset points",
                     xytext=(0, 8), ha='center', fontsize=8)

    # Rolling mean trend line
    plt.plot(df['timestamp'], df['rolling_mean'], color='green', linestyle='--', label=f'Rolling Mean', alpha=0.8)

    plt.title(f'Temperature Anomaly Detection ({STATION_ID})')
    plt.xlabel('Timestamp')
    plt.ylabel('Temperature (°C)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()

    # Save chart
    chart_path = 'outputs/anomaly_chart.png'
    plt.savefig(chart_path)
    print(f"Chart saved to {chart_path}")


# MAIN EXECUTION FLOW
if __name__ == "__main__":
    setup_storage()

    # 1. Ingestion
    raw_df = fetch_and_store_raw_data(limit=200)

    # 2. Processing
    processed_df = process_data(raw_df)

    # 3. Analytics & Presentation
    generate_outputs(processed_df)
