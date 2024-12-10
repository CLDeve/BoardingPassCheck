import streamlit as st
import requests
from datetime import datetime, timedelta

# Title of the app
st.title("Singapore Departure Validator with Flight Schedules")

# API Configuration
AVIATION_EDGE_API_KEY = "56e9c3-1bef36"  # Your provided Aviation Edge API key
FLIGHT_SCHEDULES_URL = "https://aviation-edge.com/v2/public/flights"

# Function to query the departure details API
def get_departure_details(flight_iata, departure_airport, departure_date):
    params = {
        "key": AVIATION_EDGE_API_KEY,
        "depIata": departure_airport,  # Singapore (SIN)
        "flightIata": flight_iata,    # Combined airline and flight number
    }
    try:
        response = requests.get(FLIGHT_SCHEDULES_URL, params=params)
        response.raise_for_status()
        departures = response.json()

        # Debugging: Log the API response
        st.write("API Response:", departures)

        # Handle "No Record Found" error
        if not isinstance(departures, list) or departures.get("error") == "No Record Found":
            st.error("No record found for this departure. Please verify the flight details.")
            return None

        # Filter by departure date
        for departure in departures:
            dep_time = departure.get("departure", {}).get("scheduledTime", None)
            if dep_time and dep_time.startswith(departure_date.strftime("%Y-%m-%d")):
                return departure

        # No matching departure found
        st.warning("No matching departure found for the provided date.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching departure details: {e}")
        return None

# Helper function to parse IATA boarding pass data
def parse_iata_barcode(barcode):
    try:
        passenger_name = barcode[2:22].strip()  # Extract passenger name
        airline_code = barcode[36:39].strip()  # Extract and strip airline code
        flight_number = barcode[39:44].strip() # Extract and strip flight number
        julian_date = int(barcode[44:47])      # Extract Julian date
        seat_number = barcode[48:51].strip()   # Extract seat number

        # Convert Julian date to proper date
        year = datetime.now().year
        flight_date = datetime(year, 1, 1) + timedelta(days=julian_date - 1)

        # Combine airline code and flight number (no spaces, remove leading zeros)
        flight_iata = f"{airline_code}{flight_number.lstrip('0')}"

        return {
            "Passenger Name": passenger_name,
            "Flight Identifier (IATA)": flight_iata,
            "Departure Airport": "SIN",  # Hardcoded for Singapore departures
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

    # Fetch departure details from API
    departure_details = get_departure_details(
        st.session_state.parsed_data.get("Flight Identifier (IATA)", ""),
        st.session_state.parsed_data.get("Departure Airport", ""),
        st.session_state.parsed_data.get("Flight Date"),
    )

    if departure_details:
        st.subheader("Departure Details from API:")
        st.json(departure_details)
    else:
        st.warning("No departure details found for this flight.")
elif st.session_state.error_message:
    st.error(st.session_state.error_message)
