from datetime import datetime

with open('test.txt', 'a+', encoding='utf-8') as file:
    file.write(datetime.today().strftime('%Y-%m-%d-%H-%M-%S') + '\n')