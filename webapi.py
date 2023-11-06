from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import psycopg2
from psycopg2 import Error
import requests
import json
from datetime import datetime, date
import time
from bson.json_util import dumps

POSTGRES_HOST = 'localhost'
POSTGRES_PORT = 5432
POSTGRES_DB = 'stand-db'
POSTGRES_USER = 'postgres'
POSTGRES_PASSWORD = 'postgres'

class S(BaseHTTPRequestHandler):
    def _set_response(self, code=200):
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    
    def get_connection_db(self):
        try:
            conn = psycopg2.connect(dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST)
            logging.info("%s - Database connection successful", datetime.now())
            return conn
        except:
            logging.error("%s - Can`t establish connection to database", datetime.now())


    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        if self.path.startswith('/metrics'):
            params = {}
            try:
                params = { x[:x.find('=')]:x[x.find('=')+1:] for x in self.path[self.path.find('?')+1:].split(sep='&')}
                logging.info(params)
            except:
                logging.info("%s - Not parameters for sql script", datetime.now())
            result = None
            try:
                logging.info("%s - Getting data from the database")
                connection = self.get_connection_db()
                cursor = connection.cursor()
                if 'date_from' in params and 'date_to' in params:
                    cursor.execute(f"select * from metrics m where dt between '{params['date_from']}' and '{params['date_to']}';")
                    result = cursor.fetchall()
                elif 'date_from' in params:
                    cursor.execute(f"select * from metrics m where dt >= '{params['date_from']}';")
                    result = cursor.fetchall()
                else:
                    cursor.execute(f"select * from metrics m where dt = '{date.today()}';")
                    result = cursor.fetchall()
            except:
                logging.error("%s - Can`t establish connection to database", datetime.now())
                self._set_response(code=504)
                self.wfile.write("Can`t establish connection to database".encode('utf-8'))
            finally:
                cursor.close()
                connection.close()
                logging.info("Database connection closed")

            if result is not None:
                logging.info("%s - Transforms data")
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
                'fly_in_fly_out_schedule_cnt': x[17]} for x in result]
                js = dumps(result)            
                self._set_response()
                self.wfile.write(js.encode('utf-8'))
                logging.info("%s - Request processed successfully")
            else:
                logging.info("%s There is no data in the database ", datetime.now())

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))
        if self.path == '/parse':
            try:

                data_in_post = json.loads(post_data.decode('utf-8'))
                if len(post_data) != 0 and ('profession' in  data_in_post \
                                            or 'city_id' in data_in_post \
                                            or 'date' in data_in_post):
                    
                    params = {
                            # 'text': f'NAME:{profession}',  # Текст фильтра. В имени должно быть слово "Аналитик"
                            # 'area': city_id,  # Пои ск ощуществляется по вакансиям города Москва
                            'page': 0,  # Индекс страницы поиска на HH
                            'per_page': 100  # Кол-во вакансий на 1 странице
                        }
                    try:
                        profession = data_in_post['profession']
                        logging.info("%s - profession = %s", datetime.now(), profession)
                        params['text'] = f'NAME:{profession}'
                    except:
                        logging.info("%s - The 'profession' parameter is not specified", datetime.now())
                    try:
                        city_id = data_in_post['city_id']
                        logging.info("%s - city_id = %s", datetime.now(), city_id)
                        params['area'] = city_id
                    except:
                        logging.info("%s - The 'city_id' parameter is not specified", datetime.now())
                    try:
                        date_search = data_in_post['date']
                        logging.info("%s - date = %s", datetime.now(), date_search)
                        params['date_from'] = date_search
                        # params['date_to'] = date_search
                    except:
                        logging.info("%s - The 'date' parameter is not specified", datetime.now())
                    logging.info("%s - Start parse...", datetime.now())

                    for page in range(0, 2):
                        params['page'] = page
                        logging.info('%s - Get search pages with parameters %s', datetime.now(), params)
                        req_page = requests.get('https://api.hh.ru/vacancies', params)
                        try:
                            if req_page.status_code == 200:
                                data_in_page = json.loads(req_page.content.decode())
                                req_page.close()
                                for vacancy in data_in_page['items']:
                                    logging.info('%s - Receive data from a vacancy by url %s', datetime.now(), vacancy['url'])
                                    req_vacancy = requests.get(vacancy['url'])
                                    
                                    if req_vacancy.status_code == 200:
                                        data_in_vacancy = json.loads(req_vacancy.content.decode())
                                        req_vacancy.close()
                                        vacancy_id = data_in_vacancy['id']
                                        logging.info('%s - vacancy_id = %s', datetime.now(), vacancy_id)

                                        profession_name = None 
                                        if data_in_vacancy.get('name') != None:
                                            profession_name = data_in_vacancy['name']
                                        logging.info('%s - profession_name = %s', datetime.now(), profession_name)
                                        salary_currency =None
                                        salary_from = None
                                        salary_to = None
                                        if data_in_vacancy.get('salary') != None:
                                            if data_in_vacancy['salary'].get('currency') != None:
                                                salary_currency = data_in_vacancy['salary']['currency']
                                            if data_in_vacancy['salary'].get('from') != None:
                                                salary_from = float(data_in_vacancy['salary']['from'])
                                            if data_in_vacancy['salary'].get('to') != None:
                                                salary_to = float(data_in_vacancy['salary']['to'])
                                        logging.info('%s - salary_currency = %s', datetime.now(), salary_currency)
                                        logging.info('%s - salary_from = %s', datetime.now(), salary_from)
                                        logging.info('%s - salary_to = %s', datetime.now(), salary_to)
                                        experience = None
                                        if data_in_vacancy.get('experience') != None:
                                            if data_in_vacancy['experience'].get('id') != None:
                                                experience = data_in_vacancy['experience']['id']
                                        logging.info('%s - experience = %s', datetime.now(), experience)
                                        shedule = None
                                        if data_in_vacancy.get('schedule') != None:
                                            if data_in_vacancy['schedule'].get('id') != None:
                                                shedule = data_in_vacancy['schedule']['id']
                                        logging.info('%s - shedule = %s', datetime.now(), shedule)
                                        skills = None 
                                        if len(data_in_vacancy.get('key_skills')) != 0:
                                            skills = data_in_vacancy['key_skills']
                                            skills = [ skills[x]['name'] for x in range(0, len(skills))]
                                        logging.info('%s - skills = %s', datetime.now(), skills)
                                        published_dt = None
                                        if data_in_vacancy.get('published_at') != None:
                                            published_dt = data_in_vacancy['published_at']
                                        logging.info('%s - published_dt = %s', datetime.now(), published_dt)
                                        try:
                                            connection = self.get_connection_db()
                                            cursor = connection.cursor()
                                            cursor.execute("call insert_vacancies (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", \
                                                            (int(vacancy_id), int(city_id), profession_name, salary_currency, salary_from, salary_to, experience, shedule, skills, published_dt))
                                            connection.commit()
                                            logging.info("Data added successfully")
                                        except (Exception, Error) as error:
                                            logging.error("%s - Error Postgres: %s", datetime.now(), Error)
                                        finally:
                                            if connection:
                                                cursor.close()
                                                connection.close()
                                                logging.info("Connection to PostgreSQL closed")
                                    else:
                                        logging.error("%s - Error captcha required!", datetime.now())
                                        req_vacancy.close()
                                    
                                    time.sleep(0.25)
                                    logging.info("%s - Parser sleep...", datetime.now())
                            else:
                                logging.error("%s - API HH not available! %s -- %s", datetime.now(), req_page.status_code, req_page.text)
                                self._set_response(code=404)
                                self.wfile.write("Not Found".encode('utf-8'))
                                req_page.close()
                            logging.info("%s - Parse successful!", datetime.now())
                            self._set_response()
                            self.wfile.write("OK".encode('utf-8'))
                        except:
                            logging.error("%s - API HH not available! %s -- %s", datetime.now(), req_page.status_code, req_page.text)
                            self._set_response(code=404)
                            self.wfile.write("Not Found".encode('utf-8'))
                            req_page.close()
                else:
                    logging.error("%s - The '\parse' method must contain at least one argument (profession, city_id, date)", datetime.now())
                    self._set_response(code=500)
                    self.wfile.write("Internal Error".encode('utf-8'))

            except:
                logging.error("%s - Missing parameters in json format (profession, city_id, date)", datetime.now())
                self._set_response(code=500)
                self.wfile.write("Internal Error".encode('utf-8'))
        else:
            logging.error("%s - Command error.The post method only has a task for data parsing.(/parse)", datetime.now())
            self._set_response(code=404)
            self.wfile.write("Not Found".encode('utf-8'))
            # self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))



def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('%s - Starting httpd...\n', datetime.now())
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('%s - Stopping httpd...\n', datetime.now())

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()