import streamlit as st
import requests
import pandas as pd

# API Configuration
AVIATION_EDGE_API_KEY = "56e9c3-1bef36"  # Replace with your valid API key
ENTIRE_DATASET_URL = f"https://aviation-edge.com/v2/public/schedules?key={AVIATION_EDGE_API_KEY}"

# Function to fetch entire dataset for departures
def fetch_entire_departures():
    params = {
        "depIata": "SIN",  # Fetch departures from Singapore (SIN)
    }
    try:
        response = requests.get(ENTIRE_DATASET_URL, params=params)
        response.raise_for_status()
        flights = response.json()

        # Check for valid data
        if not isinstance(flights, list):
            st.error("No departure data found or API error occurred.")
            return None

        # Process the data
        departures = []
        for flight in flights:
            dep_info = flight.get("departure", {})
            arr_info = flight.get("arrival", {})
            airline_info = flight.get("airline", {})
            flight_info = flight.get("flight", {})

            departures.append({
                "Flight Number": flight_info.get("iata", ""),
                "Airline": airline_info.get("name", ""),
                "Destination": arr_info.get("iata", ""),
                "Scheduled Departure Time": dep_info.get("scheduledTime", ""),
                "Status": flight.get("status", "Unknown"),
            })

        return departures
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching departure details: {e}")
        return None

# Streamlit Interface
st.title("Download Entire Departure Dataset (SIN)")

if st.button("Fetch and Download Dataset"):
    # Fetch data
    departures = fetch_entire_departures()
    if departures:
        # Convert to DataFrame
        df = pd.DataFrame(departures)

        # Display fetched data
        st.write(f"Fetched {len(departures)} departures.")
        st.dataframe(df)

        # Convert DataFrame to Excel and allow download
        @st.cache_data
        def convert_df_to_excel(df):
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="Departures")
            return output.getvalue()

        excel_data = convert_df_to_excel(df)

        st.download_button(
            label="Download Excel File",
            data=excel_data,
            file_name="Departures_SIN.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.warning("No departures found or unable to fetch the dataset.")
