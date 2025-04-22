import smtplib
from email.mime.text import MIMEText
import logging
from datetime import datetime

# Import local modules
import config
import state

log = logging.getLogger(__name__)

def send_notification(appointments):
    """
    Formats and sends an email notification for the given appointments.
    Updates the notification state after attempting to send.

    Args:
        appointments (list): A list of appointment dictionaries found by the parser.
    """
    if not appointments:
        log.debug("No appointments provided to send_notification.")
        return

    log.info(f"Preparing notification for {len(appointments)} appointments.")

    # Sort appointments, prioritizing weekends for display order
    appointments.sort(key=lambda x: not x.get('is_weekend', False))

    # --- Format Email Content ---
    subject = "NJ MVC REAL ID Appointment Alert!"
    body_lines = ["Found available NJ MVC REAL ID appointments:\n"]

    for appt in appointments:
        location = appt.get('location', 'N/A')
        date = appt.get('date', 'N/A')
        time = appt.get('time', 'N/A')
        # Highlight weekend appointments in the email body
        weekend_marker = " **(Weekend)**" if appt.get('is_weekend', False) else ""
        body_lines.append(f"--- Appointment ---")
        body_lines.append(f"Location: {location}")
        body_lines.append(f"Date: {date}{weekend_marker}")
        body_lines.append(f"Time: {time}")
        body_lines.append("") # Add a blank line between appointments

    body_lines.append(f"Check the NJ MVC website to book: {config.MVC_URL}")
    body = "\n".join(body_lines)

    # --- Attempt to Send Email ---
    email_configured = config.is_email_configured()

    if not email_configured:
        log.warning("Email configuration is incomplete. Logging notification content instead of sending.")
        log.info(f"--- Email Content (Not Sent) ---")
        log.info(f"To: {config.TARGET_EMAIL}")
        log.info(f"Subject: {subject}")
        log.info(f"Body:\n{body}")
        log.info(f"--- End Email Content ---")
    else:
        # Construct the email message
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = config.EMAIL_ADDRESS
        msg['To'] = config.TARGET_EMAIL

        try:
            log.info(f"Connecting to SMTP server {config.SMTP_SERVER}:{config.SMTP_PORT}...")
            # Use SMTP_SSL for implicit TLS (like port 465) or SMTP for STARTTLS (like port 587)
            # Adjust based on your provider's requirements. Defaulting to STARTTLS.
            # TODO: Consider making this configurable if needed.
            if config.SMTP_PORT == 465:
                 with smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT) as server:
                    log.info("Logging into SMTP server (SSL)...")
                    server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
                    log.info("Sending email...")
                    server.sendmail(config.EMAIL_ADDRESS, config.TARGET_EMAIL, msg.as_string())
                    log.info(f"Email notification sent successfully to {config.TARGET_EMAIL}.")
            else: # Assume STARTTLS for port 587 or others
                with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
                    server.starttls() # Secure the connection
                    log.info("Logging into SMTP server (STARTTLS)...")
                    log.info(config.EMAIL_ADDRESS + " " + config.EMAIL_PASSWORD + config )
                    server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
                    log.info("Sending email...")
                    server.sendmail(config.EMAIL_ADDRESS, config.TARGET_EMAIL, msg.as_string())
                    log.info(f"Email notification sent successfully to {config.TARGET_EMAIL}.")

        except smtplib.SMTPAuthenticationError:
            log.error("SMTP Authentication Error: Check EMAIL_ADDRESS and EMAIL_PASSWORD in .env file.")
            email_configured = False # Mark as failed to prevent state update below if strict
        except smtplib.SMTPServerDisconnected:
             log.error("SMTP Server disconnected unexpectedly. Check server/port/network.")
             email_configured = False
        except ConnectionRefusedError:
             log.error(f"Connection refused by SMTP server {config.SMTP_SERVER}:{config.SMTP_PORT}. Check server/port.")
             email_configured = False
        except Exception as e:
            log.error(f"An unexpected error occurred while sending email: {e}", exc_info=True)
            email_configured = False # Mark as failed

    # --- Update Notification State ---
    # Update state regardless of whether email *sending* succeeded,
    # as long as we *intended* to send (i.e., config was present initially).
    # This prevents spamming logs/console if email fails repeatedly.
    # If email failed due to config error, is_email_configured() handles the warning.
    log.info(f"Updating notification state for {len(appointments)} appointments.")
    for appt in appointments:
        if 'key' in appt:
            state.record_notification(appt['key'])
        else:
            log.warning(f"Appointment dictionary missing 'key': {appt}")