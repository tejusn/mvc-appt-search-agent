import schedule
import time
import logging
import os # Import the os module

# Import local modules
import config

# Import local modules
import config
import fetcher
import parser
import notifier
import state # Import state to potentially log its status if needed

# Configure logging (call the setup function from config)
config.setup_logging()
log = logging.getLogger(__name__) # Get logger for this module

def job():
    """The main job executed by the scheduler."""
    log.info("--- Running scheduled check ---")
    try:
        # 1. Fetch HTML content
        html = fetcher.fetch_appointments_html()

        # 2. Process if HTML was fetched successfully
        if html:
            valid_appointments = parser.process_appointments(html)

            # 3. Notify if valid appointments were found
            if valid_appointments:
                notifier.send_notification(valid_appointments)
            else:
                log.info("No new, valid appointments found matching criteria.")
        else:
            log.warning("Skipping processing and notification due to fetch error.")

    except Exception as e:
        # Catch any unexpected errors in the job sequence
        log.error(f"An unexpected error occurred in the main job loop: {e}", exc_info=True)

    log.info(f"--- Check finished. Currently tracking {state.get_notified_count()} notified appointments. Waiting for next run... ---")


# --- Main Execution (for Local Scheduled Testing) ---
if __name__ == "__main__":
    # Only run the scheduler loop if explicitly in local mode
    if os.getenv("ENV_TYPE", "production").lower() == "local":
        log.info("--- NJ MVC Appointment Tracker Starting (Local Scheduler Mode) ---")
        log.info(f"Checking URL: {config.MVC_URL}")
        # Get the active list of locations being monitored
    active_locations = config.get_active_target_locations()
    log.info(f"Monitoring Locations ({'ALL' if config.MONITOR_ALL_LOCATIONS else 'SPECIFIC'}): {', '.join(active_locations)}")
    log.info(f"Notification Email: {config.TARGET_EMAIL}")
    log.info(f"Check Interval: {config.CHECK_INTERVAL_MINUTES} minutes")
    log.info(f"Notification Cooldown: {config.NOTIFICATION_COOLDOWN_HOURS} hours")
    email_configured = config.is_email_configured() # Check and log email config status
    log.info(f"Email sending configured: {'Yes' if email_configured else 'No'}")

    # Run the job once immediately at startup
    log.info("Running initial check...")
    job()

    # Schedule the job to run periodically
    schedule.every(config.CHECK_INTERVAL_MINUTES).minutes.do(job)
    log.info(f"Scheduled to run every {config.CHECK_INTERVAL_MINUTES} minutes.")

    # Main loop to run the scheduler
    while True:
        try:
            schedule.run_pending()
            # Sleep for a short duration to avoid busy-waiting
            # Check schedule every 60 seconds
            time.sleep(60)
        except KeyboardInterrupt:
            log.info("Shutdown signal received. Exiting scheduler loop.")
            break
        except Exception as e:
            log.error(f"An error occurred in the scheduler loop: {e}", exc_info=True)
            # Optional: Add a longer sleep here to prevent rapid error loops
            time.sleep(300) # Sleep for 5 minutes after an error in the loop

        log.info("--- NJ MVC Appointment Tracker (Local Scheduler Mode) Stopped ---")
    else:
        print("--------------------------------------------------------------------------")
        print("INFO: mvc_tracker.py is intended for local scheduled testing.")
        print("      Set ENV_TYPE=local environment variable to run the scheduler.")
        print("      For Cloud Function deployment, use main.py as the entry point.")
        print("--------------------------------------------------------------------------")