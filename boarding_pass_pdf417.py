import requests
import pandas as pd
from datetime import datetime

# API Configuration
API_KEY = '56e9c3-1bef36'  # Your Aviation Edge API key
IATA_CODE = 'SIN'  # Singapore Changi Airport
TYPE = 'departure'  # Fetch departures

# Fetch today's date in YYYY-MM-DD format
today = datetime.now().strftime('%Y-%m-%d')

# API endpoint
url = f'https://aviation-edge.com/v2/public/timetable'

# Parameters
params = {
    'key': API_KEY,
    'iataCode': IATA_CODE,
    'type': TYPE
}

# Make the request
try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # Filter flights departing today
    today_departures = []
    for flight in data:
        # Safely access 'scheduledTime' and skip flights with missing data
        dep_time = flight.get('departure', {}).get('scheduledTime')
        if dep_time and dep_time.startswith(today):  # Check if the time exists and matches today
            today_departures.append({
                'Flight Number': flight.get('flight', {}).get('iataNumber', 'N/A'),
                'Airline': flight.get('airline', {}).get('name', 'N/A'),
                'Destination': flight.get('arrival', {}).get('iataCode', 'N/A'),
                'Scheduled Time': dep_time,
                'Status': flight.get('status', 'N/A')
            })

    # Check if any departures were found
    if today_departures:
        # Create a DataFrame
        df = pd.DataFrame(today_departures)
        # Save to Excel
        file_name = f'SIN_Departures_{today}.xlsx'
        df.to_excel(file_name, index=False)
        print(f'Data successfully saved to {file_name}')
    else:
        print("No departures found for today.")

except requests.exceptions.RequestException as e:
    print(f'Error fetching departure details: {e}')
