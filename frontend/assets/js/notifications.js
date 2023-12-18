
document.getElementById('confirmFilterBtn').addEventListener('click', function() {
    var eventCheckbox = document.getElementById('eventCheckbox');
    var warningCheckbox = document.getElementById('warningCheckbox');

    var eventType = ''; 

    if (eventCheckbox.checked && !warningCheckbox.checked) {
        eventType = 'event';
    } else if (warningCheckbox.checked && !eventCheckbox.checked) {
        eventType = 'warning';
    } else if (eventCheckbox.checked && warningCheckbox.checked) {
        eventType = 'both'; 
    }

    var redirectURL = "/notifications/0";

    if (eventType !== '') {
        redirectURL += '?type=' + eventType;
    }

    window.location.href = redirectURL; 
});

document.getElementById('clearFilterBtn').addEventListener('click', function() {
    document.getElementById('eventCheckbox').checked = true;
    document.getElementById('warningCheckbox').checked = true;
});
