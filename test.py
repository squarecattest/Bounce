import pygame

FPS = 60
dt = 1 / FPS
g = -9.8 * 6

pygame.init()
pygame.display.set_mode((1120, 630))
screen = pygame.display.set_mode(size = (1120, 630), flags = pygame.RESIZABLE)
class Ball:
    def __init__(self, pos, size):
        self.pos = pos
        self.size = size
        self.vx = 0
        self.vy = 0
        self.onground = True

    @property
    def x(self):
        return self.pos[0]
    @property
    def y(self):
        return self.pos[1]
    
    @x.setter
    def x(self, x):
        self.pos = (x, self.y)
    @y.setter
    def y(self, y):
        self.pos = (self.x, y)

    def update(self):
        if not self.onground:
            self.y -= self.vy
            if self.y + self.size >= 400:
                self.y = 400 - self.size
                self.rebounce()
                return
            self.vy += g * dt
        self.x += self.vx
        if self.vx > 0:
            self.vx -= 1
            if self.vx < 0:
                self.vx = 0
        elif self.vx < 0:
            self.vx += 1
            if self.vx > 0:
                self.vx = 0

    def hit(self, dir: bool):
        self.vx = 40 * dir - 20

    def rebounce(self):
        self.vy = abs(self.vy) / 1.5 - 1
        if self.vy < 0:
            self.vy = 0
            self.onground = True

    def bounce(self):
        self.vy = 20
        self.onground = False
            
    def render(self, screen: pygame.Surface):
        pygame.draw.circle(screen, (255, 128, 128), (int(self.x), int(self.y)), self.size)
        
ball = Ball((560, 380), 20)
while True:
    pygame.time.Clock().tick(FPS)
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.KEYDOWN:
            key = event.__dict__.get("key")
            if key == pygame.K_SPACE:
                ball.bounce()
            elif key == pygame.K_LEFT:
                ball.hit(False)
            elif key == pygame.K_RIGHT:
                ball.hit(True)

    screen.fill((255, 255, 255))
    ball.update()
    ball.render(screen)
    pygame.draw.line(screen, (0, 0, 0), (0, 400), (1120, 400), 2)
    pygame.display.update()
        