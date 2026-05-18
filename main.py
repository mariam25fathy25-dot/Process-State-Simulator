import pygame, sys, math, random
from config import (W, H, FPS, C, COL, POS, STATES,
                    ARROWS, ARROW_LABELS, NODE_R,
                    clamp, blend, draw_rounded_rect, arrow_between)
from effects import Particle, Orb
from process_logic import Process, EventLog

KEYS = {pygame.K_c:"CREATE", pygame.K_s:"SCHEDULE", pygame.K_w:"I/O WAIT",
        pygame.K_i:"COMPLETE", pygame.K_t:"TERMINATE", pygame.K_r:"RESET"}

BTN_DEFS = [("CREATE","C",C['new']),("SCHEDULE","S",C['ready']),
            ("I/O WAIT","W",C['waiting']),("COMPLETE","I",C['ready']),
            ("TERMINATE","T",C['terminated']),("RESET","R",C['muted'])]

HINTS = [("C","CREATE"),("S","SCHEDULE"),("W","I/O WAIT"),
         ("I","COMPLETE"),("T","TERMINATE"),("R","RESET")]

class Sim:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Process State Simulator")
        self.clock  = pygame.time.Clock()
        self.fnt    = {
            'xl': pygame.font.SysFont("consolas", 38, bold=True),
            'lg': pygame.font.SysFont("consolas", 26, bold=True),
            'md': pygame.font.SysFont("consolas", 20),
            'sm': pygame.font.SysFont("consolas", 16),
            'xs': pygame.font.SysFont("consolas", 13),
        }
        self.proc, self.orb, self.particles = None, None, []
        self.log   = EventLog()
        self.toast = ("", C['muted'], 0.0)
        self.t = self.frame = 0
        self.pulse = {s: random.uniform(0, math.tau) for s in STATES}
        self._build_buttons()
        self.log.add("System ready — press C to create", C['muted'])

    def _build_buttons(self):
        bw, bh, gap = 140, 52, 12
        sx = (W - (len(BTN_DEFS) * bw + (len(BTN_DEFS)-1) * gap)) // 2
        self.buttons = [
            {'rect': pygame.Rect(sx + i*(bw+gap), H-74, bw, bh),
             'label': lb, 'key': k, 'col': col}
            for i, (lb, k, col) in enumerate(BTN_DEFS)
        ]

    def _burst(self, pos, col):
        self.particles += [Particle(pos[0], pos[1], col) for _ in range(22)]

    def _ok(self, msg, col, fr=None, to=None):
        self.toast = (msg, col, 2.5)
        self.log.add(msg, col)
        if fr and to:
            self.orb = Orb(POS[fr], POS[to], COL[fr])
            self._burst(POS[to], COL[to])

    def action(self, name):
        p, ok = self.proc, self._ok
        if name == "CREATE":
            if not p: self.proc = Process(1); ok("P1 created → NEW", C['new'])
            else: ok("Already running — press RESET", C['waiting'])
        elif name == "SCHEDULE":
            if not p:                ok("No process — press CREATE", C['terminated'])
            elif p.state == "NEW":   p.move("READY");   ok("NEW → READY  (admitted)",    C['ready'],      "NEW",     "READY")
            elif p.state == "READY": p.move("RUNNING"); ok("READY → RUNNING  (dispatched)", C['running'], "READY",   "RUNNING")
            else:                    ok(f"Cannot schedule from {p.state}", C['terminated'])
        elif name == "I/O WAIT":
            if p and p.state == "RUNNING": p.move("WAITING"); ok("RUNNING → WAITING  (I/O req)", C['waiting'], "RUNNING", "WAITING")
            else: ok("Process must be RUNNING", C['terminated'])
        elif name == "COMPLETE":
            if p and p.state == "WAITING": p.move("READY"); ok("WAITING → READY  (I/O done)", C['ready'], "WAITING", "READY")
            else: ok("Process must be WAITING", C['terminated'])
        elif name == "TERMINATE":
            if p and p.state == "RUNNING": p.move("TERMINATED"); ok("RUNNING → TERMINATED  (exit)", C['terminated'], "RUNNING", "TERMINATED")
            else: ok("Process must be RUNNING", C['terminated'])
        elif name == "RESET":
            self.proc = self.orb = None; self.particles.clear(); ok("System reset", C['muted'])

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT: return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: self.action("RESET")
                elif e.key in KEYS: self.action(KEYS[e.key])
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for btn in self.buttons:
                    if btn['rect'].collidepoint(e.pos): self.action(btn['label'])
        return True

    def update(self, dt):
        self.t += dt; self.frame += 1
        if self.proc and self.proc.state == "RUNNING": self.proc.cpu += dt
        if self.orb and not self.orb.update(dt): self.orb = None
        self.particles = [p for p in self.particles if p.update(dt)]
        msg, col, ttl = self.toast
        if ttl > 0: self.toast = (msg, col, ttl - dt)

    def _draw_grid(self, s):
        for gx in range(0, W, 44):
            c = (C['grid'][0], C['grid'][1], min(255, C['grid'][2] + int(18 + 8*math.sin(self.t*.6+gx*.015))))
            pygame.draw.line(s, c, (gx, 0), (gx, H), 1)
        for gy in range(0, H, 44):
            c = (C['grid'][0], C['grid'][1], min(255, C['grid'][2] + int(18 + 8*math.sin(self.t*.6+gy*.015))))
            pygame.draw.line(s, c, (0, gy), (W, gy), 1)

    def _draw_arrows(self, s):
        for (a, b) in ARROWS:
            p1, p2 = POS[a], POS[b]
            start, end = arrow_between(p1, p2)
            dx, dy = end[0]-start[0], end[1]-start[1]
            L = math.hypot(dx, dy)
            if L > 0:
                ux, uy = dx/L, dy/L
                d = 0
                while d < L - 7:
                    x1,y1 = int(start[0]+ux*d), int(start[1]+uy*d)
                    x2,y2 = int(start[0]+ux*min(d+7,L)), int(start[1]+uy*min(d+7,L))
                    pygame.draw.line(s, C['border'], (x1,y1), (x2,y2), 2)
                    d += 11
                ang = math.atan2(dy, dx)
                tip = (int(end[0]), int(end[1]))
                pygame.draw.polygon(s, C['border'], [tip,
                    (tip[0]-11*math.cos(ang-.4), tip[1]-11*math.sin(ang-.4)),
                    (tip[0]-11*math.cos(ang+.4), tip[1]-11*math.sin(ang+.4))])
            ox = 28 if p2[0]>p1[0] else (-28 if p2[0]<p1[0] else 38)
            mx, my = (p1[0]+p2[0])//2, (p1[1]+p2[1])//2
            lt = self.fnt['xs'].render(ARROW_LABELS.get((a,b),""), True, C['muted'])
            s.blit(lt, (mx+ox-lt.get_width()//2, my-lt.get_height()//2))

    def _draw_nodes(self, s):
        for state, pos in POS.items():
            col, r = COL[state], NODE_R
            active = self.proc and self.proc.state == state
            if active:
                phase = self.t*3 + self.pulse[state]
                for rr in [r+22, r+14, r+7]:
                    g = pygame.Surface((rr*2+4,rr*2+4), pygame.SRCALPHA)
                    pygame.draw.circle(g, (*col, int(clamp(40+30*math.sin(phase),10,80))), (rr+2,rr+2), rr, 2)
                    s.blit(g, (pos[0]-rr-2, pos[1]-rr-2))
            sh = pygame.Surface((r*2+20,r*2+20), pygame.SRCALPHA)
            pygame.draw.circle(sh, (0,0,0,80), (r+10,r+14), r)
            s.blit(sh, (pos[0]-r-10, pos[1]-r-10))
            pygame.draw.circle(s, blend(C['panel'],col,.12) if active else C['panel'], pos, r)
            pygame.draw.circle(s, col, pos, r, 3 if active else 2)
            pygame.draw.circle(s, col, pos, r-10, 1)
            lbl = self.fnt['md'].render(state, True, C['text'] if active else C['muted'])
            s.blit(lbl, lbl.get_rect(center=pos))

    def _draw_sidebar(self, s, sb_x, sb_w):
        draw_rounded_rect(s, C['panel'], (sb_x,10,sb_w,190), r=12, border=1, border_col=C['border'])
        s.blit(self.fnt['xs'].render("PROCESS INFO", True, C['muted']), (sb_x+14, 20))
        pygame.draw.line(s, C['border'], (sb_x+10,38), (sb_x+sb_w-10,38), 1)
        if not self.proc:
            t = self.fnt['sm'].render("No active process", True, C['muted'])
            s.blit(t, t.get_rect(center=(sb_x+sb_w//2, 110))); return
        p = self.proc
        for i,(k,v,vc) in enumerate([("PID",f"P{p.pid}",C['text']),("STATE",p.state,COL[p.state]),
                                      ("CPU",f"{p.cpu:.2f} s",C['ready']),("TIME",f"{p.duration():.1f} s",C['muted'])]):
            s.blit(self.fnt['xs'].render(k,True,C['muted']), (sb_x+14, 48+i*28))
            s.blit(self.fnt['sm'].render(v,True,vc),          (sb_x+130,47+i*28))
        if p.state == "RUNNING":
            bx,by,bw,bh = sb_x+14, 162, sb_w-28, 6
            draw_rounded_rect(s, C['border'], (bx,by,bw,bh), r=3)
            fw = int(bw*(p.duration()%4)/4)
            if fw: draw_rounded_rect(s, C['running'], (bx,by,fw,bh), r=3)
            s.blit(self.fnt['xs'].render("CPU BURST",True,C['muted']), (bx,by-14))
        for i,st in enumerate(STATES):
            bx2 = sb_x+14+i*56
            draw_rounded_rect(s, C['panel2'], (bx2,178,50,40), r=6, border=1, border_col=COL[st])
            for txt,fk,y in [(st[:3],'xs',182),(str(p.stats[st]),'sm',198)]:
                t = self.fnt[fk].render(txt,True,COL[st] if fk=='xs' else C['text'])
                s.blit(t,(bx2+25-t.get_width()//2, y))

    def _draw_shortcuts(self, s, sb_x, sb_w):
        hy = 465
        draw_rounded_rect(s, C['panel'], (sb_x,hy,sb_w,175), r=12, border=1, border_col=C['border'])
        s.blit(self.fnt['xs'].render("KEYBOARD SHORTCUTS",True,C['muted']), (sb_x+14,hy+10))
        pygame.draw.line(s, C['border'], (sb_x+10,hy+28),(sb_x+sb_w-10,hy+28),1)
        for i,(k,lb) in enumerate(HINTS):
            y = hy+36+i*22
            s.blit(self.fnt['xs'].render(f"[{k}]",True,C['ready']),  (sb_x+14,y))
            s.blit(self.fnt['xs'].render(lb,       True,C['muted']),  (sb_x+55,y))

    def _draw_buttons(self, s):
        mx, my = pygame.mouse.get_pos()
        for btn in self.buttons:
            r, col = btn['rect'], btn['col']
            hov = r.collidepoint(mx,my)
            bg = pygame.Surface((r.w,r.h), pygame.SRCALPHA)
            pygame.draw.rect(bg, (*col, 55 if hov else 28), (0,0,r.w,r.h), border_radius=10)
            s.blit(bg, r.topleft)
            pygame.draw.rect(s, blend(col,C['white'],.5) if hov else col, r, 2 if hov else 1, border_radius=10)
            s.blit(self.fnt['xs'].render(f"[{btn['key']}]",True,C['muted']), (r.x+10,r.y+6))
            t = self.fnt['sm'].render(btn['label'],True,C['text'] if hov else col)
            s.blit(t, t.get_rect(centerx=r.centerx, y=r.y+26))

    def _draw_toast(self, s):
        msg, col, ttl = self.toast
        if ttl <= 0: return
        alpha = min(1.0,ttl)*255
        ts = self.fnt['sm'].render(msg,True,C['text'])
        tw,th = ts.get_width()+32, ts.get_height()+16
        tx,ty = W//2-tw//2, H-100
        bg = pygame.Surface((tw,th), pygame.SRCALPHA)
        pygame.draw.rect(bg, (*C['panel'],int(alpha*.95)), (0,0,tw,th), border_radius=8)
        pygame.draw.rect(bg, (*col,int(alpha*.6)),         (0,0,tw,th), 1, border_radius=8)
        s.blit(bg,(tx,ty)); s.blit(ts,(tx+16,ty+8))

    def draw(self):
        s = self.screen
        s.fill(C['bg'])
        self._draw_grid(s)
        self._draw_arrows(s)
        self._draw_nodes(s)
        for p in self.particles: p.draw(s)
        if self.orb: self.orb.draw(s)
        sb_x, sb_w = W-320, 300
        self._draw_sidebar(s, sb_x, sb_w)
        self.log.draw(s, self.fnt, sb_x, 230, sb_w, 220)
        self._draw_shortcuts(s, sb_x, sb_w)
        s.blit(self.fnt['xl'].render("PROCESS STATE SIMULATOR",True,C['text']), (14,12))
        s.blit(self.fnt['xs'].render("Operating Systems — Interactive Demo",True,C['muted']), (16,50))
        self._draw_buttons(s)
        self._draw_toast(s)
        s.blit(self.fnt['xs'].render(f"FPS {int(self.clock.get_fps())}",True,C['muted']), (W-80,H-22))
        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            if not self.handle_events(): break
            self.update(dt)
            self.draw()
        pygame.quit(); sys.exit()


if __name__ == "__main__":
    Sim().run()
