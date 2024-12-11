import streamlit as st
import requests
from datetime import datetime, timedelta

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
            "Departure Date": flight_date.date(),  # Use date only
            "Seat Number": seat_number,
        }, None
    except Exception as e:
        return None, f"Error parsing barcode: {e}"

# Function to fetch flight departure details from API
def fetch_flight_departure(flight_iata, departure_airport="SIN"):
    params = {
        'key': API_KEY,
        'iataCode': departure_airport,
        'type': 'departure',
        'flightIata': flight_iata
    }
    try:
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            if data:
                # Assuming the response contains a list of flights
                return data[0], None
            else:
                return None, "No flight data found."
        else:
            return None, f"API returned an error: {response.status_code}"
    except Exception as e:
        return None, f"Error fetching flight data: {e}"

# Streamlit app
st.title("Boarding Pass Validator with Flight Checks")

# Input for barcode
barcode = st.text_input("Scan the barcode here:")

if st.button("Scan and Validate"):
    if barcode:
        # Parse the barcode
        parsed_data, parse_error = parse_iata_barcode(barcode)
        if parse_error:
            # Display parse error with red background
            st.markdown(
                """
                <style>
                .error {
                    background-color: red;
                    padding: 10px;
                    border-radius: 5px;
                    color: white;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.markdown(f"<div class='error'>{parse_error}</div>", unsafe_allow_html=True)
        else:
            # Display parsed boarding pass details
            st.subheader("Parsed Boarding Pass Details")
            st.json(parsed_data)

            # Fetch flight departure details
            flight_data, flight_error = fetch_flight_departure(parsed_data["Flight IATA"])
            if flight_error:
                # Display flight error with red background
                st.markdown(
                    """
                    <style>
                    .error {
                        background-color: red;
                        padding: 10px;
                        border-radius: 5px;
                        color: white;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                st.markdown(f"<div class='error'>{flight_error}</div>", unsafe_allow_html=True)
            else:
                # Display flight details
                st.subheader("Flight Departure Details")
                st.json(flight_data)
    else:
        # Handle empty barcode input with red background
        st.markdown(
            """
            <style>
            .error {
                background-color: red;
                padding: 10px;
                border-radius: 5px;
                color: white;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        st.markdown("<div class='error'>Please enter a valid barcode.</div>", unsafe_allow_html=True)
