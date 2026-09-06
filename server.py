from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import time

# Створюємо TCP-сокет сервера
sock = socket(AF_INET, SOCK_STREAM)
sock.bind(('localhost', 8080))   # прив'язуємось до локальної адреси і порту 8080
sock.listen(5)                    # слухаємо вхідні підключення, черга очікування - до 5
sock.setblocking(False)           # неблокуючий режим - accept() не зупинить сервер, якщо немає нових клієнтів

players = {}     # словник {conn: {'id', 'x', 'y', 'r', 'name'}} - стан кожного підключеного гравця
conn_ids = {}    # словник {conn: id} - відповідність з'єднання його id (дублює players[conn]['id'])
id_counter = 0   # лічильник для видачі унікальних id новим гравцям


def handle_data():
    """
    Основний ігровий цикл сервера, що виконується в окремому потоці.
    На кожній ітерації:
      1) читає нові координати від усіх гравців,
      2) перевіряє, хто кого "з'їв",
      3) розсилає кожному клієнту оновлений стан усіх інших гравців.
    Винесено в окремий потік, щоб paralельно з цим головний потік міг
    приймати нові вхідні підключення через accept().
    """
    global id_counter
    while True:
        time.sleep(0.01)  # невелика затримка, щоб не навантажувати CPU у холостому циклі (~100 разів/сек)

        player_data = {}  # тимчасовий "знімок" стану гравців, що надіслали дані саме в цій ітерації
        to_remove = []    # з'єднання, які потрібно прибрати з players наприкінці ітерації (відключились/програли)

        # ---- Крок 1: читаємо нові дані від усіх підключених гравців ----
        for conn in list(players):  # list(...) - копія ключів, щоб безпечно можна було змінювати players під час цього циклу далі
            try:
                data = conn.recv(64).decode().strip()
                if ',' in data:
                    parts = data.split(',')
                    if len(parts) == 5:
                        # Розбираємо повідомлення клієнта: "id,x,y,radius,name"
                        pid, x, y, r = map(int, parts[:4])
                        name = parts[-1]
                        players[conn] = {'id': pid, 'x': x, 'y': y, 'r': r, 'name': name}
                        player_data[conn] = players[conn]  # додаємо в "активний" знімок цього тіку
            except:
                # Немає нових даних (неблокуючий сокет) або клієнт ще нічого не надіслав - пропускаємо
                continue

        # ---- Крок 2: перевіряємо зіткнення між гравцями, що оновились у цьому тіку ----
        eliminated = []  # список "з'їдених" у цій ітерації з'єднань
        for conn1 in player_data:
            if conn1 in eliminated: continue  # вже з'їдений раніше в цьому ж циклі - пропускаємо
            p1 = player_data[conn1]
            for conn2 in player_data:
                if conn1 == conn2 or conn2 in eliminated: continue
                p2 = player_data[conn2]

                # Відстань між центрами двох гравців (без hypot, вручну через теорему Піфагора)
                dx, dy = p1['x'] - p2['x'], p1['y'] - p2['y']
                distance = (dx**2 + dy**2)**0.5

                # Умова "з'їдання": кола перетинаються, і p1 більший за p2 щонайменше на 10%
                # (запобігає ситуації, коли майже однакові за розміром гравці з'їдають одне одного одночасно)
                if distance < p1['r'] + p2['r'] and p1['r'] > p2['r'] * 1.1:
                    p1['r'] += int(p2['r'] * 0.5)  # переможець отримує половину радіуса з'їденого
                    players[conn1] = p1            # одразу зберігаємо оновлений розмір у загальний стан
                    eliminated.append(conn2)       # програвця позначаємо на видалення

        # ---- Крок 3: розсилаємо кожному клієнту актуальний список інших гравців ----
        for conn in list(players.keys()):
            if conn in eliminated:
                # Гравця з'їли - повідомляємо його клієнту про поразку і готуємо до видалення
                try:
                    conn.send("LOSE".encode())
                except:
                    pass
                to_remove.append(conn)
                continue

            try:
                # Формуємо пакет з даними всіх гравців, КРІМ самого одержувача і з'їдених.
                # Формат: "id,x,y,r,name|id,x,y,r,name|" (з завершальним '|' в кінці)
                packet = '|'.join([f"{p['id']},{p['x']},{p['y']},{p['r']},{p['name']}"
                                   for c, p in players.items() if c != conn and c not in eliminated]) + '|'
                conn.send(packet.encode())
            except:
                # Не вдалось надіслати (клієнт відключився чи інша помилка) - готуємо до видалення
                to_remove.append(conn)

        # ---- Крок 4: прибираємо відключених/з'їдених гравців зі спільних словників ----
        for conn in to_remove:
            players.pop(conn, None)
            conn_ids.pop(conn, None)


# Запускаємо ігровий цикл у фоновому потоці одразу при старті сервера
Thread(target=handle_data, daemon=True).start()
print("SERVER running...")

# ---- Головний потік: постійно приймає нові підключення клієнтів ----
while True:
    try:
        conn, addr = sock.accept()          # приймаємо нове TCP-з'єднання (не блокує через setblocking(False))
        conn.setblocking(False)             # робимо неблокуючим і клієнтський сокет теж
        id_counter += 1
        # Реєструємо нового гравця зі стартовими параметрами: позиція (0,0), радіус 20, ім'я поки невідоме
        players[conn] = {'id': id_counter, 'x': 0, 'y': 0, 'r': 20, 'name': None}
        conn_ids[conn] = id_counter
        # Надсилаємо клієнту його стартові дані: "id,x,y,radius"
        conn.send(f"{id_counter},0,0,20".encode())
    except:
        # Немає нових підключень у цей момент (неблокуючий accept) - просто продовжуємо цикл
        pass