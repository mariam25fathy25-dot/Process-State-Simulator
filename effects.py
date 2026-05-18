import pygame, math, random
from collections import deque
from config import lerp, ease_out

class Particle:
    def __init__(self, x, y, col):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(40, 120)
        self.x, self.y = float(x), float(y)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.col  = col
        self.life = random.uniform(0.4, 0.9)
        self.age  = 0.0
        self.r    = random.uniform(2, 5)

    def update(self, dt):
        self.age += dt
        self.vy  += 60 * dt
        self.x   += self.vx * dt
        self.y   += self.vy * dt
        return self.age < self.life

    def draw(self, surf):
        t = 1 - self.age / self.life
        a = int(255 * t)
        r = max(1, int(self.r * t))
        s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.col, a), (r + 1, r + 1), r)
        surf.blit(s, (int(self.x) - r - 1, int(self.y) - r - 1))


class Orb:
    def __init__(self, fp, tp, col):
        self.fp, self.tp = fp, tp
        self.col   = col
        self.p     = 0.0
        self.trail = deque(maxlen=18)
        self.live  = True
        self.x, self.y = fp

    def update(self, dt):
        if not self.live:
            return False
        self.p += dt / 0.5
        if self.p >= 1:
            self.live = False
            return False
        t  = ease_out(self.p)
        cx = (self.fp[0] + self.tp[0]) / 2 + 40
        cy = (self.fp[1] + self.tp[1]) / 2 - 40
        self.x = int(lerp(lerp(self.fp[0], cx, t), lerp(cx, self.tp[0], t), t))
        self.y = int(lerp(lerp(self.fp[1], cy, t), lerp(cy, self.tp[1], t), t))
        self.trail.appendleft((self.x, self.y))
        return True

    def draw(self, surf):
        n = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            a = int(200 * (1 - i / n))
            r = max(1, int(6 - i * 0.3))
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.col, a), (r + 1, r + 1), r)
            surf.blit(s, (tx - r - 1, ty - r - 1))
        cr   = 10
        core = pygame.Surface((cr * 2, cr * 2), pygame.SRCALPHA)
        pygame.draw.circle(core, (*self.col, 230), (cr, cr), cr)
        pygame.draw.circle(core, (255, 255, 255, 200), (cr, cr), 4)
        surf.blit(core, (self.x - cr, self.y - cr))
