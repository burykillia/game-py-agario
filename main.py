from pygame import *
from random import randint
from pygame.examples.sprite_texture import clock

#Класс для їжі
class Food:
    def __init__(self, x, y , r ,c):
        self.x = x
        self.y = y
        self.r = r
        self.c = c
    #def check_collision(self, player_x, player_y, player_r):


#Створення базового вікна і гравця
init()
my_player = [0, 0, 20]
window = display.set_mode((1000, 1000))
clock = time.Clock()
eats = [Food(randint(-2000, 2000), randint(-2000, 2000), 10, (randint(0,255), randint(0,255), randint(0,255)))]
running = True

#Ігровий цикл
while running:
    for e in event.get():
        if e.type == QUIT:
            running = False
    window.fill("Grey")
    scale = max(0.3, min(50 / my_player[2], 1.5))
    draw.circle(window, (0,255,0), (my_player[0]+500,my_player[1]+500), int(my_player[2]*scale))
    keys = key.get_pressed()
    if keys[K_w]: my_player[1] -= 15
    if keys[K_s]: my_player[1] += 15
    if keys[K_a]: my_player[0] -= 15
    if keys[K_d]: my_player[0] += 15

    for eat in eats:
        sx = int((eat.x - my_player[0]) * scale + 500)
        sy = int((eat.y - my_player[1]) * scale + 500)
        draw.circle(window, eat.c, (sx, sy), eat.r)
    display.update()
    clock.tick(60)

quit()