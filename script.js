document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    const eventListEl = document.getElementById('event-list');

    // Function to populate the upcoming events list (remains unchanged)
    function populateEventList(events) {
        const now = new Date();
        const upcomingEvents = events.filter(event => new Date(event.start) >= now).sort((a, b) => new Date(a.start) - new Date(b.start)).slice(0, 7);
        if (upcomingEvents.length === 0) {
            eventListEl.innerHTML = '<li>No upcoming events found.</li>';
            return;
        }
        eventListEl.innerHTML = upcomingEvents.map(event => {
            const eventDate = new Date(event.start);
            const dateString = eventDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
            return `<li><span class="event-title">${event.title}</span><span class="event-date">${dateString}</span></li>`;
        }).join('');
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        dayMaxEvents: true, // show a "+ more" link when there are too many events
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listYear'
        },
        
        events: function(fetchInfo, successCallback, failureCallback) {
            fetch('events.json')
                .then(response => response.json())
                .then(data => {
                    populateEventList(data);
                    successCallback(data);
                })
                .catch(error => {
                    console.error("Error fetching events:", error);
                    failureCallback(error);
                });
        },

        eventClick: function(info) {
            const props = info.event.extendedProps;
            const startDate = info.event.start;
            const dateString = startDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
            const timeString = startDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
            Swal.fire({
                title: info.event.title,
                html: `<div style="text-align: left; padding: 1em;"><p><strong>Date:</strong> ${dateString}</p><p><strong>Time:</strong> ${timeString}</p><p><strong>Venue:</strong> ${props.venue || 'Not specified.'}</p><hr style="border: 0; border-top: 1px solid #eee; margin: 1em 0;" /><p><strong>Description:</strong> ${props.description || 'Not available.'}</p><p><strong>Organizer:</strong> ${props.organisingBody || 'Not specified.'}</p><p><strong>Contact:</strong> ${props.contact || 'Not available.'}</p></div>`,
                confirmButtonText: 'Close',
                confirmButtonColor: '#4A90E2'
            });
        }
    });

    calendar.render();
});
