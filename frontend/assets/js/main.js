$('#profileModal').on('show.bs.modal', function (event) {
    var role = document.cookie.split('; ').find(row => row.startsWith('role=')).split('=')[1];
    var id = document.cookie.split('; ').find(row => row.startsWith('id=')).split('=')[1];

    fetch(`/info/${role}/${id}`)
    .then(response => response.json())
    .then(data => {
        document.getElementById('idInput').value = id;
        document.getElementById('nameInput').value = data.name;
        document.getElementById('emailInput').value = data.email;
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
  
document.getElementById('logoutBtn').addEventListener('click', function() {
    document.cookie = "loggedIn=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    window.location.href = "login.html"; 
});