document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('button[name="delete"]');

    deleteButtons.forEach(deleteButton => {
        deleteButton.addEventListener('click', function(event) {
            event.preventDefault();

            const eventid = this.dataset.eventid;

            if (eventid) {
                fetch(`/delete_event/${eventid}`, {
                    method: 'POST',
                    credentials: 'same-origin'
                })
                .then(response => {
                    if (response.redirected) {
                        window.location.href = response.url;
                    }
                })
                .catch(error => {
                    console.error('There has been a problem with your fetch operation:', error);
                });
            } else {
                console.error('Event ID not found!');
            }
        });
    });
});
