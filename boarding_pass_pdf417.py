import streamlit as st
import requests
from datetime import datetime, timedelta

# Title of the app
st.title("Singapore Flight Validator with Flight Schedules")

# API Configuration
AVIATION_EDGE_API_KEY = "56e9c3-1bef36"  # Your provided Aviation Edge API key
FLIGHT_SCHEDULES_URL = "https://aviation-edge.com/v2/public/flights"

# Function to query the Flight Schedules API
def get_flight_schedule(flight_iata, flight_date):
    params = {
        "key": AVIATION_EDGE_API_KEY,
        "depIata": "SIN",  # Hardcoded for Singapore departures
        "flightIata": flight_iata,  # Combined airline code and flight number
    }
    try:
        response = requests.get(FLIGHT_SCHEDULES_URL, params=params)
        response.raise_for_status()
        flights = response.json()

        # Debugging: Log the combined flight identifier and API response
        st.write("Flight Identifier (IATA):", flight_iata)
        st.write("API Response:", flights)

        # Handle "No Record Found" error
        if not isinstance(flights, list) or flights.get("error") == "No Record Found":
            st.error("No record found in the API. Please verify the flight details.")
            return None

        # Filter results based on flight date
        for flight in flights:
            dep_time = flight.get("departure", {}).get("scheduledTime", None)
            if dep_time and dep_time.startswith(flight_date.strftime("%Y-%m-%d")):
                return flight

        # No matching flight found
        st.warning("No matching flight found in the API for the provided date.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching flight schedule: {e}")
        return None

# Helper function to parse IATA boarding pass data
def parse_iata_barcode(barcode):
    try:
        passenger_name = barcode[2:22].strip()  # Extract passenger name
        airline_code = barcode[36:39]          # Extract airline code
        flight_number = barcode[39:44].strip() # Extract flight number
        julian_date = int(barcode[44:47])      # Extract Julian date
        seat_number = barcode[48:51].strip()   # Extract seat number

        # Convert Julian date to proper date
        year = datetime.now().year
        flight_date = datetime(year, 1, 1) + timedelta(days=julian_date - 1)

        # Combine airline code and flight number
        flight_iata = f"{airline_code}{flight_number.lstrip('0')}"  # Remove leading zeros

        return {
            "Passenger Name": passenger_name,
            "Flight Identifier (IATA)": flight_iata,
            "Flight Date": flight_date.date(),
            "Seat Number": seat_number,
        }, None
    except Exception as e:
        return None, f"Error parsing barcode: {e}"

# Initialize session state
if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = None
    st.session_state.error_message = None
    st.session_state.scanned_info = ""

# Input field for barcode
barcode_data = st.text_input(
    "Scan the barcode here:",
    placeholder="Place the cursor here and scan your boarding pass...",
)

# Scan button
if st.button("Scan"):
    if barcode_data:
        st.session_state.parsed_data, st.session_state.error_message = parse_iata_barcode(barcode_data)
        st.session_state.scanned_info = barcode_data

        # Debugging: Validate parsed data
        st.write("Parsed Data:", st.session_state.parsed_data)
    else:
        st.error("Please scan a barcode before clicking the 'Scan' button.")

# Display parsed results or errors
if st.session_state.parsed_data:
    st.subheader("Parsed Boarding Pass Details:")
    st.json(st.session_state.parsed_data)

    # Fetch flight schedule from API
    flight_schedule = get_flight_schedule(
        st.session_state.parsed_data.get("Flight Identifier (IATA)", ""),
        st.session_state.parsed_data.get("Flight Date"),
    )

    if flight_schedule:
        st.subheader("Flight Schedule from API:")
        st.json(flight_schedule)
    else:
        st.warning("No flight schedule found for this flight.")
elif st.session_state.error_message:
    st.error(st.session_state.error_message)
