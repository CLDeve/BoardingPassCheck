import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from datetime import datetime

# API Configuration
API_KEY = '56e9c3-1bef36'  # Your Aviation Edge API key
IATA_CODE = 'SIN'  # Singapore Changi Airport
TYPE = 'departure'  # Fetch departures

# Fetch today's date in YYYY-MM-DD format
today = datetime.now().strftime('%Y-%m-%d')

# API endpoint
url = f'https://aviation-edge.com/v2/public/timetable'

# Function to fetch departure data
def fetch_departures():
    params = {
        'key': API_KEY,
        'iataCode': IATA_CODE,
        'type': TYPE,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        flights = response.json()

        # Filter flights departing today
        departures = []
        for flight in flights:
            dep_time = flight.get('departure', {}).get('scheduledTime')
            if dep_time and dep_time.startswith(today):  # Check if time exists and matches today's date
                departures.append({
                    'Flight Number': flight.get('flight', {}).get('iataNumber', 'N/A'),
                    'Airline': flight.get('airline', {}).get('name', 'N/A'),
                    'Destination': flight.get('arrival', {}).get('iataCode', 'N/A'),
                    'Scheduled Time': dep_time,
                    'Status': flight.get('status', 'N/A')
                })
        return departures
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching departure details: {e}")
        return None

# Streamlit Interface
st.title("Fetch and Download Today's Departures")

if st.button("Fetch Departures"):
    departures = fetch_departures()
    if departures:
        # Convert to DataFrame
        df = pd.DataFrame(departures)

        # Display data in the app
        st.write(f"Fetched {len(departures)} departures.")
        st.dataframe(df)

        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Departures')
        output.seek(0)

        # Provide download button
        st.download_button(
            label="Download Excel File",
            data=output,
            file_name=f"SIN_Departures_{today}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No departures found for today.")
