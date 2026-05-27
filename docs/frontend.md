# Frontend Documentation

The frontend consists of three files: `index.html`, `style.css`, and `script.js`. It is a fully static site served via GitHub Pages and requires no build step.

---

## `index.html`

Provides the page structure and pulls in all dependencies.

**Key elements:**

| Element | Purpose |
|---|---|
| `#calendar-container` | Wraps the FullCalendar instance. Uses `position: relative` so the loading overlay sits on top of it. |
| `#calendar-loading` | Spinner overlay. Shown only while `events.json` is being fetched from the network; hidden on cache hits. |
| `#calendar-error` | Error banner. Revealed if the network fetch fails. |
| `#calendar` | The FullCalendar mount point. |
| `#event-list-container` (`<aside>`) | Sidebar showing the next 7 upcoming events. Visible on all screen sizes including mobile (below the calendar on small screens). |
| `#event-count` | Badge in the sidebar heading showing the count of upcoming events. Hidden when zero. |
| `#event-list` | `<ul>` populated dynamically by `populateEventList()`. Items are keyboard-focusable and clickable. |

**External dependencies (CDN):**
- Google Fonts — Inter (weights 400, 500, 600, 700)
- FullCalendar 6.1.14
- SweetAlert2 11

---

## `style.css`

All styles are defined here using CSS custom properties (tokens), making theming and dark mode straightforward.

### Design tokens

Defined on `:root` with a `@media (prefers-color-scheme: dark)` override block:

| Token | Light | Dark |
|---|---|---|
| `--primary` | `#4A90E2` | `#60a5fa` |
| `--text` | `#1a1a2e` | `#e2e8f0` |
| `--text-muted` | `#5a6476` | `#94a3b8` |
| `--bg` | `#f0f4f8` | `#0f172a` |
| `--surface` | `#ffffff` | `#1e293b` |
| `--border` | `#dde3ec` | `#334155` |

### Notable sections

- **FullCalendar dark-mode overrides** — FullCalendar does not natively support CSS variables, so targeted selectors (`.fc-theme-standard td`, `.fc .fc-button-primary`, `.fc .fc-day-today`, etc.) are overridden under `@media (prefers-color-scheme: dark)`.
- **`.loading-overlay`** — `position: absolute; inset: 0` over the calendar container. Uses `[hidden]` override to ensure `display: none` takes effect even though the base rule sets `display: flex`.
- **`.error-banner`** — red-tinted banner with dark-mode variant.
- **`.event-count`** — pill badge on the sidebar heading; hidden via `[hidden]` attribute when count is zero.
- **`#event-list li`** — `cursor: pointer`; `:hover` background change; `:focus` outline for keyboard navigation.
- **`.event-popup`** — applied via SweetAlert2's `customClass` option; aligns popup content left and styles the label/value rows.
- **Mobile (`max-width: 768px`)** — `body` switches to `height: auto`; container becomes a column; calendar gets a fixed `70vh` height; sidebar stretches to full width.

---

## `script.js`

All logic runs inside a `DOMContentLoaded` listener to ensure the DOM is ready.

### Data flow

```
localStorage cache (≤30 min old)
        │ hit                  miss
        ▼                       ▼
  successCallback         fetch('events.json')
        │                       │
        └──────────┬────────────┘
                   ▼
          eventsStore (module-level)
          ├── populateEventList()  → sidebar
          └── FullCalendar         → calendar grid
```

### Key functions

#### `escapeHtml(str)`
Sanitises untrusted strings before inserting into HTML. Applied to all event fields rendered in the popup and sidebar.

#### `readLocalCache()` / `writeLocalCache(data)`
Reads/writes `iitb_events_v1` from `localStorage`. The cached object is `{ data, ts }` where `ts` is a Unix timestamp. Entries older than 30 minutes are treated as misses. Both functions are wrapped in `try/catch` to silently handle quota errors or disabled storage.

#### `showEventPopup(title, start, props)`
Shared by both the FullCalendar `eventClick` handler and the sidebar click handler. Renders a SweetAlert2 modal with date, time, venue, description, organiser, and contact. Detects `prefers-color-scheme` at call time to set `background` and `color` on the popup for dark mode.

#### `populateEventList(events)`
- Filters to events with `start ≥ now`, sorts ascending, takes first 7.
- Stores them in the module-level `upcomingEvents` array (used by the sidebar click handler).
- Renders `<li data-index="…" tabindex="0" role="button">` items for each.
- Updates the `#event-count` badge.

#### Sidebar click/keydown handlers
Delegated to `#event-list` (not each `<li>`). On click or `Enter`/`Space` keydown, finds the nearest `li[data-index]`, looks up the corresponding entry in `upcomingEvents`, and calls `showEventPopup`.

### FullCalendar configuration

| Option | Value | Notes |
|---|---|---|
| `initialView` | `dayGridMonth` | Default to month grid |
| `height` | `'100%'` | Fills the flex container |
| `dayMaxEvents` | `true` | Shows "+N more" link on busy days |
| `noEventsContent` | `'No events in this period.'` | Shown in list view when range is empty |
| `headerToolbar.right` | `dayGridMonth,timeGridWeek,listUpcoming` | Three view buttons |

#### Custom `listUpcoming` view
Replaces the built-in `listYear` view (which always started from Jan 1). Defined in the `views` option:
```javascript
listUpcoming: {
    type: 'list',
    duration: { months: 6 },
    buttonText: 'list'
}
```
Shows a 6-month rolling window. The `viewDidMount` callback fires every time the user switches *to* this view and calls `calendar.gotoDate(new Date())` (deferred via `setTimeout(0)` to run after the current render cycle), ensuring the list always opens at today's date regardless of which date was displayed in the previous view.
