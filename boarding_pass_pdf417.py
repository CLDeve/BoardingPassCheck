import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# API Configuration
AVIATION_EDGE_API_KEY = "56e9c3-1bef36"  # Your API key
FLIGHT_SCHEDULES_URL = "https://aviation-edge.com/v2/public/flights"

# Function to fetch today's departures from Singapore (SIN)
def fetch_today_departures():
    today = datetime.now().strftime("%Y-%m-%d")  # Get today's date
    params = {
        "key": AVIATION_EDGE_API_KEY,
        "depIata": "SIN",  # Singapore airport code
    }
    try:
        response = requests.get(FLIGHT_SCHEDULES_URL, params=params)
        response.raise_for_status()
        flights = response.json()

        # Check for valid data
        if not isinstance(flights, list) or "error" in flights:
            st.error("No departure data found or API error occurred.")
            return None

        # Filter departures for today
        today_departures = []
        for flight in flights:
            dep_time = flight.get("departure", {}).get("scheduledTime", "")
            if dep_time.startswith(today):
                today_departures.append({
                    "Flight Number": flight.get("flight", {}).get("iata", ""),
                    "Airline": flight.get("airline", {}).get("name", ""),
                    "Destination": flight.get("arrival", {}).get("iata", ""),
                    "Scheduled Time": dep_time,
                    "Status": flight.get("status", ""),
                })

        # Return the data
        return today_departures

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching departure details: {e}")
        return None

# Streamlit Interface
st.title("Download Today's Departures (SIN) as Excel")

# Fetch departures when button is clicked
if st.button("Fetch and Download Excel"):
    departures = fetch_today_departures()
    if departures:
        # Display data in the app
        st.write(f"Fetched {len(departures)} departures for today:")
        st.dataframe(departures)

        # Convert data to pandas DataFrame
        df = pd.DataFrame(departures)
        
        # Provide download button directly using pandas Excel writer
        @st.cache_data
        def convert_df_to_excel(df):
            # Write Excel data into a BytesIO buffer
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="Departures")
            return output.getvalue()

        excel_data = convert_df_to_excel(df)

        st.download_button(
            label="Download Excel",
            data=excel_data,
            file_name="Today_Departures.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.warning("No departures found for today!")
