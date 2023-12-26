#from modules.vector import Vector
import pygame
from modules.physics import *

from math import pi
from time import sleep

r = 16
y = 400
ground = PhysicsGround(400)
wall_left = PhysicsWall(0, PhysicsWall.FACING_RIGHT)
wall_right = PhysicsWall(1120, PhysicsWall.FACING_LEFT)
slab_size = 150, 10
slabs1: list[PhysicsSlab] = []
slabs2: list[PhysicsSlab] = []
slabs3: list[PhysicsSlab] = []
for i in range(6):
    slabs1.append(PhysicsSlab((75 + 224 * i, 300), slab_size, -120))
    slabs2.append(PhysicsSlab((75 + 224 * i, 200), slab_size, 50))
    slabs3.append(PhysicsSlab((75 + 224 * i, 100), slab_size, -50))
slab_rect = pygame.Surface(slab_size)
slab_rect.fill((128, 64, 64))
ball = PhysicsBall((560, 400 - r), r)
#ball.temp(ground)
FPS=180;pygame.init();screen = pygame.display.set_mode(size = (1120, 630));picture = pygame.image.load(".\\ball.png").convert_alpha();picture_blue=pygame.image.load(".\\ball.png").convert_alpha()
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
    ball.tick(1 / FPS, (ground, wall_left, wall_right, *slabs1, *slabs2, *slabs3), bounce=bounce)
    for slab in slabs1 + slabs2 + slabs3:
        slab.tick(1 / FPS)
    if (posx := slabs1[0].position.x) < -75:
        slabs1.append(PhysicsSlab((posx + 1344, 300), slab_size, -120))
        slabs1.pop(0)
    if (posx := slabs2[-1].position.x) > 1195:
        slabs2.insert(0, PhysicsSlab((posx - 1344, 200), slab_size, 50))
        slabs2.pop()
    if (posx := slabs3[0].position.x) < -75:
        slabs3.append(PhysicsSlab((posx + 1344, 100), slab_size, -50))
        slabs3.pop(0)
    '''
    if (posx := slabs2[-1].position.x) > 1195:
        slabs2.insert(0, PhysicsSlab((posx - 1344, 200), slab_size, -50))
        slabs2.pop()'''

    screen.fill((255, 255, 255))
    if ball.bounceable:
        rot = pygame.transform.rotate(picture, ball.rad_angle * (180 / pi))
    else:
        rot = pygame.transform.rotate(picture_blue, ball.rad_angle * (180 / pi))
    pygame.draw.line(screen, (0, 0, 0), (-1120, 400), (2240, 400), 2)
    screen.blit(rot, (ball.position[0] - rot.get_size()[0] // 2, ball.position[1] - rot.get_size()[1] // 2))
    for slab in slabs1 + slabs2 + slabs3:
        screen.blit(slab_rect, (Vector(slab.position) - Vector(slab.size) / 2).inttuple)
    pygame.display.update()