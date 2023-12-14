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
            option.value = district.textContent;
            option.textContent = district.textContent;
            districtSelect.appendChild(option);
        });
    } else if (citySelect.value === '1') {
        newTaipeiDistricts.forEach(district => {
            const option = document.createElement('option');
            option.value = district.textContent;
            option.textContent = district.textContent;
            districtSelect.appendChild(option);
        });
    }
});


var addAnimalButton = document.getElementById('addAnimalBtn');
var animalContainer = document.getElementById('animalContainer');
var i = 0;

addAnimalButton.addEventListener('click', function() {
    var animalEntry = document.createElement('div');

    var select = document.createElement('select');
    // select.name = 'eventanimals[' + i + '][animaltype]';
    select.name = 'animaltype'
    var options = ["狗", "貓", "鳥", "蛇", "鹿", "猴子", "魚", "熊", "其他"];
    for (var j = 0; j < options.length; j++) {
        var option = document.createElement('option');
        option.value = j;
        option.textContent = options[j];
        select.appendChild(option);
    }

    var input = document.createElement('input');
    input.type = 'text';
    // input.name = 'eventanimals[' + i + '][animaldescription]';
    input.name = 'animaldescription'
    input.placeholder = '動物描述';

    animalEntry.appendChild(select);
    animalEntry.appendChild(input);
    animalContainer.appendChild(animalEntry);

    i++;
});

function resetForm() {
    document.getElementById("citySelect").selectedIndex = 0;
    document.getElementById("districtSelect").selectedIndex = 0;
    document.getElementById("roadInput").value = "";

    var animalContainer = document.getElementById("animalContainer");
    animalContainer.innerHTML = "";

    document.getElementById("eventTypeSelect").selectedIndex = 0;
    document.getElementById("descriptionInput").value = "";
    document.getElementById("imageUrlInput").value = "";
}
