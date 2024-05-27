import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from psycopg2 import connect
import logging
import argparse

load_dotenv()

POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

parser = argparse.ArgumentParser(description='Start backend for Statistic HH')
parser.add_argument('-i', '--ip')
parser.add_argument('-p', '--port')
args = parser.parse_args()
HOST = args.ip
PORT = args.port

file_log = logging.FileHandler(f'./logs/incr_job_logs/{datetime.now().strftime("%d-%m-%Y_%H:%M:%S")} incr_job.log')
console_out = logging.StreamHandler()
logger = logging.getLogger(__name__)
FORMAT = '[%(asctime)s | %(levelname)s]: %(message)s'
logging.basicConfig(handlers=(file_log, console_out), level=logging.INFO, format=FORMAT)

cities  = ['1', '2']
logger.info(f"Cities for parse:{cities}")

date = (datetime.now() - timedelta(days=1)).date()
logger.info(f"Date for parse - {date}")

per_page = 100
logger.info(f"Per_page = {per_page}")

# Парсим данные из ЦБ РФ

url_exchange_rates = f"http://{HOST}:{PORT}/exchange_rates"
logger.info(f"Url - {url_exchange_rates}")
params_exchange_rates = {"date":date.strftime("%Y/%m/%d")}
logger.info(f"Parameters for post requests - {params_exchange_rates}")
req_exchange_rates = requests.post(url=url_exchange_rates, params=params_exchange_rates)
if req_exchange_rates.status_code == 200:
    logger.info("Parsing completed successfully")
else:
    logger.error("Error parse for exchange rates")
    raise RuntimeError

# Парсим данные из HH
with connect(host=POSTGRES_HOST, port=POSTGRES_PORT, dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD) as conn:
    cur = conn.cursor()
    cur.execute("select name from d_query_profession;")
    logger.info("Getting data about professions in the database")
    date = date.strftime("%Y-%m-%d")
    logger.info(f"Date - {date}")
    for value in  cur.fetchall():
        profession = value[0] 
        logger.info(f"Start parse data for profession - {profession}")
        
        for page in range(20):
            logger.info(f"Page - {page}")
            for city in cities:
                logger.info(f"City - {city}")
                params_parse = {"profession":profession, "page": str(page), "date":date, "per_page": str(per_page), "area":city}
                logger.info(f"Parameters for parse {params_parse}")
                url_parse = f"http://{HOST}:{PORT}/parse"
                logger.info(f"Url - {url_parse}")
                req_parse = requests.post(url_parse, params=params_parse)
                if req_parse.status_code == 200:
                    logger.info("Parsing completed successfully")
                else:
                    logger.error("Error parse for vacancies")
                    raise RuntimeError

# Создаем метрики
path_script = os.path.dirname(os.path.abspath(__file__)) + '/sql/increment_insert_data.sql' 
logger.info(f"Path for script - {path_script}")
with open(path_script, 'r') as file, connect(host=POSTGRES_HOST, port=POSTGRES_PORT, dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD) as conn:
    cur = conn.cursor()
    cur.execute(file.read())
    logger.info("Data processed successfully")