import imaplib
import email
from email.header import decode_header
import json
import os
import ssl
import google.generativeai as genai
import time

# --- CONFIGURATION ---
IMAP_SERVER = 'imap.iitb.ac.in'
IMAP_PORT = 993
TARGET_RECIPIENT = "student-notices@iitb.ac.in"
MAX_EMAILS_TO_PROCESS = 25

# --- SECRETS (from environment variables) ---
EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# --- FILE PATHS ---
PROCESSED_UIDS_FILE = 'processed_uids.txt'
EVENTS_JSON_FILE = 'events.json'

# --- Configure the Gemini API ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

def clean_header_text(header_value):
    """Decodes email header text into a readable string."""
    if header_value is None:
        return ""
    decoded_parts = []
    for part, charset in decode_header(header_value):
        if isinstance(part, bytes):
            try:
                decoded_parts.append(part.decode(charset or 'utf-8', errors='replace'))
            except (UnicodeDecodeError, LookupError):
                # Fallback to latin-1 if the specified charset is unknown or fails
                decoded_parts.append(part.decode('latin-1', errors='replace'))
        else:
            decoded_parts.append(part)
    return "".join(decoded_parts)

def get_email_body(msg):
    """Extracts the plain text body from an email message."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Skip any part that is an attachment
            if "attachment" in content_disposition:
                continue
            
            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='replace')
                    # Once the plain text part is found, exit the loop
                    break
                except Exception:
                    body = "Error decoding body."
    else:
        # This is not a multipart message, so get the payload directly
        if msg.get_content_type() == "text/plain":
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or 'utf-8'
            body = payload.decode(charset, errors='replace')
    return body.strip()

def get_latest_processed_uid():
    """Reads the single latest UID from the state file."""
    if not os.path.exists(PROCESSED_UIDS_FILE):
        return 0
    try:
        with open(PROCESSED_UIDS_FILE, 'r') as f:
            content = f.read().strip()
            return int(content) if content else 0
    except (ValueError, FileNotFoundError):
        return 0

def process_email_with_gemini(subject, body):
    """Analyzes email content with Gemini to extract event details."""
    if not model:
        print("         > Gemini API key not configured. Skipping API call.")
        return None

    print("         > Calling Gemini API...")
    # The prompt sent to the Gemini API, including the email's subject and body
    prompt = f"""
    Analyze the following email content to determine if it is an event announcement.
    The email subject is: "{subject}"
    The email body is:
    ---
    {body}
    ---

    If it is an event, extract the details and return ONLY a single, minified JSON object with the following keys: "title", "description", "organisingBody", "startDate", "startTime", "endDate", "venue", "contact".
    - Use the "YYYY-MM-DD" format for dates.
    - Use the "HH:MM:SS" format for time.
    - Use null for any missing values.

    If it is NOT an event announcement, return ONLY the JSON object: {{"is_event": false}}.
    """
    try:
        # Add a retry mechanism for API calls with exponential backoff
        for attempt in range(3):
            try:
                response = model.generate_content(prompt)
                if not response.text:
                    print("         > Gemini returned an empty response. Retrying...")
                    time.sleep(2 ** attempt) 
                    continue

                cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
                data = json.loads(cleaned_text)

                if data.get("is_event") is False:
                    print("         > Gemini determined this is not an event.")
                    return None

                # Assuming end time is the same as start time if not provided
                end_time = data.get('endTime', data.get('startTime'))
                
                calendar_event = {
                    "title": data.get("title"),
                    "start": f"{data.get('startDate')}T{data.get('startTime')}",
                    "end": f"{data.get('endDate')}T{end_time}",
                    "extendedProps": {
                        "description": data.get("description"),
                        "venue": data.get("venue"),
                        "organisingBody": data.get("organisingBody"),
                        "contact": data.get("contact")
                    }
                }
                print(f"         > Gemini extracted event: {calendar_event['title']}")
                return calendar_event
            except Exception as e:
                print(f"         > Attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    raise
    except Exception as e:
        print(f"         > Error calling Gemini or parsing response: {e}")
        return None


def main():
    """Main function to connect to the IMAP server, fetch, and process emails."""
    print("--- Starting Event Fetcher Script ---")
    if not all([EMAIL_USERNAME, EMAIL_PASSWORD, GEMINI_API_KEY]):
        print("Error: Missing one or more required environment variables (EMAIL_USERNAME, EMAIL_PASSWORD, GEMINI_API_KEY).")
        return

    last_processed_uid = get_latest_processed_uid()
    print(f"Starting check from UID: {last_processed_uid + 1}")

    new_events = []
    current_uid_to_check = last_processed_uid + 1
    emails_processed_in_run = 0
    latest_uid_in_run = last_processed_uid

    try:
        # Use a more secure SSL context for the connection
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        print(f"Connecting to {IMAP_SERVER}...")
        with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT, ssl_context=context) as mail:
            mail.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            print("Login successful.")
            
            # Select the INBOX, readonly=False allows us to change flags (e.g., mark as unread)
            mail.select('INBOX', readonly=False) 

            while emails_processed_in_run < MAX_EMAILS_TO_PROCESS:
                print(f"\nChecking UID: {current_uid_to_check}...")

                # First, fetch the flags for the current UID to check its original read/unread status
                status_flags, flags_data = mail.fetch(str(current_uid_to_check), '(FLAGS)')
                if status_flags != 'OK' or not flags_data or not flags_data[0]:
                    print("No more emails found or could not fetch flags. Stopping check.")
                    break
                
                # Store the original unread status. The \Seen flag means the email has been read.
                is_originally_unread = b'\\Seen' not in flags_data[0]

                # Proceed to check the recipient for all emails, regardless of read/unread status
                status_to, to_data = mail.fetch(str(current_uid_to_check), '(BODY[HEADER.FIELDS (TO)])')

                if status_to == 'OK' and isinstance(to_data[0], tuple):
                    headers = email.message_from_bytes(to_data[0][1])
                    to_header = clean_header_text(headers['to'])

                    if TARGET_RECIPIENT in to_header:
                        print(f"   - Relevant recipient found. Fetching full body for UID {current_uid_to_check}...")

                        # Fetch the full email. This action marks it as read by the server.
                        status_full, msg_data_full = mail.fetch(str(current_uid_to_check), '(RFC822)')

                        if status_full == 'OK':
                            full_msg = email.message_from_bytes(msg_data_full[0][1])
                            subject = clean_header_text(full_msg['subject'])
                            body = get_email_body(full_msg)

                            if not body:
                                print("   - Skipping processing: No plain text body found.")
                            else:
                                event_data = process_email_with_gemini(subject, body)
                                if event_data:
                                    new_events.append(event_data)
                        
                        emails_processed_in_run += 1
                        # Pause to respect API rate limits
                        print("         > Pausing for 6 seconds...")
                        time.sleep(6)
                    else:
                        print(f"   - UID {current_uid_to_check} is not addressed to {TARGET_RECIPIENT}. Skipping processing.")
                
                # If the email was originally unread, re-tag it as unread after we are done with it.
                if is_originally_unread:
                    print(f"   - Re-marking UID {current_uid_to_check} as unread.")
                    mail.store(str(current_uid_to_check), '-FLAGS', '(\\Seen)')

                latest_uid_in_run = current_uid_to_check
                current_uid_to_check += 1

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if new_events:
            print(f"\nProcessed {len(new_events)} new events in this run.")
            all_events = []
            if os.path.exists(EVENTS_JSON_FILE):
                try:
                    with open(EVENTS_JSON_FILE, 'r', encoding='utf-8') as f:
                        all_events = json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse existing {EVENTS_JSON_FILE}. Starting fresh.")
            
            all_events.extend(new_events)
            with open(EVENTS_JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_events, f, indent=4)
            print(f"Successfully updated {EVENTS_JSON_FILE}.")

        if latest_uid_in_run > last_processed_uid:
            with open(PROCESSED_UIDS_FILE, 'w') as f:
                f.write(str(latest_uid_in_run))
            print(f"State file updated with latest processed UID: {latest_uid_in_run}")

        print("\n--- Script Finished ---")

if __name__ == '__main__':
    main()
