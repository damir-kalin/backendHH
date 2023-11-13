import requests
import json
from datetime import date, datetime, timedelta


# response = requests.post('http://localhost:8080/parse/1/1')
url = 'http://localhost:8080/parse'
headers = {'Content-type': 'application/json',
           'Accept': 'text/plain',
           'Content-Encoding': 'utf-8'}
data = {
        'profession':'аналитик'
        ,'city_id':'1'
        ,'date': str(date.today() - timedelta(days=1))
        }

# print(data)

answer = requests.post(url, headers=headers, json=data)

print(answer.headers, answer.status_code, answer.text) 

