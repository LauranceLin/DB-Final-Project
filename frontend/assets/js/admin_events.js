document.getElementById('confirmBtn').addEventListener('click', function(event) {
    event.preventDefault();

    var locationValue = document.getElementById('locationSelect').value;
    var animalValue = document.getElementById('animalSelect').value;
    var eventTypeValue = document.getElementById('eventTypeSelect').value;

    var queryParams = [];

    if (locationValue !== '') {
      queryParams.push('eventdistrict=' + locationValue);
    }

    if (animalValue !== '') {
      queryParams.push('animaltype=' + animalValue);
    }

    if (eventTypeValue !== '') {
      queryParams.push('eventtype=' + eventTypeValue);
    }

    var queryString = queryParams.join('&');

    var url = '/admin_events/0';

    if (queryString !== '') {
      url += '?' + queryString;
    }

    window.location.href = url;
  });