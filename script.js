document.addEventListener('DOMContentLoaded', function () {
    const CACHE_KEY = 'iitb_events_v1';
    const CACHE_TTL = 30 * 60 * 1000; // 30 minutes

    let eventsStore    = null; // in-memory; avoids re-fetching on view navigation
    let upcomingEvents = [];   // kept in sync so sidebar click handler can reference them

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

    function showEventPopup(title, start, props) {
        props = props || {};
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const dateStr = start.toLocaleDateString('en-US', {
            weekday: 'long', month: 'long', day: 'numeric', year: 'numeric'
        });
        const timeStr = start.toLocaleTimeString('en-US', {
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
            titleText: title,
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

    function populateEventList(events) {
        const now = new Date();
        upcomingEvents = events
            .filter(e => new Date(e.start) >= now)
            .sort((a, b) => new Date(a.start) - new Date(b.start))
            .slice(0, 7);

        countEl.textContent = upcomingEvents.length || '';
        countEl.hidden = upcomingEvents.length === 0;

        if (upcomingEvents.length === 0) {
            listEl.innerHTML = '<li class="no-events">No upcoming events.</li>';
            return;
        }

        listEl.innerHTML = upcomingEvents.map(({ title, start }, i) => {
            const d = new Date(start);
            const dateStr = d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
            const timeStr = d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
            return `<li data-index="${i}" tabindex="0" role="button" aria-label="${escapeHtml(title)}">
                <span class="event-title">${escapeHtml(title)}</span>
                <span class="event-date">${escapeHtml(dateStr)} &middot; ${escapeHtml(timeStr)}</span>
            </li>`;
        }).join('');
    }

    function handleListItemActivation(e) {
        const li = e.target.closest('li[data-index]');
        if (!li) return;
        const ev = upcomingEvents[parseInt(li.dataset.index, 10)];
        if (ev) showEventPopup(ev.title, new Date(ev.start), ev.extendedProps || {});
    }

    listEl.addEventListener('click', handleListItemActivation);
    listEl.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleListItemActivation(e);
        }
    });

    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        height: '100%',
        dayMaxEvents: true,
        noEventsContent: 'No events in this period.',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listUpcoming'
        },
        views: {
            listUpcoming: {
                type: 'list',
                duration: { months: 6 },
                buttonText: 'list'
            }
        },

        // Always jump to today when entering the list view, regardless of
        // which date was previously shown in another view.
        viewDidMount: function (info) {
            if (info.view.type === 'listUpcoming') {
                setTimeout(() => calendar.gotoDate(new Date()), 0);
            }
        },

        events: function (fetchInfo, successCallback, failureCallback) {
            if (eventsStore) {
                successCallback(eventsStore);
                return;
            }
            const cached = readLocalCache();
            if (cached) {
                eventsStore = cached;
                populateEventList(cached);
                successCallback(cached);
                return;
            }
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
            showEventPopup(event.title, event.start, event.extendedProps);
        }
    });

    calendar.render();
});
