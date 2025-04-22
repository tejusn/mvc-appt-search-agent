# NJ MVC Appointment Tracker

## Goal

This project contains a Python application designed to automatically monitor the New Jersey Motor Vehicle Commission (NJ MVC) website for available REAL ID appointments at specified locations. When a suitable appointment is found, it sends an email notification.

The primary goal is to save users the time and effort of manually checking the website repeatedly.

## Features

*   Periodically fetches appointment availability data from the NJ MVC website (specifically for REAL ID).
*   Parses the website data to extract location, date, and time of available appointments.
*   Filters appointments based on a configurable list of target locations (either specific locations or all available ones).
*   Sends an email notification to a configured address when a new, qualifying appointment is found.
*   Prioritizes weekend appointments in the notification email.
*   Implements a cooldown period to avoid sending repeated notifications for the same appointment slot within a configured timeframe.
*   Designed to be deployable as a Google Cloud Function for automated, serverless execution.
*   Includes basic logging for monitoring and debugging.

## Project Structure

```
.
├── .env.example          # Example environment variables file
├── .env                  # Local environment variables (Create this from example, DO NOT COMMIT)
├── .gitignore            # Specifies intentionally untracked files that Git should ignore
├── config.py             # Handles configuration (URLs, locations, email settings, GCS)
├── fetcher.py            # Module for fetching HTML content from MVC site
├── main.py               # Entry point for Google Cloud Function deployment
├── mvc_tracker.py        # Original main script (can be used for local testing/scheduling)
├── notifier.py           # Module for formatting and sending email notifications
├── parser.py             # Module for parsing HTML/JSON and extracting appointment data
├── PLAN.md               # Detailed technical plan (generated during development)
├── PRD.md                # Product Requirements Document
├── requirements.txt      # Python dependencies
└── state.py              # Module for managing notification state (in-memory or GCS)
```

## Local Setup & Running

1.  **Prerequisites:**
    *   Python 3.9+ installed.
    *   `pip` (Python package installer).

2.  **Clone Repository:** (If applicable)
    ```bash
    git clone <repository_url>
    cd mvc-appt-search-agent
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    *   Copy `.env.example` to a new file named `.env`.
    *   Edit `.env` and fill in your email credentials:
        *   `SMTP_SERVER`: Your email provider's SMTP server (e.g., `smtp.gmail.com`).
        *   `SMTP_PORT`: The SMTP port (e.g., `587` for TLS/STARTTLS, `465` for SSL).
        *   `EMAIL_ADDRESS`: The email address the notification will be sent *from*.
        *   `EMAIL_PASSWORD`: The password for the sending email address. **Use an App Password** if using Gmail/Google Workspace.
    *   *(Optional)* Set `ENV_TYPE=local` in `.env` to ensure local settings are loaded correctly.

5.  **Configure `config.py` (Optional):**
    *   `TARGET_EMAIL`: Change the recipient email address if needed (default: `successtej@gmail.com`).
    *   `MONITOR_ALL_LOCATIONS`: Set to `True` to check all locations, `False` (default) to check only those in `SPECIFIC_TARGET_LOCATIONS`.
    *   `SPECIFIC_TARGET_LOCATIONS`: Modify this list if `MONITOR_ALL_LOCATIONS` is `False`.
    *   `NOTIFICATION_COOLDOWN_HOURS`: Adjust the cooldown period if desired.

6.  **Run Locally:**
    *   You can run the original script which uses an internal scheduler:
        ```bash
        python mvc_tracker.py
        ```
    *   This will run an initial check and then check every hour defined in `config.py`. Press `Ctrl+C` to stop. Note that the state (cooldown) is in-memory and will be lost when the script stops.

### Local HTTP Testing (Simulating Cloud Function)

You can test the HTTP-triggered function (`main.py`) locally before deploying using the `functions-framework`:

1.  **Ensure Dependencies:** `pip install -r requirements.txt`
2.  **Configure `.env`:**
    *   Make sure `ENV_TYPE=local` is set in your `.env` file.
    *   Fill in email credentials (`SMTP_SERVER`, `SMTP_PORT`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD`).
    *   *(Optional but Recommended)* Add `GCS_BUCKET_NAME=YOUR_GCS_BUCKET_NAME` to `.env` to test GCS state persistence. You may need to authenticate locally using `gcloud auth application-default login`.
3.  **Start Server:** In your terminal (in the project directory):
    ```bash
    functions-framework --target=check_mvc_appointments --source=main.py --port=8080 --debug
    ```
4.  **Trigger Function:** In a *new* terminal window:
    ```bash
    curl http://localhost:8080/
    ```
    (Or open `http://localhost:8080/` in a browser).
5.  **Check Logs:** Observe the output in the first terminal window where `functions-framework` is running.
6.  **Stop Server:** Press `Ctrl+C` in the first terminal window when done.

## Google Cloud Function Deployment

This application is designed to be deployed as a Google Cloud Function, triggered periodically by Cloud Scheduler. This provides a serverless, automated way to run the checker.

**Key Steps (See detailed instructions provided previously):**

1.  **Prerequisites:** Google Cloud SDK (`gcloud`) installed and configured, necessary APIs enabled (Cloud Functions, Cloud Build, Secret Manager, Cloud Scheduler).
2.  **Secret Manager:** Store sensitive email credentials securely. Grant the Cloud Function's service account access.
3.  **GCS Bucket:** Create a bucket to store the persistent notification state file (`mvc_tracker_state.json`).
4.  **Deploy Function:** Use `gcloud functions deploy` command, specifying:
    *   Runtime (`python311`, etc.)
    *   Entry point (`check_mvc_appointments` in `main.py`)
    *   HTTP Trigger
    *   Environment variables (e.g., `GCS_BUCKET_NAME`, `TARGET_EMAIL`, `MONITOR_ALL_LOCATIONS`).
    *   Secret Manager integration (`--set-secrets`) for email credentials.
5.  **Cloud Scheduler:** Create a job to trigger the function's HTTP URL on your desired schedule (e.g., hourly).

**Required Environment Variables for Cloud Deployment:**

*   `GCS_BUCKET_NAME`: Name of the GCS bucket for state storage.
*   `TARGET_EMAIL`: Recipient email address.
*   *(Optional)* `SMTP_PORT`: If not 587.
*   *(Optional)* `NOTIFICATION_COOLDOWN_HOURS`: Defaults to 12 if not set.
*   *(Optional)* `MONITOR_ALL_LOCATIONS`: Defaults to `"False"` if not set.
*   *(Optional)* `SPECIFIC_TARGET_LOCATIONS_JSON`: JSON array string if overriding specific locations.

**Required Secrets for Cloud Deployment (via `--set-secrets`):**

*   `EMAIL_PASSWORD`: Linked to the `MVC_EMAIL_PASSWORD` secret.
*   `EMAIL_ADDRESS`: Linked to the `MVC_EMAIL_ADDRESS` secret.
*   `SMTP_SERVER`: Linked to the `MVC_SMTP_SERVER` secret.

## Notes

*   The website parsing logic in `parser.py` relies on specific JSON data embedded in the MVC site's HTML. If the website structure changes significantly, the parser may need updates.
*   Ensure the email account used for sending allows SMTP access and check for any security measures (like App Passwords for Gmail) that might be required.