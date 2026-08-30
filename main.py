from math import hypot
from socket import socket, AF_INET, SOCK_STREAM
from pygame import *
from threading import Thread
from random import randint

# --- Підключення до сервера ---
sock = socket(AF_INET, SOCK_STREAM)          # створюємо TCP-сокет
sock.connect(('localhost', 8080))            # підключаємось до сервера гри

# Отримуємо початкові дані від сервера: свій id та стартові координати/розмір гравця
my_data = list(map(int, sock.recv(64).decode().strip().split(',')))
my_id = my_data[0]                           # унікальний ідентифікатор гравця
my_player = my_data[1:]                      # [x, y, radius] — позиція та розмір гравця
sock.setblocking(False)                      # переводимо сокет у неблокуючий режим,
                                              # щоб recv() не зупиняв основний цикл гри

# --- Ініціалізація pygame ---
init()
window = display.set_mode((1000, 1000))      # створюємо вікно гри 1000x1000
clock = time.Clock()                         # для контролю FPS
f = font.Font(None, 50)                      # шрифт для тексту (напр. "U lose!")

all_players = []                             # список усіх гравців, отриманих із сервера
running = True                               # прапорець роботи головного циклу
lose = False                                 # прапорець програшу гравця


def receive_data():
   """Функція виконується в окремому потоці й постійно приймає дані від сервера,
   не блокуючи основний ігровий цикл."""
   global all_players, running, lose
   while running:
       try:
           data = sock.recv(4096).decode().strip()
           if data == "LOSE":
               lose = True                   # сервер повідомив, що гравець програв
           elif data:
               # Дані про гравців приходять у форматі "id,x,y,r|id,x,y,r|..."
               parts = data.strip('|').split('|')
               all_players = [
                   list(map(int, p.split(',')))
                   for p in parts
                   if len(p.split(',')) == 4  # перевірка, що запис коректний (4 значення)
               ]
       except:
           pass  # ігноруємо помилки (наприклад, коли даних ще немає — неблокуючий сокет)


# Запускаємо потік прийому даних як daemon (завершиться разом з основною програмою)
Thread(target=receive_data, daemon=True).start()


class Eat:
   """Клас їжі (кружечків), яку може з'їсти гравець для збільшення розміру."""
   def __init__(self, x, y, r, c):
       self.x = x
       self.y = y
       self.radius = r
       self.color = c

   def check_collision(self, player_x, player_y, player_r):
       """Перевіряє, чи гравець торкається цієї їжі (за відстанню між центрами)."""
       dx = self.x - player_x
       dy = self.y - player_y
       return hypot(dx, dy) <= self.radius + player_r


# Генеруємо 300 випадкових об'єктів їжі в межах ігрового поля (-2000..2000)
eats = [Eat(randint(-2000, 2000), randint(-2000, 2000), 10,
           (randint(0, 255), randint(0, 255), randint(0, 255)))
       for _ in range(300)]

# --- Головний ігровий цикл ---
while running:
   # Обробка подій pygame (закриття вікна тощо)
   for e in event.get():
       if e.type == QUIT:
           running = False

   window.fill((255, 255, 255))  # заливаємо фон білим кольором

   # Масштаб камери: чим більший гравець, тим менший масштаб (щоб все влазило в екран)
   scale = max(0.3, min(50 / my_player[2], 1.5))

   # --- Малюємо інших гравців ---
   for p in all_players:
       if p[0] == my_id:
           continue  # себе малюємо окремо нижче
       # Переводимо координати інших гравців у систему координат відносно себе (камера)
       sx = int((p[1] - my_player[0]) * scale + 500)
       sy = int((p[2] - my_player[1]) * scale + 500)
       draw.circle(window, (255, 0, 0), (sx, sy), int(p[3] * scale))

   # --- Малюємо себе завжди в центрі екрана (500, 500) ---
   draw.circle(window, (0, 255, 0), (500, 500), int(my_player[2] * scale))

   # --- Обробка їжі: перевірка з'їдання та відмальовка ---
   to_remove = []
   for eat in eats:
       if eat.check_collision(my_player[0], my_player[1], my_player[2]):
           to_remove.append(eat)                      # позначаємо на видалення
           my_player[2] += int(eat.radius * 0.2)       # збільшуємо розмір гравця
       else:
           # Малюємо їжу з урахуванням позиції камери та масштабу
           sx = int((eat.x - my_player[0]) * scale + 500)
           sy = int((eat.y - my_player[1]) * scale + 500)
           draw.circle(window, eat.color, (sx, sy), int(eat.radius * scale))

   # Видаляємо з'їдену їжу зі списку
   for eat in to_remove:
       eats.remove(eat)

   # Якщо гравець програв — показуємо напис
   if lose:
       t = f.render('U lose!', 1, (244, 0, 0))
       window.blit(t, (400, 500))

   display.update()  # оновлюємо вікно
   clock.tick(60)     # обмежуємо FPS до 60

   # --- Керування гравцем (тільки якщо він не програв) ---
   if not lose:
       keys = key.get_pressed()
       if keys[K_w]: my_player[1] -= 15   # рух вгору
       if keys[K_s]: my_player[1] += 15   # рух вниз
       if keys[K_a]: my_player[0] -= 15   # рух вліво
       if keys[K_d]: my_player[0] += 15   # рух вправо

       # Надсилаємо серверу оновлену позицію та розмір гравця
       try:
           msg = f"{my_id},{my_player[0]},{my_player[1]},{my_player[2]}"
           sock.send(msg.encode())
       except:
           pass  # ігноруємо помилки відправки (напр. розрив з'єднання)

quit()  # завершуємо роботу pygame