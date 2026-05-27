# Backend Documentation

The backend is a single Python script, `process_events.py`, that runs on a schedule via GitHub Actions. It connects to the IITB IMAP server, processes new emails, extracts event data using the Google Gemini API, and writes results to `events.json`.

---

## `process_events.py`

### Configuration constants

| Constant | Value | Description |
|---|---|---|
| `IMAP_SERVER` | `imap.iitb.ac.in` | IITB mail server |
| `IMAP_PORT` | `993` | IMAPS (SSL) port |
| `TARGET_RECIPIENTS` | `{student-notices@iitb.ac.in, student-events@iitb.ac.in}` | Emails addressed to either address are processed |
| `MAX_EMAILS_TO_PROCESS` | `25` | Max emails checked per run |
| `PROCESSED_UIDS_FILE` | `processed_uids.txt` | Stores the last-checked IMAP UID |
| `EVENTS_JSON_FILE` | `events.json` | Output event data file |

### Environment variables (required)

| Variable | Description |
|---|---|
| `EMAIL_USERNAME` | IMAP login username |
| `EMAIL_PASSWORD` | IMAP login password |
| `GEMINI_API_KEY` | Google Gemini API key |

These are stored as GitHub Actions secrets and injected at runtime. The Gemini client is initialised with `genai.Client(api_key=GEMINI_API_KEY)` — the key is passed explicitly because the library's default env var lookup uses `GOOGLE_API_KEY`, not `GEMINI_API_KEY`.

---

### Processing flow

```
read processed_uids.txt → last_uid
│
└── for uid = last_uid+1 to last_uid+MAX_EMAILS_TO_PROCESS:
    │
    ├── fetch FLAGS → record original read/unread state
    ├── fetch TO header
    │
    ├── skip if TO ∉ TARGET_RECIPIENTS
    │
    ├── fetch full RFC822 message
    ├── decode subject + plain-text body
    │
    ├── call Gemini API (up to 3 retries with exponential backoff)
    │   └── parse JSON response
    │       ├── is_event: false → skip
    │       ├── missing title or startDate → skip
    │       └── build calendar_event dict
    │
    ├── restore original unread state (re-mark as unread if it was unread)
    └── sleep 6 s (rate limiting)

finally:
    ├── deduplicate new_events against existing events.json by (title, start)
    ├── append unique events to events.json
    └── write new last_uid to processed_uids.txt
```

---

### Key functions

#### `clean_header_text(header_value)`
Decodes MIME-encoded email headers (e.g. `=?UTF-8?B?...?=`) into plain Unicode strings. Falls back to `latin-1` if the declared charset fails.

#### `get_email_body(msg)`
Walks a multipart email to find the first `text/plain` part that is not an attachment. Returns an empty string if none is found (the email is then skipped).

#### `get_latest_processed_uid()`
Reads the single integer in `processed_uids.txt`. Returns `0` if the file is missing or empty, causing the script to start from the beginning of the inbox.

#### `process_email_with_gemini(subject, body)`
Sends the email subject and body to `gemini-2.5-flash` with a prompt instructing it to return a minified JSON object. The function:
1. Retries up to 3 times with `2^attempt` second backoff on empty or error responses.
2. Strips Markdown code fences (` ```json ... ``` `) before parsing.
3. Returns `None` if the model responds `{"is_event": false}`.
4. Validates that `title` and `startDate` are present and non-null before building the event — missing dates previously produced invalid `"NoneT None"` ISO strings.
5. Defaults `startTime` to `00:00:00` and `endDate`/`endTime` to the start values if not provided.

#### Deduplication (in `main()`)
Before writing to `events.json`, the script builds a set of `(title, start)` tuples from the existing events and filters `new_events` against it. This prevents duplicate entries if the same UID range is processed more than once due to a state-file reset or crash recovery.

---

## `requirements.txt`

```
google-genai>=1.0.0
```

Install with:
```bash
pip install -r requirements.txt
```

The `google-genai` package replaces the older `google-generativeai` package. The new client API is `genai.Client(api_key=...)` / `client.models.generate_content(model=..., contents=...)`.

---

## GitHub Actions workflow (`.github/workflows/main.yml`)

The workflow runs on a cron schedule (`30 * * * *` — every hour at the 30-minute mark) and can also be triggered manually.

**Steps:**
1. Checkout the repository.
2. Set up Python 3.11.
3. **Restore pip cache** (`actions/cache@v4`, keyed on `requirements.txt` hash) — avoids reinstalling packages on every run.
4. Install dependencies from `requirements.txt`.
5. Run `process_events.py` with secrets injected as environment variables.
6. Auto-commit any changes to `events.json` and `processed_uids.txt` using `stefanzweifel/git-auto-commit-action@v5`.
