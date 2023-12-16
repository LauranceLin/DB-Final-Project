fetch('/userinfo', {
    method: 'GET',
    credentials: 'same-origin'
})
.then(response => response.json())
.then(function(data) {
    if (data.role === 'user') {
        document.getElementById('report').style.display = 'block';
    } else {
        document.getElementById('report').style.display = 'none';
        document.getElementById('acceptBtn').style.display = 'block';
        
        fetch('/placementinfo')
        .then(response => response.json())
        .then(function(placementData){
            const animalEntries = document.querySelectorAll('.AnimalEntry');
            
            animalEntries.forEach((entry) => {
                const selectElement = entry.querySelector('.placementSelect');
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
        if(data.userid == responderid) {
            document.getElementById('closeBtn').style.display = 'none';
            document.getElementById('acceptBtn').style.display = 'none';
            document.getElementById('editZone').style.display = 'block';
        }
    }
})
.catch(function(error) {
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
    document.getElementById('imageUrlInput').disabled = false;
    document.getElementById('eventStatusSelect').disabled = false;

    const placementSelects = document.getElementsByClassName('placementSelect');
    for (let i = 0; i < placementSelects.length; i++) {
        placementSelects[i].disabled = false;
    }

    const animalDescriptionInputs = document.getElementsByClassName('animalDescriptionInput');
    for (let i = 0; i < animalDescriptionInputs.length; i++) {
        animalDescriptionInputs[i].disabled = false;
    }
}

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