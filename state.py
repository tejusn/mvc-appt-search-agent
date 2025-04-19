from datetime import datetime, timedelta
import logging
import config # Import config to get cooldown hours

log = logging.getLogger(__name__)

# Simple in-memory store for notified appointments
# Structure: {(location, date, time): notification_timestamp}
_NOTIFIED_APPOINTMENTS = {}

def has_been_notified_recently(appointment_key):
    """Checks if the given appointment key has been notified within the cooldown period."""
    if appointment_key not in _NOTIFIED_APPOINTMENTS:
        return False

    last_notified_time = _NOTIFIED_APPOINTMENTS[appointment_key]
    cooldown_period = timedelta(hours=config.NOTIFICATION_COOLDOWN_HOURS)
    now = datetime.now()

    if (now - last_notified_time) < cooldown_period:
        log.debug(f"Appointment {appointment_key} was already notified at {last_notified_time}. Skipping due to cooldown.")
        return True
    else:
        # Cooldown expired, remove old entry (optional, keeps dict smaller)
        # del _NOTIFIED_APPOINTMENTS[appointment_key]
        return False

def record_notification(appointment_key):
    """Records the current time as the notification time for the given appointment key."""
    now = datetime.now()
    _NOTIFIED_APPOINTMENTS[appointment_key] = now
    log.debug(f"Recorded notification for {appointment_key} at {now}.")

def get_notified_count():
    """Returns the number of appointments currently being tracked in the notified state."""
    return len(_NOTIFIED_APPOINTMENTS)

# Optional: Function to prune very old entries if the script runs for a very long time
# def prune_old_entries(days_to_keep=7):
#     cutoff = datetime.now() - timedelta(days=days_to_keep)
#     keys_to_remove = [key for key, timestamp in _NOTIFIED_APPOINTMENTS.items() if timestamp < cutoff]
#     for key in keys_to_remove:
#         del _NOTIFIED_APPOINTMENTS[key]
#     if keys_to_remove:
#         log.info(f"Pruned {len(keys_to_remove)} old entries from notification state.")