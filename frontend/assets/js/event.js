fetch('/userinfo', {
    method: 'GET',
    credentials: 'same-origin'
})
    .then(response => response.json())
    .then(function (data) {
        if (data.role === 'user') {
            document.getElementById('report').style.display = 'block';

            fetch('/placementinfo')
                .then(response => response.json())
                .then(function (placementData) {
                    const animalEntries = document.querySelectorAll('.AnimalEntry');

                    animalEntries.forEach((entry) => {
                        const selectElement = entry.querySelector('.placementSelect');
                        selectElement.name = 'placement';
                        selectElement.innerHTML = '';
                        const dataPlacement = entry.getAttribute('data-placement');
                        console.log(typeof(dataPlacement))
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
                });

        } else {
            // document.getElementById('report').style.display = 'none';
            document.getElementById('report').style.display = 'block';
            document.getElementById('acceptBtn').style.display = 'block';

            fetch('/placementinfo')
                .then(response => response.json())
                .then(function (placementData) {
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
                });

            const responderid = document.getElementById('responderInput').getAttribute('data-responderid');
            if (data.userid == responderid) {
                document.getElementById('closeBtn').style.display = 'none';
                document.getElementById('acceptBtn').style.display = 'none';
                document.getElementById('editZone').style.display = 'block';
            }
        }
    })
    .catch(function (error) {
        console.error('There has been a problem with your fetch operation:', error);
    });

function switchToEdit() {
    document.getElementById('editZone').style.display = 'none';
    document.getElementById('editMode').style.display = 'block';

    document.getElementById('citySelect').disabled = false;
    document.getElementById('districtSelect').disabled = false;
    document.getElementById('roadInput').disabled = false;
    document.getElementById('eventTypeSelect').disabled = false;
    document.getElementById('descriptionInput').disabled = false;
    document.getElementById('eventStatusSelect').disabled = false;

    status_selector = document.getElementById('eventStatusSelect');
    status_selector.children[0].disabled = true // 選擇事件狀態
    status_selector.children[1].disabled = false // unresolved
    status_selector.children[2].disabled = true // resolved
    status_selector.children[3].disabled = false // ongoing
    status_selector.children[4].disabled = false // false alarm
    status_selector.children[5].disabled = true // failed
    status_selector.children[6].disabled = true // deleted

    const placementSelects = document.getElementsByClassName('placementSelect');
    for (let i = 0; i < placementSelects.length; i++) {
        placementSelects[i].disabled = false;
    }

    const animalDescriptionInputs = document.getElementsByClassName('animalDescriptionInput');
    for (let i = 0; i < animalDescriptionInputs.length; i++) {
        animalDescriptionInputs[i].disabled = false;
    }

    const animaltypes = document.getElementsByClassName('animaltype')
    for (let i = 0; i < animaltypes.length; i++) {
        animaltypes[i].disabled = false;
    }
}

const taipeiDistricts = [
    { value: 0, textContent: '中正區' },
    { value: 1, textContent: '大同區' },
    { value: 2, textContent: '中山區' },
    { value: 3, textContent: '松山區' },
    { value: 4, textContent: '大安區' },
    { value: 5, textContent: '萬華區' },
    { value: 6, textContent: '信義區' },
    { value: 7, textContent: '士林區' },
    { value: 8, textContent: '北投區' },
    { value: 9, textContent: '內湖區' },
    { value: 10, textContent: '南港區' },
    { value: 11, textContent: '文山區' }
];

const newTaipeiDistricts = [
    { value: 0, textContent: '萬里區' },
    { value: 1, textContent: '金山區' },
    { value: 2, textContent: '板橋區' },
    { value: 3, textContent: '汐止區' },
    { value: 4, textContent: '深坑區' },
    { value: 5, textContent: '石碇區' },
    { value: 6, textContent: '瑞芳區' },
    { value: 7, textContent: '平溪區' },
    { value: 8, textContent: '雙溪區' },
    { value: 9, textContent: '貢寮區' },
    { value: 10, textContent: '新店區' },
    { value: 11, textContent: '坪林區' },
    { value: 12, textContent: '烏來區' },
    { value: 13, textContent: '永和區' },
    { value: 14, textContent: '中和區' },
    { value: 15, textContent: '土城區' },
    { value: 16, textContent: '三峽區' },
    { value: 17, textContent: '樹林區' },
    { value: 18, textContent: '鶯歌區' },
    { value: 19, textContent: '三重區' },
    { value: 20, textContent: '新莊區' },
    { value: 21, textContent: '泰山區' },
    { value: 22, textContent: '林口區' },
    { value: 23, textContent: '蘆洲區' },
    { value: 24, textContent: '五股區' },
    { value: 25, textContent: '八里區' },
    { value: 26, textContent: '淡水區' },
    { value: 27, textContent: '三芝區' },
    { value: 28, textContent: '石門區' }
];

const citySelect = document.getElementById('citySelect');
const districtSelect = document.getElementById('districtSelect');

citySelect.addEventListener('change', function () {
    districtSelect.innerHTML = '';
    const hint = document.createElement('option');
    hint.value = '';
    hint.textContent = '選擇行政區';
    hint.selected = true;
    hint.disabled = true;
    districtSelect.appendChild(hint);

    if (citySelect.value === '0') {
        taipeiDistricts.forEach(district => {
            const option = document.createElement('option');
            option.value = district.value;
            option.textContent = district.textContent;
            districtSelect.appendChild(option);
        });
    } else if (citySelect.value === '1') {
        newTaipeiDistricts.forEach(district => {
            const option = document.createElement('option');
            option.value = district.value;
            option.textContent = district.textContent;
            districtSelect.appendChild(option);
        });
    }
});