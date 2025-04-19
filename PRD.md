## Product Requirements Document: NJ MVC Appointment Tracker

**1. Introduction**

This document outlines the requirements for an agentic AI designed to track the availability of appointments at the New Jersey Motor Vehicle Commission (NJ MVC) website and notify the user when a suitable appointment becomes available.

**2. Goal**

The primary goal of this AI agent is to automatically monitor the NJ MVC website for REAL ID appointments at locations within a 30-minute general estimated driving distance from Jersey City and send an email notification to the user when such an appointment is found. The user has a preference for weekend appointments.

**3. Target User**

The target user is an individual seeking a REAL ID appointment at the NJ MVC who wants to be automatically notified when an appointment meeting their criteria becomes available, saving them the time and effort of manually checking the website.

**4. Scope**

**In Scope:**

*   Identify NJ MVC locations within a general estimated 30-minute driving radius of Jersey City.
*   Periodically check the NJ MVC website for the availability of REAL ID appointments.
*   Send an email notification to the user when a REAL ID appointment is found at a qualifying location.
*   The email notification will include the appointment location, date, time, and a link to the NJ MVC website.
*   The system will check for appointments every hour.
*   The system will prioritize weekend appointments if available.

**Out of Scope:**

*   Directly interacting with the NJ MVC website to browse and extract appointment data due to current technical limitations. This functionality will need to be implemented using tools like RooCode or Cline/Cursor that allow for web scraping or interaction.
*   Notifying the user if no appointments are currently available.
*   Considering real-time traffic conditions for determining driving time.
*   Allowing the user to specify preferred times of day for appointments (currently only weekend preference is noted).
*   Automatically booking the appointment.

**5. Functional Requirements**

*   **FR1: Location Identification:** The system shall be able to identify a list of NJ MVC locations that are estimated to be within a 30-minute drive from Jersey City. This can be achieved through a predefined list or by using a service to calculate driving distances based on location data.
*   **FR2: Appointment Checking:** The system shall periodically (every hour) attempt to access and check the NJ MVC appointment website (https://telegov.njportal.com/njmvc/AppointmentWizard/12) for available REAL ID appointments.
*   **FR3: Data Extraction (To be implemented via RooCode/Cline/Cursor):** The system shall be able to extract relevant information about available REAL ID appointments from the NJ MVC website. This includes the location, date, and time of the appointment.
*   **FR4: Location Filtering:** The system shall filter the found appointments to only include those at the locations identified in FR1.
*   **FR5: Weekend Preference:** If available, the system should prioritize and notify the user about appointments scheduled on weekends.
*   **FR6: Email Notification:** When a qualifying REAL ID appointment is found, the system shall send an email notification to successtej@gmail.com.
*   **FR7: Email Content:** The email notification shall include the following information:
    *   The name and address of the NJ MVC location.
    *   The date of the appointment.
    *   The time of the appointment.
    *   A direct link to the NJ MVC website (https://telegov.njportal.com/njmvc/AppointmentWizard/12).

**6. Non-Functional Requirements**

*   **NFR1: Reliability:** The system should reliably perform the hourly checks for appointment availability.
*   **NFR2: Efficiency:** The system should efficiently perform the checks and send notifications promptly once an appointment is found.
*   **NFR3: Maintainability:** The system should be designed in a way that allows for relatively easy updates and maintenance, especially if the structure of the NJ MVC website changes.

**7. Future Considerations (Optional)**

*   Allow the user to specify preferred days and times for appointments.
*   Integrate with a calendar to automatically add booked appointments.
*   Provide options for different notification frequencies.
*   Explore using more sophisticated methods for determining driving times, potentially integrating with real-time traffic data.