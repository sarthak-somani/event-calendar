document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');

    // Initialize the calendar
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listWeek' // Month, Week, List views
        },
        
        // ### THIS IS THE CHANGE ###
        // Tell FullCalendar to fetch events directly from your events.json file
        events: 'events.json',

        // Optional: Show event description on click
        eventClick: function(info) {
            let description = info.event.extendedProps.description || 'No description available.';
            let venue = info.event.extendedProps.venue || 'Venue not specified.';
            let body = info.event.extendedProps.organisingBody || 'Organizer not specified.';

            alert(
                'Event: ' + info.event.title + '\n' +
                '-------------------\n' +
                'Description: ' + description + '\n' +
                'Venue: ' + venue + '\n' +
                'Organizer: ' + body
            );
        }
    });

    // Render the calendar
    calendar.render();
});
