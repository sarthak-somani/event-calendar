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

    // ### CHANGE 1: Add logic to determine the best view for the screen size ###
    const isMobile = window.innerWidth < 768;
    const initialCalendarView = isMobile ? 'listYear' : 'dayGridMonth';

    const calendar = new FullCalendar.Calendar(calendarEl, {
        // Use the view we just determined
        initialView: initialCalendarView,

        dayMaxEvents: true, // show a "+ more" link when there are too many events
        
        // ### CHANGE 2: Add this line to make the calendar fill the available height ###
        expandRows: true,

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
                    
                    // This part auto-scrolls the list view to today's date
                    setTimeout(() => {
                        const todayElement = document.querySelector('.fc-list-day-today');
                        if (todayElement) {
                            todayElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    }, 200);
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
