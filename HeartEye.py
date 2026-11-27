import math as m
import random as r
import time
import tkinter as tk
import tkinter.font as tkf

BG = "#000000"
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
CYCLE = 20.0
TICK = 55

root = tk.Tk()
root.title("Heart eye")
root.geometry("900x700")
root.minsize(500, 400)
root.configure(bg=BG)
cv = tk.Canvas(root, bg=BG, highlightthickness=0)
cv.pack(fill="both", expand=True)

rng = r.Random()
fonts = {}
W = H = 1
cols = rows = 1
cw = ch = fs = 12
jit, thr, stars = [], [], []
last = None
elapsed = 0.0
last_draw = 0.0
next_blink = 2.0
blink_start = -9.0
running = True


def font_for(size):
    if size not in fonts:
        fonts[size] = tkf.Font(root=root, family="Courier New", size=size, weight="bold")
    return fonts[size]


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def ease(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)


def heart_in(x, y):
    a = x*x + y*y - 1
    return a*a*a - x*x*y*y*y <= 0


def rgb(R, G, B):
    vals = [int(clamp(v / 255) * 255) for v in (R, G, B)]
    return "#%02x%02x%02x" % tuple(vals)


def resize(_event=None):
    global W, H, cols, rows, cw, ch, fs, jit, thr, stars
    W, H = max(1, cv.winfo_width()), max(1, cv.winfo_height())
    fs = max(9, round(min(W, H) / 55))
    cw = max(1, font_for(fs).measure("W"))
    ch = fs + 2
    cols, rows = m.ceil(W / cw), m.ceil(H / ch)
    jit = [0.75 + rng.random() * 0.5 for _ in range(cols * rows)]
    thr = [rng.random() for _ in range(cols * rows)]
    stars = [(rng.random(), rng.random(), rng.random()*6.28, r.choice("+*."))
             for _ in range(70)]


def frame():
    global last, elapsed, last_draw, next_blink, blink_start
    if not running:
        return
    now = time.perf_counter() * 1000
    if last is not None:
        elapsed += min((now - last) / 1000, 0.1)
    last = now
    if now - last_draw < TICK:
        root.after(8, frame)
        return
    last_draw = now

    t = min(elapsed, CYCLE)
    if t < 0.1:
        next_blink, blink_start = 2.0, -9.0

    p = ease((t - 3) / 9)
    zoom = m.exp(m.log(16) * p)
    view_h = 1.3 / zoom
    amp = 0.2 * (1 - 0.85*p)
    look_x = amp*m.sin(t*0.8) + 0.04*m.sin(t*2.3)*(1-p)
    cam_x = look_x*p

    if t >= next_blink and p < 0.5:
        blink_start = t
        next_blink = t + 2.0 + rng.random()*1.5
    eye_open = 1.0
    bp = (t - blink_start) / 0.15
    if 0 <= bp <= 1:
        eye_open = 1 - m.sin(m.pi*bp)

    star_a = ease((t-10)/2)
    heart_t = ease((t-11.5)/4)
    fade = min(1.0, t/0.8)
    cv.delete("all")
    font = font_for(fs)

    for row in range(rows):
        py = row*ch + ch/2
        ny = (py-H/2)/H
        for col in range(cols):
            idx = row*cols + col
            px = col*cw
            nx = (px+cw/2-W/2)/H
            x, y = cam_x + nx*view_h, ny*view_h
            ax, hw = abs(x), 0.85
            lid = (max(0, 1-(ax/hw)**2)**0.9) if ax < hw else -1
            hh = ((0.3 if y < 0 else 0.2)*lid) if lid >= 0 else -1
            in_eye = lid >= 0 and abs(y) <= hh*eye_open
            draw = True

            if in_eye:
                d = m.hypot(x-look_x, y)
                highlight = (m.hypot(x-look_x+0.05, y+0.055) < 0.034 or
                             m.hypot(x-look_x-0.055, y-0.05) < 0.015)
                if highlight and eye_open > 0.5 and p < 0.95:
                    R = G = B = 255
                elif d < 0.11:
                    draw = False
                elif d < 0.27:
                    k = clamp((d-0.11)/0.16)
                    a = m.atan2(y, x-look_x)
                    f = clamp(0.5 + 0.5*(m.sin(a*23)*0.5 +
                                         m.sin(a*57+1.3)*0.3 +
                                         m.sin(a*11+k*4)*0.2))
                    ring = m.exp(-((k-0.35)/0.12)**2)
                    R, G, B = 55+115*f+65*ring, 95+125*f+45*ring, 65+95*f+15*ring
                    if k > 0.8:
                        shade = 1-(k-0.8)*3
                        R, G, B = R*shade, G*shade, B*shade
                else:
                    shade = 0.75 + 0.25*(1-ax/hw)
                    edge = 1-clamp(abs(y)/(hh+1e-6))
                    sh = 0.2 + 0.85*shade*(0.75+0.25*edge)
                    R, G, B = 240*sh, 235*sh, 228*sh
            else:
                e = m.hypot(max(ax-hw, 0), y) if lid < 0 else max(abs(y)-hh*eye_open, 0)
                dark = 1-0.72*m.exp(-e*8)
                if e < 0.015 and ax < hw:
                    dark *= 0.5
                if y < 0:
                    dark *= 1-0.75*m.exp(-e*4.5)
                vig = 1-0.3*min(1, m.hypot(x, y)/1.6)
                R, G, B = 205*dark*vig, 148*dark*vig, 105*dark*vig

            if not draw:
                if heart_t > 0:
                    scale = 0.3*(0.2+0.8*heart_t)*(1+0.05*m.sin(now/250))
                    hx, hy = nx/scale, -ny/scale+0.15
                    if heart_in(hx, hy) and thr[idx] < heart_t:
                        k = 1-min(1, m.hypot(hx, hy-0.3)/1.3)
                        color = rgb(min(255, 190+90*k), 50+70*k*jit[idx], 110+40*k)
                        cv.create_text(px, row*ch, text=r.choice(LETTERS), anchor="nw",
                                       fill=color, font=font)
                continue

            color = rgb(min(255, R*jit[idx]), min(255, G*jit[idx]), min(255, B*jit[idx]))
            cv.create_text(px, row*ch, text=r.choice(LETTERS), anchor="nw",
                           fill=color, font=font)

    if star_a > 0:
        for sx, sy, phase, char in stars:
            alpha = star_a*(0.5+0.5*m.sin(now/500+phase))*fade
            if alpha > 0.25:
                cv.create_text(sx*W, sy*H, text=char, fill="#ffffff",
                               font=font_for(max(9, fs-1)))

    if elapsed >= CYCLE:
        elapsed = 0.0
        next_blink, blink_start = 2.0, -9.0
    root.after(1, frame)


def restart(_event=None):
    global elapsed, last, next_blink, blink_start
    elapsed, last = 0.0, None
    next_blink, blink_start = 2.0, -9.0


def close():
    global running
    running = False
    root.destroy()


cv.bind("<Button-1>", restart)
cv.bind("<Configure>", resize)
root.protocol("WM_DELETE_WINDOW", close)
root.after(150, resize)
root.after(250, frame)
root.mainloop()
