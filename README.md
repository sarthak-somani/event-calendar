# IITB Event Hub

The IITB Event Hub is a web application that tracks and displays events happening at IIT Bombay. It automatically monitors two student mailing lists, uses AI to extract structured event data from emails, and presents everything in an interactive calendar.

Access the live site: [https://sarthak-somani.github.io/event-calendar/](https://sarthak-somani.github.io/event-calendar/)

## Features

- **Interactive calendar** — month, week, and list views. The list view always opens at today's date.
- **Upcoming events sidebar** — the next 7 upcoming events shown with date and time. Clicking any item opens the full detail popup.
- **Detailed event popup** — click any event on the calendar or in the sidebar to see description, venue, organiser, and contact info.
- **Dark mode** — automatically follows the system's `prefers-color-scheme` setting.
- **Performance** — events are cached in `localStorage` for 30 minutes, so navigating between calendar views doesn't re-fetch the data file on every click.
- **Loading and error states** — a spinner is shown while data loads; a clear error banner appears if the fetch fails.
- **Automated event extraction** — a Python script runs hourly via GitHub Actions, reads emails from two IITB mailing lists, and uses Google Gemini to extract event details.
- **Responsive design** — works on desktop and mobile. The upcoming events list is visible on both.

## How it Works

The project has two components: a backend Python script that ingests data, and a static frontend that displays it.

1. **Email monitoring**: `process_events.py` connects to `imap.iitb.ac.in` and processes emails sent to `student-notices@iitb.ac.in` or `student-events@iitb.ac.in`.
2. **AI extraction**: Each relevant email is sent to the Google Gemini API, which extracts title, date, time, venue, description, organiser, and contact info as structured JSON.
3. **Data storage**: Extracted events are appended to `events.json`. Duplicates are detected by `(title, start)` key and skipped. The last-processed email UID is saved in `processed_uids.txt`.
4. **Automation**: GitHub Actions runs the script every hour and auto-commits any changes to `events.json` and `processed_uids.txt`.
5. **Frontend**: `index.html` / `script.js` fetch `events.json` on load, cache it in `localStorage`, and render it with [FullCalendar](https://fullcalendar.io/). Event details are displayed via [SweetAlert2](https://sweetalert2.github.io/) modals.

## Project Structure

```
├── index.html            # Main page
├── style.css             # All styles, including dark mode
├── script.js             # Frontend logic
├── process_events.py     # Backend email ingestion script
├── events.json           # Generated event data (do not edit manually)
├── processed_uids.txt    # Last-processed IMAP UID (state file)
├── requirements.txt      # Python dependencies
├── .github/
│   └── workflows/
│       └── main.yml      # Hourly GitHub Actions workflow
└── docs/
    ├── frontend.md
    ├── backend.md
    └── data_schema.md
```

## Credits

Created by Sarthak Somani, Department of Economics, IIT Bombay and Convener at the Web and Coding Club. Built to help keep track of the many simultaneous events on campus without drowning in emails.
