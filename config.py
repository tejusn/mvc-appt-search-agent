import os
import json # Import the json module
from dotenv import load_dotenv
import logging

log = logging.getLogger(__name__)

# Load .env file for LOCAL DEVELOPMENT ONLY.
# In Cloud Functions, environment variables are set directly.
if os.getenv("ENV_TYPE", "production").lower() == "local":
    load_dotenv()
    log.info("Loaded .env file for local development.")

# --- Core Configuration ---
MVC_URL = os.getenv("MVC_URL", "https://telegov.njportal.com/njmvc/AppointmentWizard/12") # REAL ID Appointments
# --- Location Configuration ---
# Set this flag to True to monitor all locations found in the data,
# or False to monitor only the specific locations listed in SPECIFIC_TARGET_LOCATIONS.
MONITOR_ALL_LOCATIONS = True # Default to specific list (original requirement)

# List of specific locations to target if MONITOR_ALL_LOCATIONS is False
# Can be overridden by environment variable SPECIFIC_TARGET_LOCATIONS_JSON (a JSON string array)
# Example: '["Bayonne - Real ID", "Newark - Real ID"]'
SPECIFIC_TARGET_LOCATIONS_JSON = os.getenv("SPECIFIC_TARGET_LOCATIONS_JSON")

CHECK_INTERVAL_MINUTES = 60

# Default specific locations if environment variable is not set or invalid
_DEFAULT_SPECIFIC_TARGET_LOCATIONS = [
    "Bayonne - Real ID",
    "North Bergen - Real ID",
    "Newark - Real ID"
]

SPECIFIC_TARGET_LOCATIONS = _DEFAULT_SPECIFIC_TARGET_LOCATIONS
# Now check if the environment variable was set and try to parse it
if SPECIFIC_TARGET_LOCATIONS_JSON:
    try:
        parsed_locations = json.loads(SPECIFIC_TARGET_LOCATIONS_JSON)
        if isinstance(parsed_locations, list) and all(isinstance(loc, str) for loc in parsed_locations):
            SPECIFIC_TARGET_LOCATIONS = parsed_locations
            log.info(f"Loaded specific target locations from environment variable: {SPECIFIC_TARGET_LOCATIONS}")
        else:
            log.warning("SPECIFIC_TARGET_LOCATIONS_JSON environment variable is not a valid JSON list of strings. Using default.")
    except json.JSONDecodeError:
        log.warning("Could not parse SPECIFIC_TARGET_LOCATIONS_JSON environment variable. Using default.")


# Full list of location names extracted from the locationData variable (as of 2025-04-19)
# This could potentially be fetched dynamically or updated periodically, but hardcoding for now.
ALL_AVAILABLE_LOCATIONS = [
    'Bakers Basin - Real ID', 'Bayonne - Real ID', 'Camden - Real ID',
    'Cardiff  - Real ID', 'Delanco - Real ID', 'Eatontown - Real ID',
    'Edison - Real ID', 'Elizabeth - Real ID', 'Flemington - Real ID',
    'Freehold - Real ID', 'Lodi - Real ID', 'Manahawkin - Real ID',
    'Newark - Real ID', 'Newton - Real ID', 'North Bergen - Real ID',
    'Oakland - Real ID', 'Paterson - Real ID', 'Rahway - Real ID',
    'Randolph - Real ID', 'Rio Grande - Real ID', 'Runnemede - Real ID',
    'Salem - Real ID', 'South Plainfield - Real ID', 'Toms River - Real ID',
    'Vineland - Real ID', 'Washington - Real ID', 'Wayne - Real ID',
    'West Deptford - Real ID'
]

# --- Other Configuration ---
TARGET_EMAIL = os.getenv("TARGET_EMAIL", "divtejus@gmail.com") # Email recipient
# CHECK_INTERVAL_MINUTES is no longer needed as triggering is handled by Cloud Scheduler

# --- Email Configuration (Environment Variables) ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT_STR = os.getenv("SMTP_PORT", "587") # Default to 587 if not set
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Validate and convert SMTP_PORT
SMTP_PORT = None
try:
    SMTP_PORT = int(SMTP_PORT_STR)
except (ValueError, TypeError):
    log.warning(f"Invalid SMTP_PORT value '{SMTP_PORT_STR}' in .env file. Using default 587 if possible, otherwise email may fail.")
    # Attempt default if original was invalid
    if SMTP_PORT_STR != "587":
        try:
            SMTP_PORT = int("587")
        except ValueError: # Should not happen with "587"
             log.error("Could not even parse default SMTP port 587.")


# --- State Management Configuration (Environment Variables) ---
NOTIFICATION_COOLDOWN_HOURS_STR = os.getenv("NOTIFICATION_COOLDOWN_HOURS", "12")
try:
    NOTIFICATION_COOLDOWN_HOURS = int(NOTIFICATION_COOLDOWN_HOURS_STR)
except (ValueError, TypeError):
    log.warning(f"Invalid NOTIFICATION_COOLDOWN_HOURS value '{NOTIFICATION_COOLDOWN_HOURS_STR}'. Using default 12.")
    NOTIFICATION_COOLDOWN_HOURS = 12

# GCS Configuration for State Persistence
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME") # Required for state persistence
GCS_STATE_FILE_PATH = os.getenv("GCS_STATE_FILE_PATH", "mvc_tracker_state.json") # Default path within bucket

# --- Logging Setup ---
def setup_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    log.info("Logging configured.")

# --- Helper Functions ---
def is_email_configured():
    """Checks if all necessary email variables are set."""
    configured = all([SMTP_SERVER, SMTP_PORT is not None, EMAIL_ADDRESS, EMAIL_PASSWORD, TARGET_EMAIL])
    if not configured:
        log.warning("Email configuration is incomplete. Check SMTP_SERVER, SMTP_PORT, EMAIL_ADDRESS, EMAIL_PASSWORD in .env file and TARGET_EMAIL in config.py.")
    return configured

def is_gcs_configured():
    """Checks if GCS bucket name is provided."""
    if not GCS_BUCKET_NAME:
        log.error("GCS_BUCKET_NAME environment variable is not set. State persistence will fail.")
        return False
    return True

def get_active_target_locations():
    """Returns the list of locations to monitor based on the MONITOR_ALL_LOCATIONS flag."""
    if MONITOR_ALL_LOCATIONS:
        log.info(f"Monitoring ALL {len(ALL_AVAILABLE_LOCATIONS)} available locations.")
        return ALL_AVAILABLE_LOCATIONS
    else:
        # Ensure SPECIFIC_TARGET_LOCATIONS is used after potential loading from env var
        log.info(f"Monitoring SPECIFIC locations: {', '.join(SPECIFIC_TARGET_LOCATIONS)}")
        return SPECIFIC_TARGET_LOCATIONS