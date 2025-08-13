# Backend Documentation

The backend of the IITB Event Hub is a Python script named `process_events.py`. Its primary role is to automate the collection of event data by reading emails from a specified inbox, extracting relevant information, and updating a JSON file that the frontend uses.

## `process_events.py`

This script is the engine of the application, ensuring that the event data is always up-to-date.

### Key Functionality:

1.  **IMAP Connection**:
    - The script connects to the IITB IMAP server (`imap.iitb.ac.in`) using the `imaplib` library.
    - It logs in using the credentials provided as environment variables.

2.  **Email Fetching and Filtering**:
    - It selects the `INBOX` and searches for emails addressed to `student-notices@iitb.ac.in`.
    - To avoid processing the same emails repeatedly, it keeps track of the UID of the last processed email in `processed_uids.txt`. It starts checking for new emails from the next UID.

3.  **Content Extraction**:
    - For each relevant email, the script parses the content to extract the subject and the plain text body.
    - It can handle multipart emails and decodes the content into a readable format.

4.  **AI-Powered Event Parsing**:
    - The core of the extraction logic lies in the `process_email_with_gemini` function.
    - This function sends the email's subject and body to the Google Gemini API with a carefully crafted prompt.
    - The prompt instructs the AI to determine if the email is an event announcement and, if so, to extract details like title, description, date, time, venue, etc., and return them in a structured JSON format.
    - If the email is not an event, the AI returns a JSON object indicating that, and the script skips it.

5.  **Data Storage**:
    - The extracted event data is formatted into a dictionary that matches the structure expected by FullCalendar.
    - This new event data is appended to the `events.json` file.
    - The script reads the existing events from `events.json` first to ensure that old events are not lost.

6.  **State Management**:
    - After processing a batch of emails, the script updates the `processed_uids.txt` file with the UID of the last email it checked. This ensures that the next run will pick up where the current one left off.

### Dependencies

The script relies on the following Python library:

-   `google-generativeai`: The official Python client for the Google Gemini API.

You can install this dependency using pip:
```bash
pip install -U google-generativeai
```

### Configuration

The script requires the following environment variables to be set before running:

-   `EMAIL_USERNAME`: The username for the email account to be monitored.
-   `EMAIL_PASSWORD`: The password for the email account.
-   `GEMINI_API_KEY`: Your API key for the Google Gemini service.

### Execution

To run the script, execute the following command in your terminal:
```bash
python process_events.py
```

It is recommended to run this script periodically to keep the event data fresh. This can be automated using a scheduler like `cron` on Linux/macOS or Task Scheduler on Windows. For example, to run the script every hour, you could set up a cron job like this:

```
0 * * * * /usr/bin/python /path/to/your/project/process_events.py
```
