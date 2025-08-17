# IITB Event Hub

The IITB Event Hub is a web application designed to track and display events happening at the Indian Institute of Technology Bombay (IITB). It automatically fetches event information from webmail, processes it, and presents it in an easy-to-use calendar and list format.

Access the calendar from here: [https://sarthak-somani.github.io/event-calendar/](https://sarthak-somani.github.io/event-calendar/)

## Features

- **Interactive Calendar**: Displays events on a full-sized monthly, weekly, or yearly calendar.
- **Upcoming Events List**: Shows a list of the next 7 upcoming events for a quick overview.
- **Detailed Event Information**: Clicking on an event reveals a pop-up with detailed information, including description, venue, organizer, and contact details.
- **Automated Event Extraction**: A Python script automatically reads emails from a designated inbox, uses a generative AI model to extract event details, and updates the event list.
- **Responsive Design**: The interface is optimized for both desktop and mobile viewing.

## How it Works

The application consists of two main components: a backend Python script for data processing and a frontend web interface for displaying the data.

1.  **Email Fetching**: The `process_events.py` script connects to the `imap.iitb.ac.in` IMAP server and monitors the `student-notices@iitb.ac.in` mailing list.
2.  **AI-Powered Extraction**: For each new email, the script uses the Google Gemini API to analyze the content and extract structured event data (title, date, description, etc.).
3.  **Data Storage**: The extracted event information is stored in the `events.json` file. The script keeps track of processed emails by storing their UIDs in `processed_uids.txt`.
4.  **Frontend Display**: The `index.html` page, styled with `style.css`, uses `script.js` to fetch the `events.json` data and dynamically render it using the [FullCalendar](https://fullcalendar.io/) library.

## Credits

This project was created by Sarthak Somani. I'm a student at the Department of Economics, IIT Bombay, and a Convener at the Web and Coding Club.
The creation of this automated calendar app stemmed from my own need to help keep track of the many events happening simultaneously on campus and the multitude of emails we are bombarded with each day.
