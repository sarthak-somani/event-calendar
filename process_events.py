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
MAX_EMAILS_PER_RUN = 25

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
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

def clean_header_text(header_value):
    if header_value is None: return ""
    decoded_parts = []
    for part, charset in decode_header(header_value):
        if isinstance(part, bytes):
            try: decoded_parts.append(part.decode(charset or 'utf-8', errors='replace'))
            except (UnicodeDecodeError, LookupError): decoded_parts.append(part.decode('latin-1', errors='replace'))
        else: decoded_parts.append(part)
    return "".join(decoded_parts)

def get_email_body(msg):
    body = ""
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
    if not os.path.exists(PROCESSED_UIDS_FILE): return 0
    with open(PROCESSED_UIDS_FILE, 'r') as f:
        uids = [int(line.strip()) for line in f if line.strip().isdigit()]
        return max(uids) if uids else 0

def process_email_with_gemini(subject, body):
    if not model:
        print("      > Gemini API key not configured. Skipping API call.")
        return None
    print("      > Calling Gemini API...")
    prompt = f"""
    Analyze the following email content to determine if it is an event announcement. Today's date is August 3, 2025. Use this for context.
    Email Subject: "{subject}"
    Email Body: "{body}"
    If it is an event, extract details and return a single, minified JSON object with keys: "title", "description", "organisingBody", "startDate", "startTime", "endDate", "venue", "contact". Use "YYYY-MM-DD" for dates and "HH:MM:SS" for time. Use null for missing values.
    If it is NOT an event, return {{"is_event": false}}.
    """
    try:
        response = model.generate_content(prompt)
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
    print("--- Starting Event Fetcher Script (Optimized) ---")
    if not all([EMAIL_USERNAME, EMAIL_PASSWORD, GEMINI_API_KEY]):
        print("Error: Missing credentials."); return

    latest_uid = get_latest_processed_uid()
    print(f"Latest processed UID is: {latest_uid}")
    
    all_processed_uids = {str(latest_uid)} if latest_uid > 0 else set()
    new_events = []
    
    try:
        context = ssl.create_default_context(); context.set_ciphers('DEFAULT@SECLEVEL=1')
        print(f"Connecting to {IMAP_SERVER}...")
        with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT, ssl_context=context) as mail:
            mail.login(EMAIL_USERNAME, EMAIL_PASSWORD); print("Login successful.")
            mail.select('INBOX')
            
            base_search = f'(OR (TO "{TARGET_RECIPIENT}") (SUBJECT "[Student-notices]"))'
            search_criteria = f'(UID {latest_uid+1}:*) {base_search}' if latest_uid > 0 else base_search

            print(f"Searching with optimized criteria: {search_criteria}")
            status, email_ids_raw = mail.search(None, search_criteria)
            
            if status != 'OK': print("Error searching for emails."); return
            uids_to_fetch = email_ids_raw[0].split()
            if not uids_to_fetch: print("No new emails to process. All up to date!"); return
            
            ### THIS IS THE FIX ###
            # Process the NEWEST (last) emails from the list of new emails
            uids_to_process_now = uids_to_fetch[-MAX_EMAILS_PER_RUN:]
            print(f"Found {len(uids_to_fetch)} new emails. Processing the latest {len(uids_to_process_now)} for this run.")

            for uid in uids_to_process_now:
                print(f"\nProcessing new email with UID: {uid.decode()}...")
                status, msg_data = mail.fetch(uid, '(RFC822)')
                if status == 'OK' and isinstance(msg_data[0], tuple):
                    msg = email.message_from_bytes(msg_data[0][1])
                    subject, body = clean_header_text(msg['subject']), get_email_body(msg)
                    if not body: print("   - Skipping email: No plain text body found."); continue
                    print(f"   - Subject: {subject}")
                    event_data = process_email_with_gemini(subject, body)
                    if event_data:
                        new_events.append(event_data)
                        all_processed_uids.add(uid.decode())
                    print("      > Pausing for 4 seconds...")
                    time.sleep(4)
                else: print(f"   - Skipping UID {uid.decode()}: Not valid email data.")
    except Exception as e:
        print(f"\nAn error occurred: {e}"); import traceback; traceback.print_exc()
    finally:
        if new_events:
            print(f"\nProcessed {len(new_events)} new events.")
            all_events = []
            if os.path.exists(EVENTS_JSON_FILE):
                with open(EVENTS_JSON_FILE, 'r', encoding='utf-8') as f: all_events = json.load(f)
            all_events.extend(new_events)
            with open(EVENTS_JSON_FILE, 'w', encoding='utf-8') as f: json.dump(all_events, f, indent=4)
            print(f"Successfully updated {EVENTS_JSON_FILE}.")
            with open(PROCESSED_UIDS_FILE, 'w') as f:
                # Read all UIDs again to ensure we don't lose any
                if os.path.exists(PROCESSED_UIDS_FILE):
                    with open(PROCESSED_UIDS_FILE, 'r') as old_f:
                        for old_uid in old_f:
                            all_processed_uids.add(old_uid.strip())
                for uid_val in sorted([int(u) for u in all_processed_uids if u.isdigit()]): f.write(f"{uid_val}\n")
            print(f"Successfully updated {PROCESSED_UIDS_FILE}.")
        print("\n--- Script Finished ---")

if __name__ == '__main__':
    main()
