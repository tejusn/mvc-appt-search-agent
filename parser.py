import json
import re
import logging
from datetime import datetime
from bs4 import BeautifulSoup

# Import local modules
import config
import state

log = logging.getLogger(__name__)

def process_appointments(html_content):
    """
    Parses the HTML to find embedded JSON data, extracts appointments,
    filters by location, and checks against the notification cooldown.

    Args:
        html_content (str): The HTML content of the appointment page.

    Returns:
        list: A list of dictionaries, where each dictionary represents a new,
              valid appointment to notify about. Returns an empty list if
              no valid appointments are found or an error occurs.
    """
    log.info("Processing fetched content to find embedded JSON...")
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    newly_found_appointments = []
    now = datetime.now() # For cooldown check

    location_data = None
    time_data = None

    # Find the script tag containing the location data
    script_tags = soup.find_all('script')
    data_script_content = None
    for script in script_tags:
        # Look for the specific pattern indicating the start of the locationData array
        if script.string and 'var locationData = [{' in script.string:
            data_script_content = script.string
            break

    if not data_script_content:
        log.error("Could not find the script tag containing 'var locationData'. Website structure may have changed.")
        return []

    # Extract JSON data using regex
    try:
        # Regex to find 'var locationData = [...] ;' - Keep this as it seems correct based on HTML
        location_match = re.search(r'var locationData = (\[.*?\]);', data_script_content, re.DOTALL | re.MULTILINE)
        # Regex to find 'var timeData = [...]' followed by whitespace and 'var locationModel'
        # This avoids relying on a potentially missing semicolon after timeData
        time_match = re.search(r'var timeData = (\[.*?\])\s*var locationModel', data_script_content, re.DOTALL | re.MULTILINE)

        if location_match:
            location_json_str = location_match.group(1)
            # Attempt to load the JSON
            location_data = json.loads(location_json_str)
            log.info(f"Successfully parsed locationData JSON ({len(location_data)} locations).")
        else:
            log.error("Could not extract locationData JSON array from script using regex.")
            return [] # Cannot proceed without location data

        if time_match:
            time_json_str = time_match.group(1)
            # Attempt to load the JSON
            time_data = json.loads(time_json_str)
            log.info(f"Successfully parsed timeData JSON ({len(time_data)} entries).")
        else:
            log.warning("Could not extract timeData JSON array from script using regex. Availability info might be missing.")
            time_data = [] # Ensure it's an empty list if not found

    except json.JSONDecodeError as e:
        log.error(f"Error decoding JSON from script tag: {e}")
        # Log snippets for debugging
        if location_match: log.debug(f"Location JSON snippet (error source): {location_match.group(1)[:200]}...")
        if time_match: log.debug(f"Time JSON snippet (error source): {time_match.group(1)[:200]}...")
        return []
    except Exception as e:
        log.error(f"Unexpected error during JSON extraction: {e}", exc_info=True)
        return []

    # Create a lookup dictionary for time data by LocationId for efficient access
    time_lookup = {item['LocationId']: item['FirstOpenSlot'] for item in time_data if 'LocationId' in item and 'FirstOpenSlot' in item}

    # Process the location data entries
    for location_info in location_data:
        try:
            location_id = location_info.get('Id')
            location_name = location_info.get('Name')

            # Basic validation of the entry
            if not location_id or not location_name:
                log.warning(f"Skipping location entry due to missing Id or Name: {location_info}")
                continue

            # --- Location Normalization & Filtering ---
            # Normalize by removing extra whitespace
            normalized_location_name = ' '.join(location_name.split())
            matched_target_location = None
            # Get the currently active list of target locations from config
            active_targets = config.get_active_target_locations()
            # Check against the active target locations
            for target_loc in active_targets:
                # Case-insensitive check if the target name is part of the site's name
                if target_loc.lower() in normalized_location_name.lower():
                    matched_target_location = target_loc # Use the canonical name from the active list
                    break

            # If this location is not in our target list, skip it
            if not matched_target_location:
                # log.debug(f"Skipping location '{normalized_location_name}' (ID: {location_id}), not in target list.")
                continue

            # --- Check Availability using the time_lookup dictionary ---
            availability_str = time_lookup.get(location_id)
            # If no time entry or explicitly says "No Appointments", skip
            if not availability_str or "No Appointments Available" in availability_str:
                # log.info(f"No appointments currently listed for {matched_target_location} (ID: {location_id}).")
                continue

            # --- Extract Date/Time from Availability String ---
            # Example string format: "1 Appointments Available <br/> Next Available: 07/16/2025 01:55 PM"
            # Use regex to capture the date (MM/DD/YYYY) and time (HH:MM AM/PM)
            dt_match = re.search(r'Next Available: (\d{1,2}/\d{1,2}/\d{4}) (\d{1,2}:\d{2} [AP]M)', availability_str)
            if not dt_match:
                log.warning(f"Could not parse date/time from availability string for {matched_target_location}: '{availability_str}'")
                continue # Skip if format doesn't match expected pattern

            date_str = dt_match.group(1)
            time_str = dt_match.group(2)

            # --- Date/Time Parsing & Weekend Check ---
            try:
                # Parse the extracted date and time string into a datetime object
                appointment_dt = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %I:%M %p")
                # Check if the day of the week is Saturday (5) or Sunday (6)
                is_weekend = appointment_dt.weekday() >= 5
            except ValueError as e:
                log.warning(f"Error parsing extracted date/time '{date_str} {time_str}' for {matched_target_location}: {e}. Skipping.")
                continue # Skip if parsing fails

            # --- Cooldown Check using state module ---
            # Create a unique key for this specific appointment slot
            appointment_key = (matched_target_location, date_str, time_str)
            # Check if we've notified about this exact slot recently
            if state.has_been_notified_recently(appointment_key):
                continue # Skip if notified within cooldown period

            # --- Add Valid Appointment to List ---
            log.info(f"Found valid, new appointment: {appointment_key}, Weekend: {is_weekend}")
            newly_found_appointments.append({
                "location": matched_target_location,
                "date": date_str,
                "time": time_str,
                "is_weekend": is_weekend,
                "key": appointment_key
                # Optionally add address details from location_info if needed for the email notification
                # "address": f"{location_info.get('Street1', '')}, {location_info.get('City', '')}, {location_info.get('State', '')} {location_info.get('Zip', '')}"
            })

        except Exception as e:
            # Catch any unexpected errors during the processing of a single location entry
            log.error(f"Error processing location entry: {location_info}. Error: {e}", exc_info=True)

    log.info(f"HTML processing complete. Found {len(newly_found_appointments)} new, valid appointments matching criteria.")
    return newly_found_appointments