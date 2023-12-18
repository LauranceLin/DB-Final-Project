document.getElementById('banUserBtn').addEventListener('click', function() {
    var userId = this.getAttribute('data-userid');

    fetch('/banuser/' + userId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
    })
    .then(response => {
        if (response.ok) {
            alert('User banned successfully!');
        } else {
            alert('Failed to ban user. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while banning the user.');
    });
});