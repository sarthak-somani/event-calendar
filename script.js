document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');

    // Sample event data. We will replace this with real data later.
    const dummyEvents = [
        {
            title: 'Guest Lecture: AI in Science',
            start: '2025-08-11T17:30:00',
            extendedProps: {
                description: 'Dr. Anya Sharma discusses the future of AI.',
                venue: 'Convocation Hall'
            }
        },
        {
            title: 'Robotics Club Workshop',
            start: '2025-08-15',
            end: '2025-08-17',
            extendedProps: {
                description: 'A 3-day hands-on robotics workshop.',
                venue: 'VMCC'
            }
        },
        {
            title: 'Music Club Auditions',
            start: '2025-08-20T18:00:00',
            extendedProps: {
                description: 'Auditions for all singers and instrumentalists.',
                venue: 'Student Activity Center'
            }
        }
    ];

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listWeek' // Month, Week, List views
        },
        events: dummyEvents,
        // Optional: Show event description on click
        eventClick: function(info) {
            alert(
                'Event: ' + info.event.title + '\n' +
                'Description: ' + info.event.extendedProps.description + '\n' +
                'Venue: ' + info.event.extendedProps.venue
            );
        }
    });

    calendar.render();
});
