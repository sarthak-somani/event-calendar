# IITB Event Hub

The IITB Event Hub is a web application designed to track and display events happening at the Indian Institute of Technology Bombay (IITB). It automatically fetches event information from emails, processes it, and presents it in an easy-to-use calendar and list format.

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

## Setup and Usage

### Frontend

To view the event calendar, you can simply open the `index.html` file in a web browser. For the best experience, it is recommended to serve the files using a local web server.

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/event-calendar.git
    cd event-calendar
    ```

2.  **Start a simple web server**:
    If you have Python installed, you can run:
    ```bash
    # For Python 3
    python -m http.server
    ```
    Then, open your browser and navigate to `http://localhost:8000`.

### Backend

The backend script (`process_events.py`) is responsible for fetching and processing new events.

**Dependencies**:
The script requires the `google-generativeai` library. You can install it using pip:
```bash
pip install -U google-generativeai
```

**Configuration**:

1.  **Environment Variables**: The script requires the following environment variables to be set:
    - `EMAIL_USERNAME`: The username for the email account to be monitored.
    - `EMAIL_PASSWORD`: The password for the email account.
    - `GEMINI_API_KEY`: Your API key for the Google Gemini service.

    You can set these in your shell or by creating a `.env` file and using a library like `python-dotenv`.

2.  **Run the script**:
    Once the environment variables are configured, run the script from the command line:
    ```bash
    python process_events.py
    ```
    The script will connect to the email server, process new emails, and update the `events.json` file. It is recommended to run this script periodically (e.g., using a cron job) to keep the event data up-to-date.

## Contributing

Contributions are welcome! If you have suggestions for improvements or want to contribute to the project, please follow these steps:

1.  **Fork the repository**.
2.  **Create a new branch** for your feature or bug fix: `git checkout -b feature/your-feature-name`.
3.  **Make your changes** and commit them with descriptive messages.
4.  **Push your changes** to your forked repository.
5.  **Create a pull request** to the main repository, explaining the changes you have made.

Please ensure your code follows the existing style and that you update the documentation if necessary.
