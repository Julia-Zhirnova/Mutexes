# Mutexes
____
- [X] Изучить самостоятельно методы синхронизации потоков(мьютексы, семафоры, критические секции)
- [X] Сгенерировать таблицу в БД с большим количеством уникальных строк(1 045 726)
- [X] В одной программе(выбран язык программирования Python) в 10 потоков
    - [X]   считать данные из таблицы
    - [X]   дополнить считанные данные номером потока
    - [X]   записать считанные данные и номер потока в файл(отдельный файл для каждого потока)
    - [X]   Замерить время выполнения программы
- [X] Записанные данные в файлах не должны пересекаться
- [X] Повторить п.3, используя синхронную запись в файл (сбрасывать на диск содержимое файла при каждой записи, не полагаться на буфер)
____
<br/> Для выполнения задания мы используем готовую таблицу ticket_flights_tmp, в которой 1 045 726 записей. Для доступа к ней нам нужно зайти через пользователя postgres(DB_USER), пароль 123 (DB_PASSWORD), подключиться к базе данных demo (DB_NAME) и чтобы при обращении к объектам не указывать явно имя схемы bookings.flights, предварительно изменить конфигурационный параметр search_path. (OPTS). Подключаемся локально (DB_HOST = 'localhost') Структура базы данных представлена на скриншоте 1 и пример первых 10 записей на скриншоте 2. Для ее создания использовались следующие команды: </br> 
```sql
su - postgres
qwerty
./pg_start
psql -d demo
SET search_path TO bookings;
CREATE TEMP TABLE ticket_flights_tmp AS SELECT * FROM ticket_flights WITH DATA;
ALTER TABLE ticket_flights_tmp ADD COLUMN id SERIAL PRIMARY KEY;
\d ticket_flights_tmp
```
![image](https://user-images.githubusercontent.com/52165649/139704383-f77b5b5c-dc28-4f5a-b5aa-971fcdf7e116.png)
<br/> Скриншот 1. Структура БД. </br> 
```sql
SELECT * FROM ticket_flights_tmp limit 10;
```
![image](https://user-images.githubusercontent.com/52165649/139704418-fc2b173c-3262-4818-9056-653a098e2a94.png)
<br/> Скриншот 2. Первые 10 записей. </br> 
<br/> Проверяем количкство строк: </br> 
```sql
demo=# SELECT count(*) FROM ticket_flights_tmp;
count
-------—
1045726
(1 строка)
```
____
<br/> Для работы с PostgreSQL импортируем модуль psycopg2 и подключимся функцией `ps.connect`. </br> 
____
<br/> Далее создадим класс `Cursor`, при инициализации которого вызывается блокировка потока, обнуляется позиция и передается количество строк в базе. Для потоко-безопасного получения следующего индекса напишем функцию `next`, которая смещает счетчик позиции на 1, пока мы не пройдем по всем строкам базы. Чтобы пользователь видел, на каком шаге программа, будем выводить в консоль на какой мы позицию с шагом в 10.000. Пример вывода на экран на скриншоте 3 </br> 
![image](https://user-images.githubusercontent.com/52165649/139705441-47d4c4d2-a54f-49b8-843f-c87e5496e008.png)
<br/> Скриншот 3. вывод на экран прохождения записей. </br> 
____
<br/> В функции `thread_worker` опишем работу с потоками. Подключаемся для каждого потока к нашей БД, определяем нашу позицию с помощью класса `Cursor` и создадим файл для записи с именем res_Номер потока_False, где False означает, что вначале рассматривается использование буфера. Пока мы проходим по всем строкам с помощью запроса `SELECT * FROM ticket_flights_tmp WHERE id={pos}`. Метод `.fetchone()` возвращает первую запись, полученную при запросе и мы записываем ее в файл в виде
```
0005432159776 30625 Business 42100.00 1 0
Номер билета Номер рейса Класс Цена Номер строки Номер потока.
```
Файл False приведен на скриншоте 4.</br> 
![image](https://user-images.githubusercontent.com/52165649/139705761-fe527094-819e-4bbd-abfc-451ca3198360.png)
<br/> Скриншот 4. Файл res_0_False. </br> 
<br/>Когда мы не используем буфер, строки сначала записываются во все 10 файлов, потом 11 снова записывается в первый файл. Функция `flush` очищает выходной буфер и перемещает буферизованные данные на диск. Мы создали условие `if flush:` (чтобы использовать ее только во 2м случае, когда передадим параметр True). В этом случае сначала все строки записываются в 0й файл, потом переходят к 1му и так далее. Файл True приведен на скриншоте 5.
![image](https://user-images.githubusercontent.com/52165649/139706054-d7431874-1539-4d35-aaa1-636ca56dca8b.png)
<br/> Скриншот 5. Файл res_0_True. </br> 
<br/>После этого с помощью метода `.close()` закрываем файлы и соединение </br> 
____
<br/>Чтобы определить сколько строк в нашей таблице, напишем функцию `get_rows_count`, которая использует запрос `SELECT count(id) FROM ticket_flights_tmp` </br> 
____
<br/>Далее нам нужна функция `calculate_time_exec` для вычисления времени выполнения всех 10 потоков. Нам понадобится модуль `time` и метод `.time()`, чтобы получить время, выраженное в секундах с начала эпохи в начале работы программы и в конце, разница нам даст время обработки потоков. Указываем, что у нас 10 потоков мы пишем цикл, в котором с помощью метода .append() создаем потоки с помощью целевой функции `thread_worker`, описанной выше. И выводим в консоль результат работы программы (скриншоты 6 и 7).</br> 
![image](https://user-images.githubusercontent.com/52165649/139706887-173bc5de-75bb-4e35-bb06-d71e24cae93a.png) ![image](https://user-images.githubusercontent.com/52165649/139706523-e1387b85-01f7-47bb-a56c-d1c2a95990a7.png)
<br/> Скриншот 6. Используем буфер.                         Скриншот 7. Не используем буфер. </br> 
____
Первое прохождение 183.1251289844513 s Второе прохождение 189.37589025497437 s Время увеличилось на 6,25с, или на 3,4%, так как мы уведомляем систему что надо записать на диск, и не использовать буфер. В данной работе при создании потоков, для блокировки общих данных от одновременного доступа использовались такие объекты синхронизации, как мютексы( `self.mutex = threading.Lock()` ),
____
Прикрепляем код с комментариями `main.py` и результирующие файлы.

