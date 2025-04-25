import functions_framework
import logging

# Import local modules
import config
import fetcher
import parser
import notifier
import state # Import state to potentially log its status if needed

# Configure logging (call the setup function from config)
# This should run when the Cloud Function instance initializes
config.setup_logging()
log = logging.getLogger(__name__)

# Define the Cloud Function entry point.
# This function will be triggered by Cloud Scheduler (HTTP) or Pub/Sub.
# The specific signature depends on the trigger type.
# Using HTTP trigger signature for this example: main(request)
# For Pub/Sub trigger, it would be: main(event, context)
@functions_framework.http
def check_mvc_appointments(request):
    """
    Cloud Function entry point triggered by HTTP request (e.g., from Cloud Scheduler).
    Fetches MVC appointments, processes them, and sends notifications.

    Args:
        request (flask.Request): The request object (unused in this simple case,
                                 but required by the decorator).

    Returns:
        str: A response message indicating success or failure.
        int: HTTP status code.
    """
    log.info("--- Cloud Function: check_mvc_appointments invoked ---")

    # Check if GCS is configured for state persistence
    if not config.is_gcs_configured():
        # Log error, but attempt to proceed without state persistence if possible
        # Depending on requirements, you might want to return an error here instead
        log.error("GCS not configured. Proceeding without state persistence (cooldown may not work correctly).")
        # return "GCS not configured", 500 # Option to fail hard

    try:
        # 1. Fetch HTML content
        html = fetcher.fetch_appointments_html()

        # 2. Process if HTML was fetched successfully
        if html:
            valid_appointments = parser.process_appointments(html)

            # 3. Notify if valid appointments were found
            if valid_appointments:
                notifier.send_notification(valid_appointments)
                response_msg = f"Processed and found {len(valid_appointments)} new appointments: {', '.join([str(appt) for appt in valid_appointments])}"

            else:
                log.info("No new, valid appointments found matching criteria.")
                response_msg = "No new, valid appointments found."
        else:
            log.warning("Skipping processing and notification due to fetch error.")
            response_msg = "Failed to fetch appointment data."
            # Consider returning an error status if fetching fails
            # return response_msg, 500

    except Exception as e:
        # Catch any unexpected errors during the execution
        log.error(f"An unexpected error occurred in the Cloud Function: {e}", exc_info=True)
        return "Internal Server Error", 500

    log.info(f"--- Cloud Function finished. Currently tracking {state.get_notified_count()} notified appointments (via GCS). ---")
    # Return a more detailed message including found appointments
    return response_msg, 200


# --- Cloud Run Job Entry Point ---
# This function is designed to be the main execution logic when run as a Cloud Run Job.
# It performs one complete check cycle.

def run_job_check():
    """
    Entry point suitable for a Cloud Run Job.
    Performs a single check for MVC appointments.
    Raises exceptions on critical errors to mark the job as failed.
    """
    log.info("--- Cloud Run Job: run_job_check invoked ---")

    # Check if GCS is configured for state persistence
    if not config.is_gcs_configured():
        # For a job, state persistence is usually critical for the cooldown logic.
        # Raise an exception to mark the job run as failed if GCS isn't set up.
        log.error("GCS_BUCKET_NAME environment variable is not set. Cannot proceed with job.")
        raise Exception("GCS_BUCKET_NAME environment variable is not set.")

    try:
        # 1. Fetch HTML content
        log.info("Job Step 1: Fetching HTML...")
        html = fetcher.fetch_appointments_html()

        # 2. Process if HTML was fetched successfully
        if html:
            log.info("Job Step 2: Processing HTML...")
            valid_appointments = parser.process_appointments(html)

            # 3. Notify if valid appointments were found
            if valid_appointments:
                log.info(f"Job Step 3: Found {len(valid_appointments)} appointments. Notifying...")
                notifier.send_notification(valid_appointments)
            else:
                log.info("Job Step 3: No new, valid appointments found matching criteria.")
        else:
            # If fetching failed, raise an exception to mark the job run as failed
            log.error("Job Step 1 Failed: Could not fetch appointment data.")
            raise Exception("Failed to fetch appointment data.")

    except Exception as e:
        # Catch any unexpected errors during the execution
        log.error(f"An unexpected error occurred in the Cloud Run Job: {e}", exc_info=True)
        # Re-raise the exception to ensure the Job run is marked as failed in Cloud Run
        raise e

    log.info(f"--- Cloud Run Job finished successfully. Currently tracking {state.get_notified_count()} notified appointments (via GCS). ---")


# --- Optional: Allow direct execution for local testing of the job logic ---
# Note: This part is NOT used by Cloud Run Jobs directly.
# Cloud Run Jobs execute the container's entrypoint/command based on the Dockerfile or Buildpack config.
# To test locally: Set RUN_MODE=job environment variable and run `python main.py`
import os # Import os here for the __main__ block
if __name__ == "__main__" and os.getenv("RUN_MODE", "http").lower() == "job":
    log.info("Running job check directly via __main__ (for local testing)...")
    # Ensure logging is set up if running directly (it might not be if config wasn't imported elsewhere)
    if not logging.getLogger().hasHandlers():
         config.setup_logging() # Setup logging if it hasn't been done
    try:
        run_job_check()
        log.info("Local job test finished successfully.")
    except Exception as e:
        log.error(f"Local job test failed: {e}", exc_info=True)
        # Exit with a non-zero code to indicate failure in a local test script context
        import sys
        sys.exit(1)