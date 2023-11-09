import requests
from datetime import date, datetime, timedelta
import json


url = 'http://localhost:8080/skills'

data = {'date_from': str(date(2023,10,29))
        #,'date_to': str(date(2023,10,29))
        }

print(data)

r = requests.get(url, params=data)

print(r.headers, r.status_code, r.text) 

f = open('data.json', 'wb')
f.write(r.text.encode('utf-8'))
