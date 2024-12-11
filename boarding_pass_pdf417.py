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
            "Departure Date": flight_date.date(),
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
def validate_flight(flight_details, boarding_pass_details):
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
        scheduled_time = scheduled_time.split(".")[0]
        flight_datetime = datetime.strptime(scheduled_time.replace("T", " "), "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        validation_messages.append(f"Alert: Unable to parse Scheduled Departure Time. Error: {e}")
        return validation_messages

    # Check if flight date matches boarding pass date
    flight_date = flight_datetime.date()
    boarding_pass_date = boarding_pass_details.get("Departure Date")
    if flight_date != boarding_pass_date:
        validation_messages.append(
            f"Alert: Boarding pass date ({boarding_pass_date}) does not match flight date ({flight_date})!"
        )

    # Check if flight date is today
    current_date = datetime.now().date()
    if flight_date != current_date:
        validation_messages.append(
            f"Alert: Flight date is not today! (Flight Date: {flight_date}, Today's Date: {current_date})"
        )

    # Check if flight is within the next 24 hours
    current_time = datetime.now()
    time_difference = flight_datetime - current_time
    if time_difference.total_seconds() < 0:
        validation_messages.append(f"Alert: The flight has already departed! (Flight Time: {flight_datetime})")
    elif time_difference.total_seconds() > 86400:  # 24 hours in seconds
        validation_messages.append(
            f"Alert: Flight is not within the next 24 hours! (Flight Time: {flight_datetime}, Current Time: {current_time})"
        )

    return validation_messages

# Streamlit Interface
st.title("Boarding Pass Validator with Flight Checks")

# Initialize session state for the barcode field
if "barcode_data" not in st.session_state:
    st.session_state["barcode_data"] = ""

# Function to clear the barcode field
def clear_barcode():
    st.session_state["barcode_data"] = ""

# Scan boarding pass barcode
barcode_data = st.text_input(
    "Scan the barcode here:",
    placeholder="Place the cursor here and scan your boarding pass...",
    key="barcode_data"
)

# Inject custom CSS for conditional red background
def apply_red_background():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: red;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Fetch and Display Results
if st.button("Scan and Validate"):
    has_error = False
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

                # Validate flight details
                validation_results = validate_flight(flight_details, parsed_data)
                if validation_results:
                    has_error = True
                    for alert in validation_results:
                        st.error(alert)
                else:
                    st.success("Flight details are valid!")
            else:
                has_error = True
                st.warning("No departure details found for this flight.")
        else:
            has_error = True
            st.error(error)
    else:
        has_error = True
        st.error("Please scan a barcode first.")

    # Apply red background if there are errors
    if has_error:
        apply_red_background()

    # Clear the barcode input field
    clear_barcode()
