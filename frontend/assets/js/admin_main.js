
const idInput = document.getElementById('idInput');
const emailInput = document.getElementById('emailInput');
const logoutBtn = document.getElementById('logoutBtn');
const profileModal = document.getElementById('profileModal');

profileModal.addEventListener('show.bs.modal', function () {
    fetch('/userinfo')
        .then(response => response.json())
        .then(data => {
            idInput.value = data.userid;
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
