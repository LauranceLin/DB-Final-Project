import psycopg2
import bcrypt
import string
import random
import csv
import numpy as np
import datetime
from faker import Faker
from sqlalchemy import event
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
import time
from sqlalchemy import text

def manual_gen_password():
    global PASSWORD_LEN
    len = random.choice(PASSWORD_LEN)
    letters = string.ascii_letters + string.digits
    passwd = ''.join(random.choice(letters) for _ in range(len))
    print(passwd)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(passwd.encode(), salt).decode()
    return hashed


def gen_org_email():
    len = random.choice(PASSWORD_LEN)
    letters = string.ascii_letters + string.digits
    email = ''.join(random.choice(letters) for _ in range(len))
    email = email.lower().replace(" ", "_")[:20] + "@gmail.com"
    return email


def gen_phonenumber():
    global PHONENUM_LEN
    letters = string.digits
    return ''.join(random.choice(letters) for i in range(PHONENUM_LEN))


PASSWORD_LEN = range(8, 16)
PHONENUM_LEN = 10

# # read responder csv
# df = pd.read_csv("./csv/responder.csv", dtype={'phonenumber': str})
# df['respondername'] = df['respondername'].str.replace(" ","")
# # print(type(df['password'][1]))
# # fill the password and email
# df['password'] = df['password'].apply(lambda x: manual_gen_password() if x != x else x)
# df['email'] = df['email'].apply(lambda x: gen_org_email() if x != x else x)
# obj_list = df.to_dict(orient='records')
# engine = create_engine('postgresql://postgres:postgres@127.0.0.1:5432/furalert')

# for responder in obj_list:
#     stmt = f"UPDATE responder SET respondername='{responder['respondername']}', phonenumber='{responder['phonenumber']}', respondertype='{responder['respondertype']}', address='{responder['address']}' WHERE responderid='{responder['responderid']}';"
#     print(stmt)
#     with engine.begin() as connection:
#         connection.execute(text(stmt))

# df.to_sql("responder", engine.connect(), index=False, if_exists="append")


df = pd.read_csv("./csv/replacement.csv", dtype={'phonenumber': str})
df = df[166:]
df['phonenumber'] = df['phonenumber'].apply(lambda x: gen_phonenumber() if x != x else x)
print(df)
obj_list = df.to_dict(orient='records')
engine = create_engine('postgresql://postgres:postgres@127.0.0.1:5432/furalert')
for placement in obj_list:
    stmt = f"UPDATE placement SET name='{placement['name']}', address='{placement['address']}', phonenumber='{placement['phonenumber']}' WHERE placementid='{placement['placementid']}';"
    print(stmt)
    with engine.begin() as connection:
        connection.execute(text(stmt))

# df.to_sql("placement", engine.connect(), index=False, if_exists="append")