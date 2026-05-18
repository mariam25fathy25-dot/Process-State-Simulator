import pygame, math

def lerp(a, b, t):
    return a + (b - a) * t

def ease_out(t):
    return 1 - (1 - t) ** 3

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def blend(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def draw_rounded_rect(surf, col, rect, r=10, border=0, border_col=None):
    pygame.draw.rect(surf, col, rect, border_radius=r)
    if border and border_col:
        pygame.draw.rect(surf, border_col, rect, border, border_radius=r)

def arrow_between(p1, p2, radius=54):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(dx, dy)
    if L == 0:
        return p1, p2
    ux, uy = dx / L, dy / L
    start = (p1[0] + ux * radius, p1[1] + uy * radius)
    end   = (p2[0] - ux * (radius + 6), p2[1] - uy * (radius + 6))
    return start, end

def draw_arrow(surf, col, p1, p2, width=2):
    s, e = arrow_between(p1, p2)
    pygame.draw.line(surf, col, (int(s[0]), int(s[1])), (int(e[0]), int(e[1])), width)
    angle = math.atan2(e[1] - s[1], e[0] - s[0])
    size = 10
    pts = [
        (e[0], e[1]),
        (e[0] - size * math.cos(angle - 0.45), e[1] - size * math.sin(angle - 0.45)),
        (e[0] - size * math.cos(angle + 0.45), e[1] - size * math.sin(angle + 0.45)),
    ]
    pygame.draw.polygon(surf, col, pts)

def midpoint(p1, p2):
    return ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)

W, H = 1400, 820
FPS  = 60
CX   = W // 2

C = {
    'bg':         (4,   5,   14),
    'grid':       (14,  18,  38),
    'panel':      (8,   11,  24),
    'panel2':     (12,  16,  34),
    'border':     (22,  28,  58),
    'new':        (168, 85,  247),
    'ready':      (6,   182, 212),
    'running':    (16,  185, 129),
    'waiting':    (245, 158, 11),
    'terminated': (239, 68,  68),
    'text':       (232, 234, 246),
    'muted':      (80,  90,  130),
    'white':      (255, 255, 255),
    'suc':        (16,  185, 129),
}

STATES = ["NEW", "READY", "RUNNING", "WAITING", "TERMINATED"]
POS = {
    "NEW":        (CX,       100),
    "READY":      (CX,       240),
    "RUNNING":    (CX,       390),
    "WAITING":    (CX + 230, 520),
    "TERMINATED": (CX - 230, 520),
}
COL = {s: C[s.lower()] for s in STATES}

VALID = {
    "NEW":        ["READY"],
    "READY":      ["RUNNING"],
    "RUNNING":    ["READY", "WAITING", "TERMINATED"],
    "WAITING":    ["READY"],
    "TERMINATED": [],
}

ARROWS = [
    ("NEW",     "READY"),
    ("READY",   "RUNNING"),
    ("RUNNING", "READY"),
    ("RUNNING", "WAITING"),
    ("RUNNING", "TERMINATED"),
    ("WAITING", "READY"),
]
ARROW_LABELS = {
    ("NEW",     "READY"):      "admit",
    ("READY",   "RUNNING"):    "dispatch",
    ("RUNNING", "READY"):      "preempt",
    ("RUNNING", "WAITING"):    "I/O wait",
    ("RUNNING", "TERMINATED"): "exit",
    ("WAITING", "READY"):      "I/O done",
}

NODE_R = 54
