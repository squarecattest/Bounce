import pygame
from modules.physics import PhysicsBall, PhysicsGround, PhysicsSlab, PhysicsWall
from modules import vector
from math import pi
from time import sleep
r = 26
y = 400
ground = PhysicsGround(400)
wall_left = PhysicsWall(0, PhysicsWall.FACING_RIGHT)
wall_right = PhysicsWall(1120, PhysicsWall.FACING_LEFT)
slab_size = 150, 10
slabs1: list[PhysicsSlab] = []
slabs2: list[PhysicsSlab] = []
for i in range(6):
    slabs1.append(PhysicsSlab((75 + 224 * i, 300), slab_size, -50))
    slabs2.append(PhysicsSlab((75 + 224 * i, 200), slab_size, 50))
slab_rect = pygame.Surface(slab_size)
slab_rect.fill((128, 64, 64))
ball = PhysicsBall((560, 400 - r), r)
ball.temp(ground)
FPS=180;pygame.init();screen = pygame.display.set_mode(size = (1120, 630));picture = pygame.image.load(".\\test_circle.png").convert_alpha()
while True:
    pygame.time.Clock().tick(FPS)
    events = pygame.event.get()
    bounce = False
    for event in events:
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.KEYDOWN:
            key = event.__dict__.get("key")
            bounce = key == pygame.K_SPACE
    ball.tick(1 / FPS, (ground, wall_left, wall_right, *slabs1, *slabs2), bounce=bounce)
    for slab in slabs1 + slabs2:
        slab.tick(1 / FPS)
    if (posx := slabs1[0].position.x) < -75:
        slabs1.append(PhysicsSlab((posx + 1344, 300), slab_size, -50))
        slabs1.pop(0)
    if (posx := slabs2[-1].position.x) > 1195:
        slabs2.insert(0, PhysicsSlab((posx - 1344, 200), slab_size, 50))
        slabs2.pop()

    screen.fill((255, 255, 255))
    rot = pygame.transform.rotate(picture, ball.angle * (180 / pi))
    pygame.draw.line(screen, (0, 0, 0), (-1120, 400), (2240, 400), 2)
    screen.blit(rot, (ball.position[0] - rot.get_size()[0] // 2, ball.position[1] - rot.get_size()[1] // 2))
    for slab in slabs1 + slabs2:
        screen.blit(slab_rect, (slab.position - vector.Vector(slab_size) / 2).inttuple)
    
    pygame.display.update()

exit()
def init():
    global ball, k
    ball = PhysicsBall((560, 400 - r), r)
    ball.x = 560
    ball.y = 400 - r
    ball.a = 0

    ball.vx = 0 #純動
    ball.w = -20
    k = 60
    k = -1#
RELATIVE_SCALE, RELATIVE_OFFSET = 0.96, 0.01 #0.95 ~ 0.99
ABSOLUTE_SCALE, ABSOLUTE_OFFSET = 0.99, 0.1#
def a():
    v_ground = -ball.vx
    v_ball = ball.w * r
    v_avr = (v_ground + v_ball) / 2
    v_ground = approach(v_ground, v_avr, RELATIVE_SCALE, RELATIVE_OFFSET)
    v_ball = approach(v_ball, v_avr, RELATIVE_SCALE, RELATIVE_OFFSET)
    ball.vx = -v_ground
    ball.w = v_ball / r
    
    ball.vx = approach(ball.vx, 0, ABSOLUTE_SCALE, ABSOLUTE_OFFSET)
    ball.w = approach(ball.w, 0, ABSOLUTE_SCALE, ABSOLUTE_OFFSET / r)

def sign(v):
    if v>0: return 1
    if v<0: return -1
    return 0
    
def approach(value, v_c, scale, offset):
    diff = (value - v_c) * scale
    if abs(diff) < offset:
        return v_c
    return v_c + diff - offset * sign(diff)


FPS=60;pygame.init();screen = pygame.display.set_mode(size = (1120, 630), flags=pygame.RESIZABLE);picture = pygame.image.load(".\\test_circle.png").convert_alpha()
init()
while True:
    pygame.time.Clock().tick(FPS)
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.KEYDOWN:
            if k == 0:
                k -= 1
            else:
                init()
    if k > 0:
        k -= 1
    if k != 0:
        ball.x += ball.vx * 1/FPS
        ball.a += ball.w * (180/pi) * 1/FPS
    if k < 0:
        a()
    screen.fill((255, 255, 255))
    rot = pygame.transform.rotate(picture, ball.a)
    pygame.draw.line(screen, (0, 0, 0), (-1120, 400), (2240, 400), 2)
    screen.blit(rot, (ball.x - rot.get_size()[0] // 2, ball.y - rot.get_size()[1] // 2))
    
    pygame.display.update()

exit()
from itertools import cycle
FPS = 60
screen = pygame.display.set_mode(size = (1120, 630))
picture = pygame.image.load(".\\test_circle.png").convert_alpha()
print(picture.get_size())
angle = 0
a = cycle(tuple(range(128, 256)) + tuple(reversed(range(128, 256))))
while True:
    pygame.time.Clock().tick(FPS)
    events = pygame.event.get()
    angle += 1
    for event in events:
        if event.type == pygame.QUIT:
            exit()

    screen.fill((next(a), 255, 255))
    rot = pygame.transform.rotate(picture, angle)
    print(rot.get_size())
    screen.blit(rot, (560 - rot.get_size()[0] // 2, 200 - rot.get_size()[1] // 2))
    pygame.display.update()