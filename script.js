document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    const eventListEl = document.getElementById('event-list');

    // Function to populate the upcoming events list
    function populateEventList(events) {
        const now = new Date();
        
        // Filter for future events, sort them, and take the first 5
        const upcomingEvents = events
            .filter(event => new Date(event.start) >= now)
            .sort((a, b) => new Date(a.start) - new Date(b.start))
            .slice(0, 7); // Show the next 7 events

        if (upcomingEvents.length === 0) {
            eventListEl.innerHTML = '<li>No upcoming events found.</li>';
            return;
        }

        // Create list items for each upcoming event
        eventListEl.innerHTML = upcomingEvents.map(event => {
            const eventDate = new Date(event.start);
            const dateString = eventDate.toLocaleDateString('en-US', {
                weekday: 'long', month: 'long', day: 'numeric'
            });
            return `
                <li>
                    <span class="event-title">${event.title}</span>
                    <span class="event-date">${dateString}</span>
                </li>
            `;
        }).join('');
    }

    // Initialize the calendar
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listWeek'
        },
        
        // Use a function for events to fetch and process data
        events: function(fetchInfo, successCallback, failureCallback) {
            fetch('events.json')
                .then(response => response.json())
                .then(data => {
                    // Populate the side list with the fetched data
                    populateEventList(data);
                    // Load events into the calendar
                    successCallback(data);
                })
                .catch(error => {
                    console.error("Error fetching events:", error);
                    failureCallback(error);
                });
        },

        // Use SweetAlert2 for event clicks
        eventClick: function(info) {
            const props = info.event.extendedProps;
            Swal.fire({
                title: info.event.title,
                html: `
                    <div style="text-align: left; padding: 1em;">
                        <p><strong>Description:</strong> ${props.description || 'Not available.'}</p>
                        <p><strong>Venue:</strong> ${props.venue || 'Not specified.'}</p>
                        <p><strong>Organizer:</strong> ${props.organisingBody || 'Not specified.'}</p>
                        <p><strong>Contact:</strong> ${props.contact || 'Not available.'}</p>
                    </div>
                `,
                confirmButtonText: 'Close',
                confirmButtonColor: '#4A90E2'
            });
        }
    });

    // Render the calendar
    calendar.render();
});
