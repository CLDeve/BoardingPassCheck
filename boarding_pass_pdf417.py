import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz  # For time zone handling

# Define local time zone (Singapore Time for SIN)
LOCAL_TIMEZONE = pytz.timezone("Asia/Singapore")

# API Configuration
API_KEY = '56e9c3-1bef36'  # Replace with your actual API key
BASE_URL = 'https://aviation-edge.com/v2/public/timetable'

# Helper function to parse IATA boarding pass barcode
def parse_iata_barcode(barcode):
    try:
        passenger_name = barcode[2:22].strip()
        airline_code = barcode[36:39].strip()
        flight_number = barcode[39:44].strip()
        julian_date = int(barcode[44:47])
        seat_number = barcode[48:51].strip()

        year = datetime.now().year
        flight_date = datetime(year, 1, 1) + timedelta(days=julian_date - 1)

        flight_iata = f"{airline_code}{flight_number.lstrip('0')}"

        return {
            "Passenger Name": passenger_name,
            "Flight IATA": flight_iata,
            "Departure Date": flight_date.strftime("%d/%b/%Y"),  # Format date here
            "Seat Number": seat_number,
        }, None
    except Exception as e:
        return None, f"Error parsing barcode: {e}"

# Function to fetch flight departure details from API
def fetch_flight_departure(flight_iata, departure_airport="SIN"):
    params = {
        "key": API_KEY,
        "iataCode": departure_airport,
        "type": "departure"
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        flights = response.json()

        for flight in flights:
            if flight.get("flight", {}).get("iataNumber") == flight_iata:
                # Parse scheduledTime from API (assumed to be UTC)
                scheduled_time_utc = flight.get("departure", {}).get("scheduledTime", "")
                if scheduled_time_utc:
                    scheduled_datetime_utc = datetime.strptime(
                        scheduled_time_utc.split(".")[0], "%Y-%m-%dT%H:%M:%S"
                    ).replace(tzinfo=pytz.utc)  # Treat as UTC
                    # Convert to local time
                    scheduled_datetime_local = scheduled_datetime_utc.astimezone(LOCAL_TIMEZONE)
                    formatted_scheduled_time = scheduled_datetime_local.strftime("%d/%b/%Y %H:%M")
                else:
                    formatted_scheduled_time = "N/A"

                return {
                    "Flight Number": flight.get("flight", {}).get("iataNumber", "N/A"),
                    "Airline": flight.get("airline", {}).get("name", "N/A"),
                    "Destination": flight.get("arrival", {}).get("iataCode", "N/A"),
                    "Scheduled Departure Time": formatted_scheduled_time,
                    "Status": flight.get("status", "N/A"),
                    "Departure Airport": departure_airport,
                }
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching departure details: {e}")
        return None

# Function to validate flight details
def validate_flight(flight_details, boarding_pass_details):
    validation_messages = []

    # Check if departure is from SIN
    if flight_details.get("Departure Airport") != "SIN":
        validation_messages.append("Alert: Departure is not from SIN!")

    # Get and validate the scheduled departure time
    scheduled_time = flight_details.get("Scheduled Departure Time", "")
    if not scheduled_time or scheduled_time == "N/A":
        validation_messages.append("Alert: Scheduled Departure Time is missing!")
        return validation_messages

    try:
        # Parse the local scheduled time
        flight_datetime_local = datetime.strptime(scheduled_time, "%d/%b/%Y %H:%M").replace(tzinfo=LOCAL_TIMEZONE)
    except ValueError as e:
        validation_messages.append(f"Alert: Unable to parse Scheduled Departure Time. Error: {e}")
        return validation_messages

    # Check if flight date matches boarding pass date
    flight_date = flight_datetime_local.date()
    boarding_pass_date = datetime.strptime(boarding_pass_details.get("Departure Date"), "%d/%b/%Y").date()
    if flight_date != boarding_pass_date:
        validation_messages.append(
            f"Alert: Boarding pass date ({boarding_pass_details['Departure Date']}) "
            f"does not match flight date ({flight_datetime_local.strftime('%d/%b/%Y')})!"
        )

    # Check if flight date and time are within 24 hours
    current_time = datetime.now(LOCAL_TIMEZONE)
    time_difference = flight_datetime_local - current_time
    if time_difference.total_seconds() < 0:
        validation_messages.append(f"Alert: The flight has already departed! (Flight Time: {flight_datetime_local.strftime('%d/%b/%Y %H:%M')})")
    elif time_difference.total_seconds() > 86400:  # 24 hours in seconds
        validation_messages.append(
            f"Alert: Flight is not within the next 24 hours! (Flight Time: {flight_datetime_local.strftime('%d/%b/%Y %H:%M')}, "
            f"Current Time: {current_time.strftime('%d/%b/%Y %H:%M')})"
        )

    return validation_messages

# Streamlit Interface
if "barcode_data" not in st.session_state:
    st.session_state["barcode_data"] = ""

def process_scan():
    has_error = False
    if st.session_state["barcode_data"]:
        parsed_data, error = parse_iata_barcode(st.session_state["barcode_data"])
        if parsed_data:
            flight_details = fetch_flight_departure(parsed_data["Flight IATA"])
            if flight_details:
                st.json(flight_details)
                validation_results = validate_flight(flight_details, parsed_data)
                for message in validation_results:
                    st.error(message) if "Alert" in message else st.success(message)
            else:
                st.error("No departure details found.")
        else:
            st.error(error)
        st.session_state["barcode_data"] = ""

st.text_input(
    "Scan the barcode here:",
    placeholder="Place the cursor here and scan your boarding pass...",
    key="barcode_data",
    on_change=process_scan,
)
