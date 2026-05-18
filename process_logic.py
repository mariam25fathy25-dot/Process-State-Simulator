import pygame, time
from collections import deque
from config import STATES, VALID, COL, C, draw_rounded_rect

class Process:
    def __init__(self, pid):
        self.pid   = pid
        self.state = "NEW"
        self.start = time.time()
        self.cpu   = 0.0
        self.total = 0.0
        self.stats = {s: 0 for s in STATES}
        self.stats["NEW"] = 1
        self.history = []

    def move(self, ns):
        if ns not in VALID[self.state]:
            return False
        self.history.append((self.state, ns, time.time()))
        self.state = ns
        self.start = time.time()
        self.stats[ns] += 1
        return True

    def duration(self):
        return time.time() - self.start

    def color(self):
        return COL[self.state]

class EventLog:
    def __init__(self):
        self.entries = deque(maxlen=12)

    def add(self, msg, col):
        self.entries.appendleft((msg, col, time.time()))

    def draw(self, surf, fnt, x, y, w, h):
        draw_rounded_rect(surf, C['panel'], (x, y, w, h), r=12,
                          border=1, border_col=C['border'])
        label = fnt['xs'].render("EVENT LOG", True, C['muted'])
        surf.blit(label, (x + 12, y + 10))
        pygame.draw.line(surf, C['border'],
                         (x + 10, y + 28), (x + w - 10, y + 28), 1)
        for i, (msg, col, _) in enumerate(self.entries):
            if i >= 9:
                break
            iy  = y + 36 + i * 20
            dot = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*col, 200), (3, 3), 3)
            surf.blit(dot, (x + 12, iy + 4))
            t = fnt['xs'].render(msg[:34], True, col)
            surf.blit(t, (x + 22, iy))
