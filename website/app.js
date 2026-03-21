async function loadCalendars(){
    const response = await fetch('/calendars');
    const calendars = await response.json();
    console.log(calendars);
}

loadCalendars();