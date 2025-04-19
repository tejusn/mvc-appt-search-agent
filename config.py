import os
from dotenv import load_dotenv
import logging

log = logging.getLogger(__name__)

# Load environment variables from .env file first
load_dotenv()

# --- Core Configuration ---
MVC_URL = "https://telegov.njportal.com/njmvc/AppointmentWizard/12" # REAL ID Appointments
# --- Location Configuration ---
# Set this flag to True to monitor all locations found in the data,
# or False to monitor only the specific locations listed in SPECIFIC_TARGET_LOCATIONS.
MONITOR_ALL_LOCATIONS = True # Default to specific list (original requirement)

# List of specific locations to target if MONITOR_ALL_LOCATIONS is False
# (Using names found in locationData, e.g., "Bayonne - Real ID")
SPECIFIC_TARGET_LOCATIONS = [
    "Bayonne - Real ID",
    "North Bergen - Real ID",
    "Newark - Real ID"
    # Add other specific locations here if needed, matching the names from ALL_AVAILABLE_LOCATIONS
]

# Full list of location names extracted from the locationData variable (as of 2025-04-19)
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
TARGET_EMAIL = "successtej@gmail.com" # Reverted to original PRD value
CHECK_INTERVAL_MINUTES = 60 # Defined in PRD

# --- Email Configuration (from .env file) ---
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


# --- State Management Configuration ---
NOTIFICATION_COOLDOWN_HOURS = 12 # Don't re-notify for the same slot within 12 hours

# --- Logging Setup (can be centralized here too) ---
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

def get_active_target_locations():
    """Returns the list of locations to monitor based on the MONITOR_ALL_LOCATIONS flag."""
    if MONITOR_ALL_LOCATIONS:
        log.info(f"Monitoring ALL {len(ALL_AVAILABLE_LOCATIONS)} available locations.")
        return ALL_AVAILABLE_LOCATIONS
    else:
        log.info(f"Monitoring SPECIFIC locations: {', '.join(SPECIFIC_TARGET_LOCATIONS)}")
        return SPECIFIC_TARGET_LOCATIONS