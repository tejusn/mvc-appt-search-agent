import requests
import logging
import config # Import config to get MVC_URL

log = logging.getLogger(__name__)

def fetch_appointments_html():
    """
    Fetches the appointment page HTML content from the configured URL.

    Returns:
        str: The HTML content as text if successful, None otherwise.
    """
    url = config.MVC_URL
    log.info(f"Fetching appointments HTML from {url}...")
    try:
        # Consider adding headers to mimic a real browser if needed
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        log.info(f"Successfully fetched HTML content ({len(response.text)} bytes).")
        return response.text
    except requests.exceptions.Timeout:
        log.error(f"Timeout error while fetching appointments from {url}.")
        return None
    except requests.exceptions.RequestException as e:
        log.error(f"Error fetching appointments from {url}: {e}")
        return None
    except Exception as e:
        log.error(f"An unexpected error occurred during fetching: {e}", exc_info=True)
        return None