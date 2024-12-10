import requests
import pandas as pd
from datetime import datetime

# API Configuration
API_KEY = 'YOUR_API_KEY'  # Replace with your Aviation Edge API key
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
response = requests.get(url, params=params)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    # Filter flights departing today
    today_departures = [
        {
            'Flight Number': flight['flight']['iataNumber'],
            'Airline': flight['airline']['name'],
            'Destination': flight['arrival']['iataCode'],
            'Scheduled Time': flight['departure']['scheduledTime'],
            'Status': flight['status']
        }
        for flight in data
        if flight['departure']['scheduledTime'].startswith(today)
    ]
    # Create a DataFrame
    df = pd.DataFrame(today_departures)
    # Save to Excel
    file_name = f'SIN_Departures_{today}.xlsx'
    df.to_excel(file_name, index=False)
    print(f'Data successfully saved to {file_name}')
else:
    print(f'Failed to fetch data: {response.status_code} - {response.text}')
