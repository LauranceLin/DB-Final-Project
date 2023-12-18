document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.delete-button');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const channelid = button.getAttribute('data-channelid');

            fetch(`/delete_subscription/${channelid}`, {
                method: 'POST',
                credentials: 'same-origin'
            })
            .then(response => {
                if (response.ok) {
                    window.location.reload(); 
                } else {
                    console.error('Error deleting subscription');
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
});
