import time # модуль для работы со временем, нужен, чтобы замерить время выполнения программы

import psycopg2 as ps # модуль для работы с БД PostgreSQL
import threading # модуль для реализации многопоточности в программах.

DB_NAME = 'demo'
DB_USER = 'postgres'
DB_PASSWORD = '123'
DB_HOST = 'localhost'
OPTS = f'-c search_path=bookings'

class Cursor:
    def __init__(self, count):
        self.mutex = threading.Lock() # блокировка, которая на время работы потока с ресурсом закрывает последний от других обращений
        self.pos = 0 # на какой позиции мы находимся
        self.count = count # количество строк в БД

    # потоко-безопасное получение следующего индекса
    def next(self):
        pos = None
        with self.mutex:
            if self.pos < self.count:
                self.pos += 1
                pos = self.pos
                # чтобы пользователь видел, на каком шаге программа, будем выводить в консоль на какой мы позицию с шагом в 10.000
                if pos % 10000 == 0: 
                    print(pos)

        return pos

# подключаемся к БД
def get_connection():
    return ps.connect(dbname=DB_NAME, user=DB_USER,
                    password=DB_PASSWORD, host=DB_HOST, options=OPTS)


def thread_worker(cursor, thread_id, flush=False):
    # открываем соединение для каждого потока
    conn = get_connection()
    ps_cursor = conn.cursor()
    file = open('res_' + str(thread_id) + '_' + str(flush), 'w') #  создадим файл для записи с именем res_Номер потока_False
    while pos := cursor.next():
        ps_cursor.execute(f'SELECT * FROM ticket_flights_tmp WHERE id={pos}') 
        row = ps_cursor.fetchone() # возвращает первую запись.
        res = ""
        for a in row:
            res += str(a) + " "
        file.write(res + str(thread_id) + "\n")
        if flush:
            file.flush() # очистить выходной буфер и переместить буферизованные данные на диск
# при первом прохождениии передаем параметр False, чтобы не попасть в условие, во 2м true

    file.close()
    ps_cursor.close()
    conn.close()

def get_rows_count(conn):
    ps_cursor = conn.cursor()
    ps_cursor.execute('SELECT count(id) FROM ticket_flights_tmp')
    cnt = ps_cursor.fetchone()
    ps_cursor.close()

    return cnt[0]

# вычисляем время для 10 потоков
def calculate_time_exec(flush=False, threads_count=10):
    conn = get_connection()
    raws_count = get_rows_count(conn)
    conn.close()

    print('rows count:', raws_count)
    cursor = Cursor(raws_count)

    threads = []
    for i in range(threads_count):
        threads.append(threading.Thread(target=thread_worker, args=(cursor, i, flush)))
# append используется для создания потока с помощью целевой функции

    exec_time_start = time.time() # время, выраженное в секундах с начала эпохи.
    for thread in threads:
        thread.start() # запуск потока

    for thread in threads:
        thread.join() # приостанавливает выполнение текущего потока до тех пор, пока не завершится другой поток.

    exec_time_end = time.time() - exec_time_start # определяем, сколько прошло времени

    return exec_time_end


if __name__ == '__main__':
    print('Executing non-flush, 10 threads')
    print('  execution time:', calculate_time_exec(), 's')
    print('Executing flush, 10 threads')
    print('  execution time:', calculate_time_exec(True), 's')
