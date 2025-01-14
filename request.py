from threading import Thread
from sys import argv
import requests
import datetime

def make_request(host_name: str, request_info: dict):

    #Пытаемся додолбиться до хоста
    try:
        #Замеряем выремя запроса
        start = datetime.datetime.now()
        response = requests.get(host_name)
        duration = (datetime.datetime.now() - start).microseconds/1000

    #Если ресурс по данному хосту не найден
    except requests.exceptions.InvalidSchema:
        request_info['Errors'] += 1

    #Перехватываем неизвестную ошибку
    except Exception:
        print(f'Непредвиденная ошибка при запросе по адресу: {host_name}!')
        request_info['Errors'] += 1

    else:
        #Выполняем все условности
        if duration < request_info['Min']:
            request_info['Min'] = duration

        if duration > request_info['Max']:
            request_info['Max'] = duration

        request_info['Avg'] += duration

        #Просматриваем коды
        #print(f'Код запроса к {host_name}: {response.status_code}')###Убарть потом!!!
        if response.status_code // 100 in [4, 5]:
            request_info['Failed'] += 1

        else:
            request_info['Success'] += 1

    return


#Выполнение запросов и их иссленование
def test_requests(host_name: str, request_count: int, hosts_info:list) -> dict:

    #Структура для хранения сведений об опериции ping
    request_info = {'Host_name': host_name, 'Success': 0, 'Failed': 0, 'Errors': 0, 'Min': float('inf'), 'Max': 0, 'Avg' :0}

    #Инициализируем потоки
    threads = [Thread(target=make_request, args=(host_name, request_info,)) for _ in range(request_count)]

    #Запускаем потоки
    for thread in threads:
        thread.start()

    #Отлавливаем потоки
    for thread in threads:
        thread.join()

    #Вычисляем среденее время запроса
    request_info['Avg'] = round(request_info['Avg']/request_count, 3)

    hosts_info.append(request_info)

    #return request_info
    return


#Получение хостов из файлов
def get_hosts_from_files(input_file_name: list[str]) -> list[str]:

    hosts = []

    for file_name in input_file_name:

        #Пробуем открывать файл
        try:
            file = open(file_name, 'r')

        #Если файл не существует
        except FileNotFoundError:
            print(f'Файл {file_name} не найден!')

        #Перехватываем неизвестную ошибку
        except Exception:
            print(f'Непредвиденная ошибка при чтении из файла: {file_name}!')

        else:
            #Проходимся по стркам
            for line in file.readlines():
                hosts += line.strip().split(',')

            file.close()        

    return hosts

#Проверка формата адресов
def check_host_format(host_name: str)->bool:
    
    if host_name[:8] != 'https://' and host_name[:7] != 'http://':
        return False
    
    if len(host_name[8:].split('.')) != 2:
        return False
    
    return True


#Значения по умолчанию
request_count = 1
hosts = None
input_file_name = None
output_file_name = None


#Вытаскиваем параметры
for i in range(1, len(argv) - 1):

    #Хосты
    if argv[i] == '-H' and hosts == None:
        hosts = argv[i + 1].split(',')

        #Проверка на заполенние флага
        if hosts[0][0] == '-':
            print(f'Некорректно задан адрес: {argv[i + 1]}!')
            hosts = None

    #Кол-во запросов
    elif argv[i] == '-C':
        try:
            request_count = int(argv[i + 1])
        except ValueError:
            print(f'Некорректно задано кол-во запросов: {argv[i + 1]}, установлено значение по умолчанию (1)!')

    #Названия входных файлов
    elif argv[i] == '-F' and input_file_name == None and hosts == None :
        input_file_name = argv[i + 1].split(',')

        #Проверка на заполенние флага
        if input_file_name[0][0] == '-':
            print(f'Некорректно задано имя входного файла: {argv[i + 1]}!')
            input_file_name = None

    #Названия выходных файлов
    elif argv[i] == '-O' and output_file_name == None:
        output_file_name = argv[i + 1]

        #Проверка на заполенние флага
        if output_file_name[0][0] == '-':
            print(f'Некорректно задано имя выходного файла: {argv[i + 1]}!')
            output_file_name = None


#Если считываем из файлов
if input_file_name != None:
    print('Читаем адреса из файлов...')
    hosts = get_hosts_from_files(input_file_name)

#Проверяем формат адресов
for host in hosts:
    if not check_host_format(host):
        print(f'Адрес {host} не удовлетоворяет шаблону!')
        hosts.remove(host)

hosts_info = []

#Пытаемся получть доступ к адресу
try:
    #Инициализируем потоки
    #Кидаем запросы на каждый хост из hosts
    threads = [Thread(target=test_requests, args=(hosts[i], request_count, hosts_info,)) for i in range(len(hosts))]

    #Запускаем потоки
    for thread in threads:
        thread.start()

    #Отлавливаем потоки
    for thread in threads:
        thread.join()

#Если флаг не заполнен
except TypeError:
    print(f'Не найдено ни одного адреса для проверки!')


#Выводим результат
if output_file_name != None:

    with open(output_file_name, 'w') as file:

        for host in hosts_info:
            file.write(f"\tHost: {host['Host_name']}\nSuccess: {host['Success']}\nFailed: {host['Failed']}\nErrors: {host['Errors']}\nMin: {host['Min']}\nMax: {host['Max']}\nAvg: {host['Avg']}\n")

    print(f'Результат записан в файл!')

else:
    for host in hosts_info:
        print(f"\tHost: {host['Host_name']}\nSuccess: {host['Success']}\nFailed: {host['Failed']}\nErrors: {host['Errors']}\nMin: {host['Min']}\nMax: {host['Max']}\nAvg: {host['Avg']}")