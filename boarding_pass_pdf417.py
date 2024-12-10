import streamlit as st
import requests
from datetime import datetime, timedelta

# Title of the app
st.title("IATA Boarding Pass Validator with Flight Tracking")

# API Configuration
AVIATION_EDGE_API_KEY = "56e9c3-1bef36"  # Your provided Aviation Edge API key
FLIGHT_TRACKER_URL = "https://aviation-edge.com/v2/public/timetable"

# Function to query the API
def get_flight_details(departure_airport, flight_number, flight_date):
    params = {
        "key": AVIATION_EDGE_API_KEY,
        "iataCode": departure_airport,
        "type": "departure",
    }
    try:
        response = requests.get(FLIGHT_TRACKER_URL, params=params)
        response.raise_for_status()
        flights = response.json()

        # Filter results based on flight number and date
        for flight in flights:
            if (flight["flight"]["iataNumber"] == flight_number and
                flight["departure"]["scheduledTime"].startswith(flight_date.strftime("%Y-%m-%d"))):
                return flight
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching flight details: {e}")
        return None

# Helper function to parse IATA boarding pass data
def parse_iata_barcode(barcode):
    try:
        passenger_name = barcode[2:22].strip()  # Extract passenger name
        departure_airport = barcode[30:33]     # Extract departure airport code
        arrival_airport = barcode[33:36]       # Extract arrival airport code
        airline_code = barcode[36:39]          # Extract airline code
        flight_number = barcode[39:44].strip() # Extract flight number
        julian_date = int(barcode[44:47])      # Extract Julian date
        seat_number = barcode[48:51].strip()   # Extract seat number

        # Convert Julian date to proper date
        year = datetime.now().year
        flight_date = datetime(year, 1, 1) + timedelta(days=julian_date - 1)

        # Return parsed data and no error message
        return {
            "Passenger Name": passenger_name,
            "Departure Airport": departure_airport,
            "Arrival Airport": arrival_airport,
            "Airline Code": airline_code,
            "Flight Number": flight_number,
            "Flight Date": flight_date.date(),
            "Seat Number": seat_number,
        }, None
    except Exception as e:
        return None, f"Error parsing barcode: {e}"

# Initialize session state
if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = None
    st.session_state.error_message = None
    st.session_state.last_barcode = ""

# Callback to process and clear input
def process_and_clear_input():
    barcode_data = st.session_state.barcode_input
    if barcode_data and barcode_data != st.session_state.last_barcode:
        st.session_state.last_barcode = barcode_data
        st.session_state.parsed_data, st.session_state.error_message = parse_iata_barcode(barcode_data)
    st.session_state.barcode_input = ""

# Input field for barcode
st.text_input(
    "Scan the barcode here:",
    placeholder="Place the cursor here and scan your boarding pass...",
    key="barcode_input",
    on_change=process_and_clear_input,
)

# Display parsed results or errors
if st.session_state.parsed_data:
    st.json(st.session_state.parsed_data)

    # Fetch flight details from API
    flight_details = get_flight_details(
        st.session_state.parsed_data["Departure Airport"],
        st.session_state.parsed_data["Flight Number"],
        st.session_state.parsed_data["Flight Date"],
    )

    if flight_details:
        st.subheader("Flight Details from API:")
        st.json(flight_details)
    else:
        st.error("No flight details found for this flight.")
elif st.session_state.error_message:
    st.error(st.session_state.error_message)