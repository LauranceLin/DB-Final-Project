const taipeiDistricts = [
    { value: 'Zhongzheng', textContent: '中正區' },
    { value: 'Datong', textContent: '大同區' },
    { value: 'Zhongshan', textContent: '中山區' },
    { value: 'Songshan', textContent: '松山區' },
    { value: 'Daan', textContent: '大安區' },
    { value: 'Wanhua', textContent: '萬華區' },
    { value: 'Xinyi', textContent: '信義區' },
    { value: 'Shilin', textContent: '士林區' },
    { value: 'Beitou', textContent: '北投區' },
    { value: 'Neihu', textContent: '內湖區' },
    { value: 'Nangang', textContent: '南港區' },
    { value: 'Wenshan', textContent: '文山區' }
];

const newTaipeiDistricts = [
    { value: 'Wanli', textContent: '萬里區' },
    { value: 'Jinshan', textContent: '金山區' },
    { value: 'Banqiao', textContent: '板橋區' },
    { value: 'Xizhi', textContent: '汐止區' },
    { value: 'Shenkeng', textContent: '深坑區' },
    { value: 'Shiding', textContent: '石碇區' },
    { value: 'Ruifang', textContent: '瑞芳區' },
    { value: 'Pingxi', textContent: '平溪區' },
    { value: 'Shuangxi', textContent: '雙溪區' },
    { value: 'Gongliao', textContent: '貢寮區' },
    { value: 'Xindian', textContent: '新店區' },
    { value: 'Pinglin', textContent: '坪林區' },
    { value: 'Wulai', textContent: '烏來區' },
    { value: 'Yonghe', textContent: '永和區' },
    { value: 'Zhonghe', textContent: '中和區' },
    { value: 'Tucheng', textContent: '土城區' },
    { value: 'Sanxia', textContent: '三峽區' },
    { value: 'Shulin', textContent: '樹林區' },
    { value: 'Yingge', textContent: '鶯歌區' },
    { value: 'Sanchong', textContent: '三重區' },
    { value: 'Xinzhuang', textContent: '新莊區' },
    { value: 'Taishan', textContent: '泰山區' },
    { value: 'Linkou', textContent: '林口區' },
    { value: 'Luzhou', textContent: '蘆洲區' },
    { value: 'Wugu', textContent: '五股區' },
    { value: 'Bali', textContent: '八里區' },
    { value: 'Tamsui', textContent: '淡水區' },
    { value: 'Sanzhi', textContent: '三芝區' },
    { value: 'Shimen', textContent: '石門區' }
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

    if (citySelect.value === 'Taipei') {
        taipeiDistricts.forEach(district => {
            const option = document.createElement('option');
            option.value = district.value;
            option.textContent = district.textContent;
            districtSelect.appendChild(option);
        });
    } else if (citySelect.value === 'NewTaipei') {
        newTaipeiDistricts.forEach(district => {
            const option = document.createElement('option');
            option.value = district.value;
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
    select.name = 'eventanimals[' + i + '][animaltype]'; 
    var options = ["狗", "貓", "鳥", "蛇", "鹿", "猴子", "魚", "熊", "其他"]; 
    for (var j = 0; j < options.length; j++) {
        var option = document.createElement('option');
        option.value = j;
        option.textContent = options[j];
        select.appendChild(option);
    }

    var input = document.createElement('input');
    input.type = 'text';
    input.name = 'eventanimals[' + i + '][animaldescription]';
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
