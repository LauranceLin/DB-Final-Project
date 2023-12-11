import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import threading
from fake_user_agent import user_agent
from queue import Queue
import os


def get_new_taipei_address():
    headers = {
        # 'authority': 'www.addresscopy.com',
        # 'method': 'GET',
        # 'scheme': 'https',
        # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        # 'Accept-Encoding': 'gzip, deflate, br',
        # 'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        # 'Referer': 'https://www.addresscopy.com/taiwan/Taipei_City/',
        # 'Sec-Ch-Ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        # 'Sec-Ch-Ua-Mobile': '?0',
        # 'Sec-Ch-Ua-Platform': '"macOS"',
        # 'Sec-Fetch-Dest': 'document',
        # 'Sec-Fetch-Mode': 'navigate',
        # 'Sec-Fetch-Site': "same-origin",
        # 'Sec-Fetch-User': "?1",
        # 'Upgrade-Insecure-Requests': "1",
        'User-Agent': user_agent()
    }
    response = requests.get(
        "https://www.addresscopy.com/taiwan/New_Taipei_City/", headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    results = soup.find_all("li", {
        'class': 'text-dark',
        'style': 'text-align:left; font-size:18px;'
    })
    temp = {}
    for result in results:
        string = result.text
        if '縣市名稱: = ' in string:
            temp['縣市'] = string.replace('縣市名稱: = ', '')
        elif '市區名稱: = ' in string:
            temp['市區'] = string.replace('市區名稱: = ', '')
        elif '完整地址: ' in string:
            temp['地址'] = string.replace('完整地址: ', '')
    return temp


def get_address_job(q):
    # print(get_new_taipei_address())
    try:
        q.put(get_new_taipei_address())
    except:
        pass



def get_address_csv(number):
    start_time = time.time()
    count = 1000
    address_list = []
    all_thread = []
    q = Queue()
    for i in range(count):
        thread = threading.Thread(target=get_address_job, args=(q,))
        thread.start()
        all_thread.append(thread)


        # try:
        #     address_list.append(get_new_taipei_address())
        # except:
        #     continue

    for t in all_thread:
        t.join()
    print(q.qsize())
    for _ in range(q.qsize()):
        address_list.append(q.get())

    # print(address_list)
    df = pd.DataFrame(address_list)
    print(df)
    df.to_csv(f'new_taipei_address_{number}.csv')
    print("--- %s seconds ---" % (time.time() - start_time))


# for i in range(30, 50):
#     get_address_csv(i)
#     time.sleep(5)

folder_path = "./"
dirs = os.listdir(folder_path)
exportList = []
df = pd.DataFrame()
for file in dirs:
    if file.endswith(".csv"):
        print(file[:len(file)-4])
        temp_df = pd.read_csv(folder_path+file, index_col=0)
        df = pd.concat([df, temp_df], ignore_index=True)
print(len(df))
df = df.dropna()
replace_list = ['台灣省']
replace_list.extend(list(df['市區'].unique()))
replace_list.extend(list(df['縣市'].unique()))
for replace in replace_list:
    df['地址'] = df['地址'].str.replace(replace, '')

print(len(df))
print(df)
df.to_csv("taipei_address.csv", index=False)