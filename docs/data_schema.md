# Data Schema Documentation

The `events.json` file is the central data store for the IITB Event Hub application. It contains a JSON array of event objects, where each object represents a single event. This file is generated and updated by the `process_events.py` script and is consumed by the `script.js` on the frontend to display the events.

## `events.json` Structure

The file contains a single JSON array `[]`. Each element in the array is an object with the following structure, which is compatible with the [FullCalendar event object](https://fullcalendar.io/docs/event-object):

```json
[
  {
    "title": "Event Title",
    "start": "YYYY-MM-DDTHH:MM:SS",
    "end": "YYYY-MM-DDTHH:MM:SS",
    "extendedProps": {
      "description": "A detailed description of the event.",
      "venue": "Location of the event",
      "organisingBody": "The name of the organizer",
      "contact": "Contact information (email, phone, etc.)"
    }
  },
  ...
]
```

### Field Descriptions

-   **`title`** (string): The title of the event. This is displayed on the calendar.
-   **`start`** (string): The start date and time of the event in ISO 8601 format (`YYYY-MM-DDTHH:MM:SS`).
-   **`end`** (string): The end date and time of the event in ISO 8601 format. If the end time is not available, it may be the same as the start time.
-   **`extendedProps`** (object): An object containing additional custom properties for the event.
    -   **`description`** (string | null): A detailed description of the event.
    -   **`venue`** (string | null): The location or venue of the event.
    -   **`organisingBody`** (string | null): The name of the department, club, or group organizing the event.
    -   **`contact`** (string | null): Contact information for the event organizer, such as an email address, phone number, or website.

### Example Event Object

Here is an example of a single event object from the `events.json` file:

```json
{
    "title": "Central Library Orientation 2025",
    "start": "2025-08-04T10:00:00",
    "end": "2025-08-08T10:00:00",
    "extendedProps": {
        "description": "Detailed Library Orientation Program for new entrants and senior students interested in learning more about library resources and services.",
        "venue": "Conference Hall, 2nd Floor, Central Library",
        "organisingBody": "Central Library",
        "contact": "+91-22-2576-8936 / 8926"
    }
}
```
