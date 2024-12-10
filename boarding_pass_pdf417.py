import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from io import BytesIO

# API Configuration
API_KEY = '56e9c3-1bef36'  # Your Aviation Edge API key
BASE_URL = 'https://aviation-edge.com/v2/public/timetable'

# Helper function to parse IATA boarding pass barcode
def parse_iata_barcode(barcode):
    try:
        passenger_name = barcode[2:22].strip()  # Extract passenger name
        airline_code = barcode[36:39].strip()  # Extract airline code
        flight_number = barcode[39:44].strip()  # Extract flight number
        julian_date = int(barcode[44:47])  # Julian date for flight
        seat_number = barcode[48:51].strip()  # Extract seat number

        # Convert Julian date to proper date
        year = datetime.now().year
        flight_date = datetime(year, 1, 1) + timedelta(days=julian_date - 1)

        # Combine airline code and flight number
        flight_iata = f"{airline_code}{flight_number.lstrip('0')}"

        return {
            "Passenger Name": passenger_name,
            "Flight IATA": flight_iata,
            "Departure Date": flight_date.date(),
            "Seat Number": seat_number,
        }, None
    except Exception as e:
        return None, f"Error parsing barcode: {e}"

# Function to fetch flight departure details from API
def fetch_flight_departure(flight_iata, departure_airport="SIN"):
    params = {
        "key": API_KEY,
        "iataCode": departure_airport,  # Hardcoded for Singapore departures
        "type": "departure"
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        flights = response.json()

        # Filter for the specific flight
        for flight in flights:
            if flight.get("flight", {}).get("iataNumber") == flight_iata:
                return {
                    "Flight Number": flight.get("flight", {}).get("iataNumber", "N/A"),
                    "Airline": flight.get("airline", {}).get("name", "N/A"),
                    "Destination": flight.get("arrival", {}).get("iataCode", "N/A"),
                    "Scheduled Departure Time": flight.get("departure", {}).get("scheduledTime", "N/A"),
                    "Status": flight.get("status", "N/A")
                }
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching departure details: {e}")
        return None

# Streamlit Interface
st.title("Boarding Pass Validator with Departure Search")

# Scan boarding pass barcode
barcode_data = st.text_input(
    "Scan the barcode here:",
    placeholder="Place the cursor here and scan your boarding pass...",
)

# Fetch and Display Results
if st.button("Scan and Search"):
    if barcode_data:
        # Parse the barcode
        parsed_data, error = parse_iata_barcode(barcode_data)
        if parsed_data:
            st.subheader("Parsed Boarding Pass Details")
            st.json(parsed_data)

            # Search departure details
            flight_details = fetch_flight_departure(parsed_data["Flight IATA"])
            if flight_details:
                st.subheader("Flight Departure Details")
                st.json(flight_details)
            else:
                st.warning("No departure details found for this flight.")
        else:
            st.error(error)
    else:
        st.error("Please scan a barcode first.")
