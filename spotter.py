#!/usr/bin/env python
import requests
import json
import time
from datetime import datetime, timedelta

# --- Configuration ---
# List of tail numbers (or registration numbers) to watch for.
# Make sure to enter them exactly as they might appear in the data.
TAIL_NUMBERS_TO_WATCH = ["IDAHO99", "N2163J"]

# The URL to your SkyAware aircraft.json file.
AIRCRAFT_JSON_URL = ""

# Your Discord webhook URL. Leave as an empty string to disable.
DISCORD_WEBHOOK_URL = ""

# Your Home Assistant webhook URL. Leave as an empty string to disable.
HOME_ASSISTANT_WEBHOOK_URL = ""

# How often to check for new aircraft (in seconds).
CHECK_INTERVAL = 60

# How long to wait before notifying about the same aircraft again (in minutes).
NOTIFICATION_COOLDOWN = 90

# --- End of Configuration ---

# A dictionary to keep track of recently seen aircraft to avoid repeat notifications.
recently_seen_aircraft = {}

def send_discord_notification(aircraft):
    """Sends a notification to the configured Discord webhook."""
    if not DISCORD_WEBHOOK_URL:
        return

    flight_info = aircraft.get('flight', 'N/A').strip()
    altitude = aircraft.get('alt_baro', 'N/A')
    speed = aircraft.get('gs', 'N/A')
    squawk = aircraft.get('squawk', 'N/A')

    message = (
        f"🛩️ **Spotted Aircraft!**\n\n"
        f"**Tail Number:** {flight_info}\n"
        f"**Altitude:** {altitude} ft\n"
        f"**Ground Speed:** {speed} knots\n"
        f"**Squawk Code:** {squawk}\n"
        f"**Track on FlightAware:** [View Flight](https://flightaware.com/live/flight/{flight_info})"
    )

    payload = {
        "content": message
    }

    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
        print(f"Sent Discord notification for {flight_info}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Discord notification: {e}")

def send_home_assistant_notification(aircraft):
    """Triggers the configured Home Assistant webhook."""
    if not HOME_ASSISTANT_WEBHOOK_URL:
        return

    flight_info = aircraft.get('flight', 'N/A').strip()

    payload = {
        "tail_number": flight_info,
        "altitude": aircraft.get('alt_baro', 'N/A'),
        "speed": aircraft.get('gs', 'N/A'),
        "squawk": aircraft.get('squawk', 'N/A'),
        "latitude": aircraft.get('lat', 'N/A'),
        "longitude": aircraft.get('lon', 'N/A')
    }

    try:
        requests.post(HOME_ASSISTANT_WEBHOOK_URL, json=payload)
        print(f"Sent Home Assistant notification for {flight_info}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Home Assistant notification: {e}")

def main():
    """Main function to fetch data and check for specified aircraft."""
    while True:
        try:
            response = requests.get(AIRCRAFT_JSON_URL)
            response.raise_for_status()
            data = response.json()
            aircraft_list = data.get('aircraft', [])
            now = datetime.now()

            for aircraft in aircraft_list:
                flight_info = aircraft.get('flight', 'not_available').strip()

                if flight_info in TAIL_NUMBERS_TO_WATCH:
                    last_seen_time = recently_seen_aircraft.get(flight_info)

                    if not last_seen_time or (now - last_seen_time) > timedelta(minutes=NOTIFICATION_COOLDOWN):
                        print(f"Found watched aircraft: {flight_info}")
                        send_discord_notification(aircraft)
                        send_home_assistant_notification(aircraft)
                        recently_seen_aircraft[flight_info] = now
                    else:
                        print(f"Aircraft {flight_info} was already seen recently. Skipping notification.")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching aircraft data: {e}")
        except json.JSONDecodeError:
            print("Error decoding JSON from the aircraft data feed.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        print(f"Waiting for {CHECK_INTERVAL} seconds before the next check...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()