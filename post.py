import requests
import json
from datetime import date, datetime, timedelta
import os



url = 'http://localhost:80/parse'
headers = {'Content-type': 'application/json',
           'Accept': 'text/plain',
           'Content-Encoding': 'utf-8'}
data = {'profession':'Аналитик'
        ,'city_id':'1'
        ,'date': str(date.today() - timedelta(days=8))
        }

print(data)

answer = requests.post(url, headers=headers, json=data)

print(answer.headers, answer.status_code, answer.text) 
# with open(os.getcwd() + '/env', 'r', encoding='utf-8') as f:
#         print(f.readlines())