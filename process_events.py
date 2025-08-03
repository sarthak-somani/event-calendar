import imaplib
import email
from email.header import decode_header
import json
import os
import socket
import ssl
import google.generativeai as genai
import time

# --- CONFIGURATION ---
IMAP_SERVER = 'imap.iitb.ac.in'
IMAP_PORT = 993
TARGET_RECIPIENT = "student-notices.iitb.ac.in"
MAX_EMAILS_TO_PROCESS = 25 # Process up to 25 emails in one run

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
    if header_value is None: return ""
    decoded_parts = [];
    for part, charset in decode_header(header_value):
        if isinstance(part, bytes):
            try: decoded_parts.append(part.decode(charset or 'utf-8', errors='replace'))
            except (UnicodeDecodeError, LookupError): decoded_parts.append(part.decode('latin-1', errors='replace'))
        else: decoded_parts.append(part)
    return "".join(decoded_parts)

def get_email_body(msg):
    body = "";
    if msg.is_multipart():
        for part in msg.walk():
            content_type, content_disposition = part.get_content_type(), str(part.get("Content-Disposition"))
            if "attachment" in content_disposition: continue
            if content_type == "text/plain":
                try:
                    payload, charset = part.get_payload(decode=True), part.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='replace'); break
                except Exception: body = "Error decoding body."
    else:
        if msg.get_content_type() == "text/plain":
            payload, charset = msg.get_payload(decode=True), msg.get_content_charset() or 'utf-8'
            body = payload.decode(charset, errors='replace')
    return body.strip()

def get_latest_processed_uid():
    """Reads the single latest UID from the state file."""
    if not os.path.exists(PROCESSED_UIDS_FILE): return 0
    try:
        with open(PROCESSED_UIDS_FILE, 'r') as f:
            content = f.read().strip()
            return int(content) if content else 0
    except (ValueError, FileNotFoundError):
        return 0

def process_email_with_gemini(subject, body):
    if not model:
        print("      > Gemini API key not configured. Skipping API call."); return None
    print("      > Calling Gemini API...")
    prompt = f"""
    Analyze the following email content to determine if it is an event announcement.
    If it is an event, extract details and return a single, minified JSON object with keys: "title", "description", "organisingBody", "startDate", "startTime", "endDate", "venue", "contact". Use "YYYY-MM-DD" for dates and "HH:MM:SS" for time. Use null for missing values.
    If it is NOT an event, return {{"is_event": false}}.
    """
    try:
        response = model.generate_content(prompt)
        if not response.text:
            print("      > Gemini returned an empty response. Skipping."); return None
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned_text)
        if data.get("is_event") is False:
            print("      > Gemini determined this is not an event."); return None
        calendar_event = {
            "title": data.get("title"), "start": f"{data.get('startDate')}T{data.get('startTime')}",
            "end": f"{data.get('endDate')}T{data.get('startTime')}",
            "extendedProps": {"description": data.get("description"), "venue": data.get("venue"),
                              "organisingBody": data.get("organisingBody"), "contact": data.get("contact")}
        }
        print(f"      > Gemini extracted event: {calendar_event['title']}")
        return calendar_event
    except Exception as e:
        print(f"      > Error calling Gemini or parsing response: {e}"); return None

def main():
    print("--- Starting Event Fetcher Script (Sequential Check) ---")
    if not all([EMAIL_USERNAME, EMAIL_PASSWORD, GEMINI_API_KEY]):
        print("Error: Missing credentials."); return

    last_processed_uid = get_latest_processed_uid()
    print(f"Starting check from UID: {last_processed_uid + 1}")
    
    new_events = []
    current_uid_to_check = last_processed_uid + 1
    emails_processed_in_run = 0
    latest_uid_in_run = last_processed_uid
    
    try:
        context = ssl.create_default_context(); context.set_ciphers('DEFAULT@SECLEVEL=1')
        print(f"Connecting to {IMAP_SERVER}...")
        with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT, ssl_context=context) as mail:
            mail.login(EMAIL_USERNAME, EMAIL_PASSWORD); print("Login successful.")
            mail.select('INBOX')
            
            # Loop sequentially until we run out of emails or hit our batch limit
            while emails_processed_in_run < MAX_EMAILS_TO_PROCESS:
                print(f"\nChecking UID: {current_uid_to_check}...")
                # Fetch headers for the current UID
                status, msg_data = mail.fetch(str(current_uid_to_check), '(BODY[HEADER.FIELDS (TO)])')
                
                # If fetch fails, we've likely run out of emails
                if status != 'OK' or not msg_data[0]:
                    print("No more emails found. Stopping check.")
                    break
                
                # Check if the 'TO' header is relevant
                if isinstance(msg_data[0], tuple):
                    headers = email.message_from_bytes(msg_data[0][1])
                    to_header = clean_header_text(headers['to'])
                    
                    if TARGET_RECIPIENT in to_header:
                        print(f"   - Relevant recipient found. Fetching full body for UID {current_uid_to_check}...")
                        # Fetch the full email body
                        status_full, msg_data_full = mail.fetch(str(current_uid_to_check), '(RFC822)')
                        if status_full == 'OK':
                            full_msg = email.message_from_bytes(msg_data_full[0][1])
                            subject, body = clean_header_text(full_msg['subject']), get_email_body(full_msg)
                            if not body:
                                print("   - Skipping: No plain text body found.")
                            else:
                                event_data = process_email_with_gemini(subject, body)
                                if event_data:
                                    new_events.append(event_data)
                        
                        emails_processed_in_run += 1
                        print("      > Pausing for 6 seconds...")
                        time.sleep(6)
                    else:
                        print(f"   - UID {current_uid_to_check} is not to student-notices. Skipping.")
                
                latest_uid_in_run = current_uid_to_check
                current_uid_to_check += 1

    except Exception as e:
        print(f"\nAn error occurred during the loop: {e}")
    finally:
        # Save results and update the single latest UID
        if new_events:
            print(f"\nProcessed {len(new_events)} new events in this run.")
            all_events = []
            if os.path.exists(EVENTS_JSON_FILE):
                with open(EVENTS_JSON_FILE, 'r', encoding='utf-8') as f: all_events = json.load(f)
            all_events.extend(new_events)
            with open(EVENTS_JSON_FILE, 'w', encoding='utf-8') as f: json.dump(all_events, f, indent=4)
            print(f"Successfully updated {EVENTS_JSON_FILE}.")
        
        if latest_uid_in_run > last_processed_uid:
            with open(PROCESSED_UIDS_FILE, 'w') as f:
                f.write(str(latest_uid_in_run))
            print(f"State file updated with latest processed UID: {latest_uid_in_run}")
        
        print("\n--- Script Finished ---")

if __name__ == '__main__':
    main()
