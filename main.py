from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import psycopg2
import json
from datetime import datetime
import requests
import time
from bson.json_util import dumps
import argparse
import sys
import os

class S(BaseHTTPRequestHandler):

    def __init__(self, request, client_address, server) -> None:
        self.config = self.get_config()
        super().__init__(request, client_address, server)

    def get_config(self):
        config = None
        # try:
        with open(os.getcwd() + '/env', 'r', encoding='utf-8') as f:
            config =  {x.strip().split('=')[0]:x.strip().split('=')[1] for x in f.readlines()}
            logging.info("%s - Read config", datetime.now())
            logging.info(config)
            return config
        # except:
        #     logging.error("%s - _config file is missing", datetime.now())

    def get_connection_database(self):
        config =self.config
        if config:
            try:
                connection = psycopg2.connect(host=config['HOST'], port=int(config['PORT']), dbname=config['NAME_DATABASE'], user=config['USER'], password=config['PASSWORD'])
                logging.info("%s - Database connection successful", datetime.now())
                return connection
            except:
                self._set_response(500, ['Content-type', 'text/html'],"Can`t establish connection to database")
    
    def get_parameters_for_parse(self, post_data):
        if post_data != b'':
            parameters = {'page': 0, 'per_page': 100}
            data_in_post = json.loads(post_data.decode('utf-8'))
            
            if 'profession' in  data_in_post or 'city_id' in data_in_post or 'date' in data_in_post:
                try:
                    profession = data_in_post['profession']
                    logging.info("%s - profession = %s", datetime.now(), profession)
                    parameters['text'] = f'NAME:{profession}'
                except:
                    logging.info("%s - The 'profession' parameter is not specified", datetime.now())
                try:
                    city_id = data_in_post['city_id']
                    logging.info("%s - city_id = %s", datetime.now(), city_id)
                    parameters['area'] = city_id
                except:
                    logging.info("%s - The 'city_id' parameter is not specified", datetime.now())
                try:
                    date_search = data_in_post['date']
                    logging.info("%s - date = %s", datetime.now(), date_search)
                    parameters['date_from'] = date_search
                    parameters['date_to'] = date_search
                except:
                    logging.info("%s - The 'date' parameter is not specified", datetime.now())
                logging.info("%s - Parameters collected for parsing", datetime.now())
                return parameters
            else:
                self._set_response(500, ['Content-type', 'text/html'], "Missing parameters in json format (profession, city_id, date)")
                return
        else:
            self._set_response(500, ['Content-type', 'text/html'], "Missing parameters in json format (profession, city_id, date)")
            return

    def _set_response(self, response, header, message):
        if response == 200:
            logging.info("%s - %s", datetime.now(), message)
        else:
            logging.error("%s - %s", datetime.now(), message)
        self.send_response(response)
        self.send_header(header[0], header[1])
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))
    
    def get_url_vacancy_in_page(self, parameters):
        logging.info('%s - Get search pages with parameters %s', datetime.now(), parameters)
        try:
            req_page = requests.get('https://api.hh.ru/vacancies', parameters)
            urls = []
            if req_page.status_code == 200:
                data_in_page = json.loads(req_page.content.decode())
                req_page.close()
                logging.info("%s - Page received", datetime.now())
                for vacancy in data_in_page['items']:
                    urls.append(vacancy['url'])
                return urls
        except:
            self._set_response(500, ['Content-type', 'text/html'], "API HH not available")
            return
    
    def get_data_in_vacancy(self, url):
        logging.info('%s - Receiving data from a link: %s', datetime.now(), url)
        try:
            req_vacancy = requests.get(url)
            result = {}
            if req_vacancy.status_code == 200:
                data_in_vacancy = json.loads(req_vacancy.content.decode())
                req_vacancy.close()
                result["vacancy_id"] = data_in_vacancy['id']
                logging.info('%s - vacancy_id = %s', datetime.now(), result["vacancy_id"])
                result["city_id"] = data_in_vacancy['area']['id']
                result["profession_name"] = None 
                if data_in_vacancy.get('name') != None:
                    result["profession_name"] = data_in_vacancy['name']
                logging.info('%s - profession_name = %s', datetime.now(), result["profession_name"])
                result["salary_currency"] = None
                result["salary_from"] = None
                result["salary_to"] = None
                if data_in_vacancy.get('salary') != None:
                    if data_in_vacancy['salary'].get('currency') != None:
                        result["salary_currency"] = data_in_vacancy['salary']['currency']
                    if data_in_vacancy['salary'].get('from') != None:
                        result["salary_from"] = float(data_in_vacancy['salary']['from'])
                    if data_in_vacancy['salary'].get('to') != None:
                        result["salary_to"] = float(data_in_vacancy['salary']['to'])
                logging.info('%s - salary_currency = %s', datetime.now(), result["salary_currency"])
                logging.info('%s - salary_from = %s', datetime.now(), result["salary_from"])
                logging.info('%s - salary_to = %s', datetime.now(), result["salary_to"])
                result["experience"] = None
                if data_in_vacancy.get('experience') != None:
                    if data_in_vacancy['experience'].get('id') != None:
                        result["experience"] = data_in_vacancy['experience']['id']
                logging.info('%s - experience = %s', datetime.now(), result["experience"])
                result["shedule"] = None
                if data_in_vacancy.get('schedule') != None:
                    if data_in_vacancy['schedule'].get('id') != None:
                        result["shedule"] = data_in_vacancy['schedule']['id']
                logging.info('%s - shedule = %s', datetime.now(), result["shedule"])
                result["skills"] = None 
                if len(data_in_vacancy.get('key_skills')) != 0:
                    skills = data_in_vacancy['key_skills']
                    result["skills"] = [ skills[x]['name'] for x in range(0, len(skills))]
                logging.info('%s - skills = %s', datetime.now(), result["skills"])
                result["published_dt"] = None
                if data_in_vacancy.get('published_at') != None:
                    result["published_dt"] = data_in_vacancy['published_at']
                logging.info('%s - published_dt = %s', datetime.now(), result["published_dt"])
                logging.info("%s - Job details have been successfully received", datetime.now())
                req_vacancy.close()
                return result
            else:
                logging.error("%s - Error captcha required!", datetime.now())
                req_vacancy.close()
                return
        except:
            self._set_response(500, ['Content-type', 'text/html'], "API HH not available")
            return

    def load_data(self, connection, vacancy):
        try:
            cursor = connection.cursor()
            cursor.execute("call insert_vacancies (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", \
                            (int(vacancy["vacancy_id"]), int(vacancy["city_id"]), vacancy["profession_name"], \
                                vacancy["salary_currency"], vacancy["salary_from"], vacancy["salary_to"], \
                                vacancy["experience"], vacancy["shedule"], vacancy["skills"], vacancy["published_dt"]))
            connection.commit()
            cursor.close()
            logging.info("%s - Data has been successfully added to the database.", datetime.now())
        except:
            logging.error("%s - There was an error entering data into the database.", datetime.now())

    def get_parameters_for_get(self, get_path):
        try:
            parameters = {x[:x.find('=')]:x[x.find('=')+1:] for x in get_path[get_path.find('?')+1:].split(sep='&')}
            if "profession_id" in parameters and "city_id" in parameters:
                str_parameters = ','.join([parameters[x] for x in ["city_id", "profession_id"]])
                if "date_from" in parameters or "date_to" in parameters:
                    str_parameters = str_parameters + ',' + ','.join(["'" + parameters[x] + "'" for x in ["date_from", "date_to"] if x in parameters])
                logging.info("%s - Parameters collected for get data", datetime.now())
                return str_parameters
            else:
                self._set_response(404, ['Content-type', 'text/html'], "No parameters for sql script")
        except:
            self._set_response(404, ['Content-type', 'text/html'], "No parameters for sql script")

    def get_data_metrics(self, connection, function, parameters):
        try:
            cursor = connection.cursor()
            cursor.execute(f"select * from {function}({parameters});")
            result = cursor.fetchall()
            cursor.close()
            return result
        except:
            self._set_response(500, ['Content-type', 'text/html'], "Failed to retrieve data from database")

    def transform_data(self, metrics, skills):
        try:
            result = [{
                'city_id': x[0],
                'profession_id': x[1],
                'dt': str(x[2]),
                'cnt': x[3],
                'no_experience_cnt': x[4],
                'between_1_and_3_cnt': x[5],
                'between_3_and_6_cnt': x[6],
                'more_than_6_cnt': x[7],
                'avg_salary': x[8],
                'no_experience_avg_salary': x[9],
                'between_1_and_3_avg_salary': x[10],
                'between_3_and_6_avg_salary': x[11],
                'more_than_6_avg_salary': x[12],
                'flexible_schedule_cnt': x[13],
                'remote_schedule_cnt': x[14],
                'full_day_schedule_cnt': x[15],
                'shift_schedule_cnt': x[16],
                'fly_in_fly_out_schedule_cnt': x[17],
                'skills': [{'name': y[3], 'cnt': y[4]} for y in skills if y[0]==x[0] and y[1]==x[1] and y[2]==x[2]]
                } for x in metrics]
            js = dumps(result) 
            return js    
        except:
            self._set_response(500, ['Content-type', 'text/html'], "Failed to retrieve data from database")


    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        connection = self.get_connection_database()
        if connection:
            if self.path.startswith('/metrics'):
                parameters = self.get_parameters_for_get(self.path)
                metrics = self.get_data_metrics(connection,"get_metric", parameters)
                skills = self.get_data_metrics(connection,"get_skills", parameters)
                result = self.transform_data(metrics, skills)
                self._set_response(200, ['Content-type', 'json'], result)
            else:
                self._set_response(404, ['Content-type', 'text/html'], "Command error. The get method only has a task for get data. (/metrics)")
            connection.close()
            logging.info("%s - Connection to database closed", datetime.now())

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))
        connection = self.get_connection_database()
        if connection:
            if self.path == '/parse':
                parameters_for_parse = self.get_parameters_for_parse(post_data)
                if parameters_for_parse:
                    logging.info(parameters_for_parse)
                    logging.info("%s - Start parse...", datetime.now())
                    for page in range(0, 20):
                        parameters_for_parse['page'] = page
                        url_in_page = self.get_url_vacancy_in_page(parameters_for_parse)
                        for url in url_in_page:
                            vacancy = self.get_data_in_vacancy(url)
                            if vacancy:
                                self.load_data(connection, vacancy)
                            time.sleep(0.25)
                            logging.info("%s - Parser sleep...", datetime.now())
                    logging.info("%s - Parse successful!", datetime.now())
                    self._set_response(200, ['Content-type', 'text/html'], "Successful request for {}".format(self.path))
            else:
                self._set_response(404, ['Content-type', 'text/html'], "Command error.The post method only has a task for data parsing.(/parse)")
            connection.close()
            logging.info("%s - Connection to database closed", datetime.now())

parser = argparse.ArgumentParser(description='Start backend for Statistic HH')
parser.add_argument('-p', '--port')
args = parser.parse_args()
logging.basicConfig(level=logging.INFO)
host = '127.0.0.1'
try:
    port = int(args.port)
    httpd = HTTPServer((host, port), S)
    logging.info('%s - host (%s) port(%s).\n', datetime.now(), host, port)
except:
    httpd = HTTPServer(('127.0.0.1', 80), S)
    logging.info('%s - host (%s) port (%s).\n', datetime.now(), host, '80')
logging.info('%s - Starting httpd...\n', datetime.now())
httpd.serve_forever()
try:
    sys.exit(130)
except SystemExit:
    os._exit(130)
finally:
    httpd.server_close()
    logging.info('%s - Stopping httpd...\n', datetime.now())