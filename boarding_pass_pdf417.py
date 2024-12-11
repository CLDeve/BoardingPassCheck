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
                    "Status": flight.get("status", "N/A"),
                    "Departure Airport": departure_airport,
                }
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching departure details: {e}")
        return None

# Function to validate flight details
def validate_flight(flight_details, barcode_date):
    validation_messages = []

    # Check if departure is from SIN
    if flight_details.get("Departure Airport") != "SIN":
        validation_messages.append("Alert: Departure is not from SIN!")

    # Get and validate the scheduled departure time
    scheduled_time = flight_details.get("Scheduled Departure Time", "")
    if not scheduled_time:
        validation_messages.append("Alert: Scheduled Departure Time is missing!")
        return validation_messages

    try:
        # Remove fractional seconds if present
        scheduled_time = scheduled_time.split(".")[0]  # Remove ".000" or similar
        flight_datetime = datetime.strptime(scheduled_time.replace("T", " "), "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        validation_messages.append(f"Alert: Unable to parse Scheduled Departure Time. Error: {e}")
        return validation_messages

    # Compare the departure date from the barcode with the API date
    api_date = flight_datetime.date()
    if barcode_date != api_date:
        validation_messages.append(
            f"Alert: Mismatch between boarding pass date ({barcode_date}) and flight API date ({api_date})."
        )

    # Check if flight is within the next 24 hours
    current_time = datetime.now()
    time_difference = flight_datetime - current_time
    if time_difference.total_seconds() < -3600:  # Allow flights within 1 hour in the past
        validation_messages.append(
            f"Alert: Flight has already taken off! (Flight Time: {flight_datetime}, Current Time: {current_time})"
        )
    elif time_difference.total_seconds() > 86400:  # More than 24 hours in the future
        validation_messages.append(
            f"Alert: Flight is not within the next 24 hours! (Flight Time: {flight_datetime}, Current Time: {current_time})"
        )

    return validation_messages

# Streamlit Interface
st.title("Boarding Pass Validator with Flight Checks")

# Scan boarding pass barcode
barcode_data = st.text_input(
    "Scan the barcode here:",
    placeholder="Place the cursor here and scan your boarding pass...",
)

# Fetch and Display Results
if st.button("Scan and Validate"):
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

                # Validate flight details with the parsed departure date
                validation_results = validate_flight(flight_details, parsed_data["Departure Date"])
                if validation_results:
                    for alert in validation_results:
                        st.error(alert)
                else:
                    st.success("Flight details are valid!")
            else:
                st.warning("No departure details found for this flight.")
        else:
            st.error(error)
    else:
        st.error("Please scan a barcode first.")
