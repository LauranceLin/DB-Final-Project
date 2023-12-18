fetch('/placementinfo')
        .then(response => response.json())
        .then(function(placementData){
            const animalEntries = document.querySelectorAll('.AnimalEntry');

            animalEntries.forEach((entry) => {
                const selectElement = entry.querySelector('.placementSelect');
                selectElement.name = 'placement';
                selectElement.innerHTML = '';
                const dataPlacement = entry.getAttribute('data-placement');

                for (const placement of placementData) {
                    const option = document.createElement('option');
                    option.setAttribute('value', placement.placementid);
                    if (placement.placementname === dataPlacement) {
                        option.setAttribute('selected', true);
                    }
                    option.textContent = placement.placementname;
                    selectElement.appendChild(option);
                }
            });
        })
.catch(function(error) {
    console.error('There has been a problem with your fetch operation:', error);
});

document.getElementById('deleteEventBtn').addEventListener('click', function() {
    var eventid = this.getAttribute('data-eventid');

    fetch('/delete_event/' + eventid, {
        method: 'DELETE'
    })
    .then(response => {
        if (response.ok) {
            alert('Event deleted successfully!');
        } else {
            alert('Failed to delete event. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while deleting the event.');
    });
});