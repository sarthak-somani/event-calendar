document.addEventListener('DOMContentLoaded', function () {
    const CACHE_KEY = 'iitb_events_v1';
    const CACHE_TTL = 30 * 60 * 1000; // 30 minutes

    // Module-level events store so FullCalendar doesn't re-fetch on view changes
    let eventsStore = null;

    function escapeHtml(str) {
        if (str == null) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function readLocalCache() {
        try {
            const raw = localStorage.getItem(CACHE_KEY);
            if (!raw) return null;
            const { data, ts } = JSON.parse(raw);
            if (Date.now() - ts < CACHE_TTL) return data;
        } catch (_) {}
        return null;
    }

    function writeLocalCache(data) {
        try {
            localStorage.setItem(CACHE_KEY, JSON.stringify({ data, ts: Date.now() }));
        } catch (_) {}
    }

    const loadingEl = document.getElementById('calendar-loading');
    const errorEl   = document.getElementById('calendar-error');
    const listEl    = document.getElementById('event-list');
    const countEl   = document.getElementById('event-count');

    function setLoading(on) { loadingEl.hidden = !on; }
    function showError()    { errorEl.hidden = false; }

    function populateEventList(events) {
        const now = new Date();
        const upcoming = events
            .filter(e => new Date(e.start) >= now)
            .sort((a, b) => new Date(a.start) - new Date(b.start))
            .slice(0, 7);

        countEl.textContent = upcoming.length || '';
        countEl.hidden = upcoming.length === 0;

        if (upcoming.length === 0) {
            listEl.innerHTML = '<li class="no-events">No upcoming events.</li>';
            return;
        }

        listEl.innerHTML = upcoming.map(({ title, start }) => {
            const d = new Date(start);
            const dateStr = d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
            const timeStr = d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
            return `<li>
                <span class="event-title">${escapeHtml(title)}</span>
                <span class="event-date">${escapeHtml(dateStr)} &middot; ${escapeHtml(timeStr)}</span>
            </li>`;
        }).join('');
    }

    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        height: '100%',
        dayMaxEvents: true,
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listYear'
        },

        events: function (fetchInfo, successCallback, failureCallback) {
            // Return in-memory store immediately (no re-fetch on view navigation)
            if (eventsStore) {
                successCallback(eventsStore);
                return;
            }
            // Try 30-minute localStorage cache
            const cached = readLocalCache();
            if (cached) {
                eventsStore = cached;
                populateEventList(cached);
                successCallback(cached);
                return;
            }
            // Network fetch
            setLoading(true);
            fetch('events.json')
                .then(r => {
                    if (!r.ok) throw new Error(`HTTP ${r.status}`);
                    return r.json();
                })
                .then(data => {
                    eventsStore = data;
                    writeLocalCache(data);
                    populateEventList(data);
                    successCallback(data);
                })
                .catch(err => {
                    console.error('Failed to load events:', err);
                    showError();
                    failureCallback(err);
                })
                .finally(() => setLoading(false));
        },

        eventClick: function ({ event }) {
            const props = event.extendedProps;
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

            const dateStr = event.start.toLocaleDateString('en-US', {
                weekday: 'long', month: 'long', day: 'numeric', year: 'numeric'
            });
            const timeStr = event.start.toLocaleTimeString('en-US', {
                hour: '2-digit', minute: '2-digit', hour12: true
            });

            const row = (label, val, fallback = 'Not available') => {
                const content = escapeHtml(val) || `<em>${fallback}</em>`;
                return `<div class="popup-row">
                    <span class="popup-label">${label}</span>
                    <span class="popup-value">${content}</span>
                </div>`;
            };

            Swal.fire({
                titleText: event.title,
                html: `
                    <div class="popup-meta">
                        ${row('Date', dateStr, '')}
                        ${row('Time', timeStr, '')}
                        ${row('Venue', props.venue, 'Not specified')}
                    </div>
                    <div class="popup-divider"></div>
                    <div class="popup-body">
                        ${row('Description', props.description)}
                        ${row('Organizer', props.organisingBody, 'Not specified')}
                        ${row('Contact', props.contact)}
                    </div>`,
                confirmButtonText: 'Close',
                confirmButtonColor: '#4A90E2',
                customClass: { popup: 'event-popup' },
                background: prefersDark ? '#1e293b' : '#ffffff',
                color:      prefersDark ? '#e2e8f0' : '#1a1a2e',
            });
        }
    });

    calendar.render();
});
