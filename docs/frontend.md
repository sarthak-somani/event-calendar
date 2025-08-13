# Frontend Documentation

The frontend of the IITB Event Hub is responsible for displaying the event data to the user. It consists of three main files:

- `index.html`: The main HTML file that structures the web page.
- `style.css`: The CSS file that styles the application.
- `script.js`: The JavaScript file that handles the application's logic, including fetching data and rendering the calendar.

## `index.html`

The `index.html` file provides the basic structure of the web application. It includes:

- **Header**: Contains the title of the application, "IITB Event Hub".
- **Main Content**: Divided into two main sections:
    - `calendar-container`: This is where the interactive FullCalendar is rendered.
    - `event-list-container`: This section displays a list of upcoming events.
- **External Libraries**: The file links to the following external libraries via CDN:
    - **Google Fonts**: For the "Inter" font.
    - **FullCalendar**: For the interactive calendar functionality.
    - **SweetAlert2**: For creating attractive pop-up modals to display event details.
- **Local Scripts and Styles**: It links to the local `style.css` for styling and `script.js` for the application logic.

## `style.css`

This file contains all the CSS rules for styling the application. It defines the layout, colors, fonts, and other visual aspects of the elements in `index.html`. It ensures a clean and responsive design that works on both desktop and mobile devices.

## `script.js`

The `script.js` file contains the core logic for the frontend. It executes when the DOM is fully loaded.

### Key Functionality:

1.  **Initialization**: It gets references to the calendar and event list elements in the DOM.
2.  **Event Data Fetching**:
    - It uses the `fetch` API to load the event data from the `events.json` file.
    - The `events` function within the FullCalendar configuration is responsible for this.
3.  **Populate Upcoming Events**:
    - The `populateEventList` function filters the events to find those that are in the future.
    - It then sorts them by date and displays the next 7 upcoming events in the "Upcoming Events" list.
4.  **Calendar Rendering**:
    - It initializes a new `FullCalendar` object and configures it.
    - **`initialView`**: Defaults to a `listYear` view on mobile and `dayGridMonth` on desktop.
    - **`headerToolbar`**: Configures the navigation buttons for the calendar (e.g., prev, next, today, and different views).
    - **`events`**: Specifies the function to fetch event data.
    - **`eventClick`**: Defines a callback function that is triggered when a user clicks on an event. This function uses `SweetAlert2` to display a modal with detailed information about the clicked event.
5.  **Mobile-Specific Behavior**: The script includes logic to automatically scroll to today's date when the calendar is in the `listYear` view on mobile devices, making it easier for users to see current events.
