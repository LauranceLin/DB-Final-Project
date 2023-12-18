
const reportRadio = document.getElementById('reportRadio');
const warningRadio = document.getElementById('warningRadio');
const warningLevelSelect = document.getElementById('warningLevelSelect');

for (let i = 1; i <= 10; i++) {
    let option = document.createElement('option');
    option.value = i;
    option.textContent = i;
    warningLevelSelect.appendChild(option);
}

reportRadio.addEventListener('click', function() {
    warningLevelSelect.disabled = true;
});

warningRadio.addEventListener('click', function() {
    warningLevelSelect.disabled = !warningRadio.checked;
});

function resetForm() {
    document.getElementById('reportRadio').checked = true;
    document.getElementById('warningRadio').checked = false; 
    document.getElementById('warningLevelSelect').disabled = true;
    document.getElementById('warningLevelSelect').selectedIndex = 0;
    document.getElementById('descriptionInput').value = '';
}