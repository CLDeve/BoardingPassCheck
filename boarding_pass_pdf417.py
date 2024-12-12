import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# API Configuration
API_KEY = '56e9c3-1bef36'  # Replace with your Aviation Edge API key
BASE_URL = 'https://aviation-edge.com/v2/public/timetable'

# Function to fetch departure flights
def fetch_departures(departure_airport="SIN"):
    """
    Fetch all departure flights from the API for a given airport.

    Args:
        departure_airport (str): IATA code for the departure airport.

    Returns:
        list: List of flights returned by the API.
    """
    params = {
        "key": API_KEY,
        "iataCode": departure_airport,
        "type": "departure"  # Fetch departure flights
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching flight data: {e}")
        return []

# Function to filter flights by date
def filter_flights_by_date(flights, target_date):
    """
    Filter flights by a specific date.

    Args:
        flights (list): List of flight data.
        target_date (str): Target date in YYYY-MM-DD format.

    Returns:
        list: List of flights matching the target date.
    """
    target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    filtered_flights = []
    for flight in flights:
        scheduled_time = flight.get("departure", {}).get("scheduledTime", None)
        if scheduled_time:
            flight_date = datetime.strptime(scheduled_time.split("T")[0], "%Y-%m-%d").date()
            if flight_date == target_date:
                filtered_flights.append({
                    "Flight Number": flight.get("flight", {}).get("iataNumber", "N/A"),
                    "Airline": flight.get("airline", {}).get("name", "N/A"),
                    "Destination": flight.get("arrival", {}).get("iataCode", "N/A"),
                    "Scheduled Departure Time": flight.get("departure", {}).get("scheduledTime", "N/A"),
                    "Status": flight.get("status", "N/A"),
                })
    return filtered_flights

# Streamlit Interface
st.title("Flight Departure Status Checker")

# Inputs
flight_number = st.text_input("Enter the flight number (e.g., EK353):")
departure_airport = st.text_input("Enter the departure airport IATA code (e.g., SIN):", value="SIN")
departure_date = st.date_input("Select the departure date:", min_value=datetime.now().date())

# Check and filter flights
if st.button("Check Flight Status"):
    if flight_number and departure_airport and departure_date:
        st.write(f"Checking flight {flight_number} departing from {departure_airport} on {departure_date}...")
        
        # Fetch all departures
        flights = fetch_departures(departure_airport)

        if flights:
            # Filter flights by date
            filtered_flights = filter_flights_by_date(flights, departure_date.strftime("%Y-%m-%d"))
            
            # Check if the specific flight exists
            flight_details = next((f for f in filtered_flights if f["Flight Number"] == flight_number), None)
            
            if flight_details:
                st.write("Flight Details:")
                st.json(flight_details)

                # Determine the flight's status
                status = flight_details["Status"].lower()
                if status == "active":
                    st.success("The flight has already departed.")
                elif status == "scheduled":
                    st.warning("The flight is scheduled but has not departed yet.")
                elif status == "cancelled":
                    st.error("The flight has been cancelled.")
                else:
                    st.info("The flight status is unknown.")
            else:
                st.error(f"No flight with number {flight_number} found for {departure_date}.")
        else:
            st.error("No departure data available for the specified airport.")
    else:
        st.error("Please provide the flight number, departure airport, and date.")

# Option to download all filtered flights
if st.button("Download All Flights on Selected Date"):
    if departure_airport and departure_date:
        st.write(f"Fetching all flights departing from {departure_airport} on {departure_date}...")
        
        # Fetch all departures
        flights = fetch_departures(departure_airport)

        if flights:
            # Filter flights by date
            filtered_flights = filter_flights_by_date(flights, departure_date.strftime("%Y-%m-%d"))
            
            if filtered_flights:
                # Convert to DataFrame
                flight_df = pd.DataFrame(filtered_flights)

                # Convert DataFrame to Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    flight_df.to_excel(writer, index=False, sheet_name='Flights')

                # Provide download button
                st.download_button(
                    label="Download Flights as Excel",
                    data=output.getvalue(),
                    file_name=f"{departure_airport}_flights_{departure_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error(f"No flights found departing from {departure_airport} on {departure_date}.")
        else:
            st.error("No departure data available for the specified airport.")

it should not save data
