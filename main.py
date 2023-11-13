from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import psycopg2
import json
from sys import argv
from datetime import datetime
import requests
import time


class S(BaseHTTPRequestHandler):

    def _get_connection_database(self):
        config = None
        try:
            with open("./_config", 'r', encoding='utf-8') as f:
                config =  {x.strip().split('=')[0]:x.strip().split('=')[1] for x in f.readlines()}
                logging.info("%s - Read config.txt", datetime.now())
        except:
            logging.error("%s - config.txt file is missing", datetime.now())
        if config:
            try:
                connection = psycopg2.connect(host=config['HOST'], port=int(config['PORT']), \
                                        dbname=config['NAME_DATABASE'], user=config['USER'], password=config['PASSWORD'])
                logging.info("%s - Database connection successful", datetime.now())
                return connection
            except:
                logging.error("%s - Can`t establish connection to database", datetime.now())
                self._set_response(2)
    
    def _get_parameters(self, method):
        parameters = {}
        if method == "POST":
            if self.path == '/parse':
                parameters = {'page': 0, 'per_page': 100}
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length) 
                data_in_post = json.loads(post_data.decode('utf-8'))
                if len(post_data) != 0 and ('profession' in  data_in_post \
                                            or 'city_id' in data_in_post \
                                            or 'date' in data_in_post):
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
                    except:
                        logging.info("%s - The 'date' parameter is not specified", datetime.now())
                    logging.info("%s - Parameters collected for parsing", datetime.now())
                    return parameters
                else:
                    logging.error("%s - Missing parameters in json format (profession, city_id, date)", datetime.now())
                    self._set_response(4)
                    return
        elif method == "GET":
            try:
                parameters = { x[:x.find('=')]:x[x.find('=')+1:] for x in self.path[self.path.find('?')+1:].split(sep='&')}
                logging.info("%s - Parameters collected for the get request", datetime.now())
            except:
                logging.info("%s - Not parameters for sql script", datetime.now())
                

        
    def _set_response(self, code):
        response = 200
        header = ['Content-type', 'text/html']
        message = ''
        if code == 1:
            message = "Successful request for {}".format(self.path)
        elif code == 2:
            response = 500
            message = "Can`t establish connection to database"
        elif code == 3:
            response = 404
            message = "Command error.The post method only has a task for data parsing.(/parse)"
        elif code == 4:
            response = 500
            message = "Missing parameters in json format (profession, city_id, date)" 
        elif code == 5:
            response = 500
            message = "API HH not available" 
        self.send_response(response)
        self.send_header(header[0], header[1])
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))
    
    def _get_url_vacancy_in_page(self, parameters):
        logging.info('%s - Get search pages with parameters %s', datetime.now(), parameters)
        req_page = requests.get('https://api.hh.ru/vacancies', parameters)
        if req_page.status_code == 200:
            data_in_page = json.loads(req_page.content.decode())
            req_page.close()
            logging.info("%s - Page received", datetime.now())
            return data_in_page['items']['url']
        else:
            req_page.close()
            logging.error("%s - API HH not available %s -- %s", datetime.now(), req_page.status_code, req_page.text)
            self._set_response(5)
            return
    
    def _get_data_in_vacancy(self, url):
        logging.info('%s - Receiving data from a link: %s', datetime.now(), url)
        req_vacancy = requests.get(url)
        result = {}
        if req_vacancy.status_code == 200:
            data_in_vacancy = json.loads(req_vacancy.content.decode())
            req_vacancy.close()
            result["vacancy_id"] = data_in_vacancy['id']
            logging.info('%s - vacancy_id = %s', datetime.now(), result["vacancy_id"])
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
            return result
        else:
            logging.error("%s - Error captcha required!", datetime.now())
            req_vacancy.close()
            return

    def _load_data(connection, vacancy):
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

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response(1)

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))
        connection = self._get_connection_database()
        if connection:
            if self.path == '/parse':
                parameters_for_parse = self._get_parameters("POST")
                if parameters_for_parse:  
                    logging.info("%s - Start parse...", datetime.now())
                    for page in range(0, 2):
                        parameters_for_parse['page'] = page
                        url_in_page = self._get_url_vacancy_in_page(parameters_for_parse)
                        for url in url_in_page:
                            vacancy = self._get_data_in_vacancy(url)
                            if vacancy:
                                self._load_data(connection, vacancy)
                            time.sleep(0.25)
                            logging.info("%s - Parser sleep...", datetime.now())
                    logging.info("%s - Parse successful!", datetime.now())            
            else:
                logging.error("%s - Command error.The post method only has a task for data parsing.(/parse)", datetime.now())
                self._set_response(3)
            connection.close()
            logging.info("%s - Connection to database closed", datetime.now())



def run(server_class=HTTPServer, handler_class=S, port=80):
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
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
    