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
                response_msg = f"Processed and found {len(valid_appointments)} new appointments."
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
    return response_msg, 200

# Note: The old mvc_tracker.py file with the schedule loop is no longer needed
# for Cloud Function deployment. You can keep it for local testing if desired,
# but ensure it doesn't interfere with the Cloud Function deployment process.
# Consider adding a check in mvc_tracker.py like:
# if __name__ == "__main__" and os.getenv("ENV_TYPE", "production").lower() == "local":
#    # Run local scheduler loop
# else:
#    # Maybe log a message indicating it's not meant for direct execution in deployed env
#    pass