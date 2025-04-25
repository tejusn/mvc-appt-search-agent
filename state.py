from google.cloud import storage
from datetime import datetime, timedelta
import logging
import json
import config # Import config to get cooldown hours and GCS settings

log = logging.getLogger(__name__)

# Initialize GCS client (this assumes the Cloud Function environment has credentials)
storage_client = None
if config.is_gcs_configured():
    try:
        storage_client = storage.Client()
    except Exception as e:
        log.error(f"Failed to initialize Google Cloud Storage client: {e}", exc_info=True)
        # The script might still run but state persistence will fail.

def _get_gcs_blob():
    """Helper function to get the GCS blob object for the state file."""
    if not storage_client or not config.GCS_BUCKET_NAME:
        log.error("GCS client or bucket name not configured. Cannot access state file.")
        return None
    try:
        bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
        blob = bucket.blob(config.GCS_STATE_FILE_PATH)
        return blob
    except Exception as e:
        log.error(f"Error accessing GCS bucket '{config.GCS_BUCKET_NAME}': {e}", exc_info=True)
        return None

def _read_state_from_gcs():
    """Reads the current notification state from the GCS file."""
    blob = _get_gcs_blob()
    if not blob:
        return {} # Return empty state if GCS access fails

    try:
        if blob.exists():
            state_json = blob.download_as_text()
            state_data = json.loads(state_json)
            # Convert stored timestamps (ISO strings) back to datetime objects
            # Also convert list keys back to tuples
            deserialized_state = {}
            for key_str, timestamp_str in state_data.items():
                 # Key is stored as string '["loc", "date", "time"]', convert back to tuple
                 try:
                     key_list = json.loads(key_str)
                     if isinstance(key_list, list) and len(key_list) == 3:
                         key_tuple = tuple(key_list)
                         deserialized_state[key_tuple] = datetime.fromisoformat(timestamp_str)
                     else:
                          log.warning(f"Skipping invalid key format in state file: {key_str}")
                 except (json.JSONDecodeError, TypeError) as key_err:
                      log.warning(f"Error deserializing state key '{key_str}': {key_err}")

            log.info(f"Successfully read state file from GCS. Tracking {len(deserialized_state)} notified appointments.")
            return deserialized_state
        else:
            log.info("State file not found in GCS. Starting with empty state.")
            return {}
    except json.JSONDecodeError as e:
        log.error(f"Error decoding JSON from state file '{config.GCS_STATE_FILE_PATH}': {e}. Starting with empty state.")
        return {}
    except Exception as e:
        log.error(f"Error reading state file from GCS: {e}", exc_info=True)
        return {} # Return empty state on error

def _write_state_to_gcs(state_data):
    """Writes the given notification state to the GCS file."""
    blob = _get_gcs_blob()
    if not blob:
        log.error("Cannot write state file to GCS.")
        return False

    try:
        # Convert datetime objects to ISO strings for JSON serialization
        # Convert tuple keys to JSON strings
        serialized_state = {}
        for key_tuple, timestamp_dt in state_data.items():
             key_str = json.dumps(list(key_tuple)) # Convert tuple key to JSON list string
             serialized_state[key_str] = timestamp_dt.isoformat()

        state_json = json.dumps(serialized_state, indent=2)
        blob.upload_from_string(state_json, content_type='application/json')
        log.info(f"Successfully wrote state file ({len(state_data)} entries) to GCS.")
        return True
    except Exception as e:
        log.error(f"Error writing state file to GCS: {e}", exc_info=True)
        return False

# --- Public State Functions ---

def has_been_notified_recently(appointment_key):
    """Checks if the given appointment key has been notified within the cooldown period by reading GCS state."""
    current_state = _read_state_from_gcs() # Read fresh state each time
    if appointment_key not in current_state:
        return False

    last_notified_time = current_state[appointment_key]
    cooldown_period = timedelta(hours=config.NOTIFICATION_COOLDOWN_HOURS)
    now = datetime.now()

    if (now - last_notified_time) < cooldown_period:
        log.debug(f"Appointment {appointment_key} was already notified at {last_notified_time}. Skipping due to cooldown.")
        return True
    else:
        # Cooldown expired, no need to explicitly remove here as we write the whole state later
        return False

def record_notification(appointment_key):
    """Records the current time for the appointment key and writes the updated state to GCS."""
    current_state = _read_state_from_gcs() # Read current state
    now = datetime.now()
    current_state[appointment_key] = now # Update or add the key
    log.debug(f"Recording notification for {appointment_key} at {now}.")
    _write_state_to_gcs(current_state) # Write the entire updated state back

def get_notified_count():
    """Returns the number of appointments currently tracked in the GCS state file."""
    # Reads the state file just to get the count
    current_state = _read_state_from_gcs()
    return len(current_state)