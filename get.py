import requests
from datetime import date, datetime, timedelta
import json


url = 'http://localhost:8080/metrics'

data = {
        'profession_id': '1'
        ,'city_id': '1'
        ,'date_from': str(date(2023,10,29))
        ,'date_to': str(date(2023,11,14))
        }

print(data)

r = requests.get(url, params=data)

print(r.headers, r.status_code, r.text) 

f = open('data.json', 'wb')
f.write(r.text.encode('utf-8'))

f.close()