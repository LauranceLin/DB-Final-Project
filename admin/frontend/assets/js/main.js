
fetch('/userinfo')
.then(response => response.json())
.then(data => {
    if (data.role === 'user') {
        document.getElementById('create-event').style.display = 'list-item';
        document.getElementById('report-record').style.display = 'list-item';
    } else if (data.role === 'responder') {
        document.getElementById('respond-record').style.display = 'list-item';
    }
})
.catch(error => {
    console.error('Error fetching userinfo:', error);
});

const idInput = document.getElementById('idInput');
const nameInput = document.getElementById('nameInput');
const emailInput = document.getElementById('emailInput');
const logoutBtn = document.getElementById('logoutBtn');
const profileModal = document.getElementById('profileModal');

profileModal.addEventListener('show.bs.modal', function () {
    fetch('/userinfo')
        .then(response => response.json())
        .then(data => {
            idInput.value = data.userid;
            nameInput.value = data.name;
            emailInput.value = data.email;
        })
        .catch(error => {
            console.error('Error fetching userinfo:', error);
        });
});

logoutBtn.addEventListener('click', () => {
    fetch('/logout', {
        method: 'GET'
    })
    .then(response => {
        console.log('Logout successful');
        window.location.href = '/login';
    })
    .catch(error => {
        console.error('Error during logout:', error);
    });
});
