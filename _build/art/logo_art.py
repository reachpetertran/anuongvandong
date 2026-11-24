"""Logo anuongvandong.com – cùng họ huy hiệu với daynentang / tamhonkhoe / kynanglamviec.

Khung chung: vòm xanh than, viền kem, dải băng tên, thanh dưới ghi EST. 2026.
Biểu tượng giữa đổi theo chủ đề. Chữ chuyển thành nét (Inter Bold / SemiBold).

    python3 _build/art/logo_art.py            # sinh 3 phương án vào _build/art/phuong-an/
    python3 _build/art/logo_art.py --chot A   # sinh bộ logo chính thức vào assets/logo/
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textpath import centered

INTER = '/usr/share/fonts/opentype/inter/'
NAVY, NAVY2, CREAM = '#1b2a41', '#24385a', '#fffdf8'
GREEN, GREEN_L, GREEN_D = '#2f7d4a', '#5cae4f', '#1f5a3a'
SUN_A, SUN_B = '#f6a33a', '#e8702a'
ACCENT = '#f6a33a'

ARCH_OUT = 'M36 400 V186 A164 164 0 0 1 364 186 V400 Z'
ARCH_IN = 'M48 392 V186 A152 152 0 0 1 352 186 V392 Z'


def la(cx, cy, dai, rong, goc, mau, gan=CREAM):
    """Một chiếc lá: hai cung đối xứng + gân giữa, xoay quanh gốc lá (cx, cy)."""
    d = (f'M0 0 C{rong} {-dai * 0.25} {rong} {-dai * 0.75} 0 {-dai} '
         f'C{-rong} {-dai * 0.75} {-rong} {-dai * 0.25} 0 0Z')
    return (f'<g transform="translate({cx} {cy}) rotate({goc})"><path d="{d}" fill="{mau}"/>'
            f'<path d="M0 -4 L0 {-dai * 0.86}" stroke="{gan}" stroke-width="4" stroke-linecap="round" fill="none"/></g>')


def dau_chan(x, y, goc, s=1.0, mau=CREAM):
    """Dấu bàn chân giản lược (không phải hình người): gót + 4 chấm ngón."""
    ngon = ''.join(f'<circle cx="{dx}" cy="{dy}" r="{r}" fill="{mau}"/>'
                   for dx, dy, r in ((-6, -25, 3.6), (0, -27, 3.9), (6, -25, 3.6), (11, -20, 3.0)))
    return (f'<g transform="translate({x} {y}) rotate({goc}) scale({s})">'
            f'<ellipse cx="2" cy="-8" rx="8" ry="13" fill="{mau}"/>{ngon}</g>')


def nen():
    return (f'<rect x="0" y="0" width="400" height="440" fill="{NAVY}"/>'
            f'<circle cx="200" cy="176" r="92" fill="url(#sun)"/>'
            f'<path d="M30 300 L110 215 L150 250 L200 175 L250 240 L290 205 L370 300Z" fill="{NAVY2}"/>')


def pa_A():
    """A – Lá và nhịp bước: chồi hai lá mọc trên đồi, hàng dấu chân đi lên."""
    doi = f'<path d="M20 330 C110 250 290 250 380 330Z" fill="{GREEN}"/>'
    doi2 = f'<path d="M200 262 C260 258 330 280 380 330 L250 330Z" fill="{GREEN_L}"/>'
    than = f'<path d="M200 270 C200 240 200 215 202 190" stroke="{GREEN_D}" stroke-width="7" fill="none" stroke-linecap="round"/>'
    las = la(202, 214, 78, 30, -42, GREEN_L) + la(202, 236, 66, 26, 48, GREEN)
    chan = (dau_chan(118, 316, 28, 0.85) + dau_chan(146, 300, 18, 0.85) +
            dau_chan(268, 300, -18, 0.85) + dau_chan(296, 316, -28, 0.85))
    return nen() + doi + doi2 + than + las + chan


def pa_B():
    """B – Bát cơm và nhịp tim: bát trên đồi, chồi lá bốc lên, đường nhịp chạy ngang."""
    doi = f'<path d="M20 330 C110 270 290 270 380 330Z" fill="{GREEN}"/>'
    bat = (f'<path d="M122 238 H278 C276 282 244 306 200 306 C156 306 124 282 122 238Z" fill="{CREAM}"/>'
           f'<path d="M122 238 H278" stroke="{GREEN_D}" stroke-width="6" stroke-linecap="round"/>'
           f'<rect x="178" y="304" width="44" height="10" rx="4" fill="{CREAM}"/>'
           f'<path d="M140 262 H260" stroke="{SUN_B}" stroke-width="5" opacity=".55"/>')
    hat = ''.join(f'<ellipse cx="{x}" cy="{y}" rx="9" ry="6" fill="{CREAM}"/>'
                  for x, y in ((150, 234), (168, 226), (186, 222), (204, 220), (222, 222), (240, 226), (256, 233)))
    las = la(200, 222, 70, 26, -30, GREEN_L) + la(200, 224, 58, 22, 34, GREEN)
    nhip = (f'<path d="M60 286 H112 L124 266 L136 304 L146 286 H150" stroke="{CREAM}" stroke-width="6" '
            f'fill="none" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<path d="M250 286 H262 L272 270 L284 302 L294 286 H340" stroke="{CREAM}" stroke-width="6" '
            f'fill="none" stroke-linejoin="round" stroke-linecap="round"/>')
    return nen() + doi + nhip + hat + bat + las


def pa_C():
    """C – Đường đi và mặt trời: con đường uốn lượn lên đồi, lá ở hai bên."""
    doi = f'<path d="M20 330 C80 240 320 240 380 330Z" fill="{GREEN}"/>'
    doi2 = f'<path d="M200 250 C280 250 340 280 380 330 L260 330Z" fill="{GREEN_L}"/>'
    duong = (f'<path d="M150 332 C170 300 250 300 228 280 C206 262 186 262 204 246" stroke="{CREAM}" '
             f'stroke-width="22" fill="none" stroke-linecap="round"/>'
             f'<path d="M150 332 C170 300 250 300 228 280 C206 262 186 262 204 246" stroke="{SUN_A}" '
             f'stroke-width="3" stroke-dasharray="8 9" fill="none"/>')
    las = (la(104, 300, 62, 22, -18, GREEN_L) + la(116, 304, 48, 18, 30, GREEN_D) +
           la(302, 300, 62, 22, 18, GREEN_D) + la(290, 304, 48, 18, -30, GREEN_L))
    return nen() + doi + doi2 + duong + las


PHUONG_AN = {'A': pa_A, 'B': pa_B, 'C': pa_C}


def svg(art, chu=True, icon=False):
    defs = (f'<defs><clipPath id="c"><path d="{ARCH_IN}"/></clipPath><linearGradient id="sun" x1="0" y1="0" '
            f'x2="0" y2="1"><stop offset="0" stop-color="{SUN_A}"/><stop offset="1" stop-color="{SUN_B}"/>'
            f'</linearGradient></defs>')
    if icon:
        # Icon vuông: chỉ vòm + biểu tượng, nền xanh than, góc bo.
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="20 40 360 360">{defs}'
                f'<rect x="20" y="40" width="360" height="360" rx="64" fill="{NAVY}"/>'
                f'<g clip-path="url(#c)">{art}</g>'
                f'<path d="{ARCH_IN}" fill="none" stroke="{CREAM}" stroke-width="5"/></svg>')
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 428">{defs}'
         f'<path d="{ARCH_OUT}" fill="{NAVY}"/><g clip-path="url(#c)">{art}</g>'
         f'<path d="{ARCH_IN}" fill="none" stroke="{CREAM}" stroke-width="4"/>')
    if chu:
        t, _ = centered('ĂN UỐNG VẬN ĐỘNG', INTER + 'Inter-Bold.otf', 25, 200.2, 361, 0.9)
        b, _ = centered('EST. 2026 · ANUONGVANDONG.COM', INTER + 'Inter-SemiBold.otf', 13, 200, 412, 1.6)
        s += (f'<path d="M14 322 H386 L374 352 L386 382 H14 L26 352Z" fill="{CREAM}" stroke="{NAVY}" stroke-width="6"/>'
              f'<rect x="27" y="392" width="346" height="30" fill="{NAVY}"/>'
              f'<path fill="{NAVY}" d="{t}"/><path fill="{ACCENT}" d="{b}"/>')
    return s + '</svg>'


def ghi(path, noi_dung):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(noi_dung)


def png(svg_path, png_path, w):
    subprocess.run(['rsvg-convert', '-w', str(w), '-o', png_path, svg_path], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chot', choices=list(PHUONG_AN))
    a = ap.parse_args()
    goc = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if not a.chot:
        out = os.path.join(goc, '_build', 'art', 'phuong-an')
        for k, f in PHUONG_AN.items():
            p = os.path.join(out, f'logo-{k}.svg')
            ghi(p, svg(f()))
            png(p, p[:-4] + '.png', 512)
            pi = os.path.join(out, f'icon-{k}.svg')
            ghi(pi, svg(f(), icon=True))
            png(pi, pi[:-4] + '.png', 256)
        print('Đã sinh 3 phương án ->', out)
        return
    art = PHUONG_AN[a.chot]()
    out = os.path.join(goc, 'assets', 'logo')
    ghi(os.path.join(out, 'anuongvandong-logo.svg'), svg(art))
    ghi(os.path.join(out, 'anuongvandong-logo-khong-chu.svg'), svg(art, chu=False))
    ghi(os.path.join(out, 'anuongvandong-icon.svg'), svg(art, icon=True))
    ghi(os.path.join(out, 'favicon.svg'), svg(art, icon=True))
    for w in (512, 1024):
        png(os.path.join(out, 'anuongvandong-logo.svg'), os.path.join(out, f'anuongvandong-logo-{w}.png'), w)
    png(os.path.join(out, 'anuongvandong-icon.svg'), os.path.join(out, 'anuongvandong-icon-512.png'), 512)
    png(os.path.join(out, 'anuongvandong-icon.svg'), os.path.join(out, 'apple-touch-icon.png'), 180)
    png(os.path.join(out, 'anuongvandong-icon.svg'), '/tmp/fav48.png', 48)
    subprocess.run(['convert', '/tmp/fav48.png', '-define', 'icon:auto-resize=48,32,16',
                    os.path.join(out, 'favicon.ico')], check=True)
    print('Đã chốt phương án', a.chot, '->', out)


if __name__ == '__main__':
    main()
