#!/usr/bin/env python3
"""Sinh app/www/ từ public/ của website anuongvandong.com.

- Chép mọi trang, tài nguyên (bỏ sitemap, robots, _headers, 404).
- Đổi link tuyệt đối `/a/b/` thành tương đối `../../a/b/index.html` để chạy khi mất mạng.
- Bỏ canonical, hreflang, og:*; bỏ header, link "bỏ qua" và dòng trang anh em của web; chèn khung app.
- Chèn script nhỏ trong <head> áp cỡ chữ, nền đã lưu (tránh nháy màn hình).
- Sinh www/app/index.js: khung chương trình (Phần → bài), cặp VI/EN, chỉ mục tìm kiếm, sách.

SÁCH – CHỖ CHỪA SẴN:
  Tab "Sách" đã có trong app (www/app/sach.html). Hiện chưa có sách → hiện thông báo "đang viết".
  Khi sách xong: đặt dữ liệu sách (out/app/ của mã sách: manifest.json + chapters/*.json) vào
  app/sach-data/ (KHÔNG đưa lên GitHub, đã .gitignore) và thêm app/build_book.py có hàm
  build(BOOK, WWW, HEAD_JS) trả về dict {title, author, checked, parts, chapters, front, back, search}
  (cùng khuôn với app trachnhiemxahoi). Không phải sửa app.js.

Chạy:  python3 app/build_www.py
"""
import html as H
import json
import re
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PUB = ROOT / "public"
APP = ROOT / "app"
WWW = APP / "www"
SHELL = APP / "shell"
BOOK = APP / "sach-data"          # chỗ chừa cho sách – .gitignore
SKIP = {"sitemap.xml", "robots.txt", "_headers", "404.html"}
KEY = "auvd.v1"


def front(p):
    t = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    return yaml.safe_load(m.group(1)) if m else {}


def page_of(url):
    """/an-uong/muoi/ → an-uong/muoi/index.html"""
    return url.strip("/") + "/index.html" if url.strip("/") else "index.html"


# ---------- 1. Dữ liệu bài, khung chương trình ----------
vi = {}
for p in sorted((ROOT / "content/vi").glob("*.md")):
    f = front(p)
    if f.get("status") == "published" and f.get("url"):
        vi[f["slug"]] = f
en_by_pair = {}
for p in sorted((ROOT / "content/en").glob("*.md")):
    f = front(p)
    if f.get("status") == "published" and f.get("pair") and f.get("url"):
        en_by_pair[f["pair"]] = f

khung = yaml.safe_load((ROOT / "data/khung.yaml").read_text(encoding="utf-8"))
modules = []
for ph in khung["phan"]:
    lessons = []
    for b in ph.get("bai") or []:
        s = b.get("slug")
        if not s or s not in vi:
            continue                     # bài chưa đăng không vào app
        e = en_by_pair.get(s)
        lessons.append({
            "vi": page_of(vi[s]["url"]), "t": vi[s]["title"],
            "en": page_of(e["url"]) if e else None,
            "t_en": e["title"] if e else None,
        })
    if lessons:
        modules.append({"id": f"p{ph['so']}", "t": ph["ten"], "t_en": ph.get("ten_en", ph["ten"]),
                        "lessons": lessons})


# ---------- 2. Chép public/ ----------
if WWW.exists():
    shutil.rmtree(WWW)
shutil.copytree(PUB, WWW, ignore=lambda d, names: [n for n in names if n in SKIP])
(WWW / "app").mkdir(exist_ok=True)
for f in SHELL.iterdir():
    shutil.copy(f, WWW / "app" / f.name)

HEAD_JS = ("<script>try{var s=JSON.parse(localStorage.getItem('" + KEY + "')||'{}').set||{};"
           "var d=document.documentElement;d.dataset.fs=s.fs||'2';"
           "var t=s.theme||'auto';if(t==='auto')t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';"
           "d.dataset.theme=t;}catch(e){}</script>")


def fix_link(h, pre):
    """Link nội bộ: tuyệt đối → tương đối; thư mục → index.html."""
    if re.match(r"^(https?:|mailto:|tel:|#|data:|javascript:|//)", h):
        return h
    path, _, frag = h.partition("#")
    if path.startswith("/"):
        path = pre + path.lstrip("/")
        if path == "":
            path = "./"
    if path.endswith("/") or path in (".", ".."):
        path = path.rstrip("/") + "/index.html" if path not in ("./",) else "index.html"
        path = re.sub(r"^\./", "", path)
    return path + ("#" + frag if frag else "")


search = []
pages = sorted(WWW.rglob("*.html"))
for p in pages:
    rel = p.relative_to(WWW).as_posix()
    if rel.startswith("app/"):
        continue
    s = p.read_text(encoding="utf-8")
    lang = "en" if rel.startswith("en/") else "vi"
    pre = "../" * (len(p.relative_to(WWW).parts) - 1)

    # cặp ngôn ngữ (từ nút .lang của web, trước khi bỏ header)
    m = re.search(r'<a class="lang" href="([^"]*)"', s)
    alt = fix_link(m.group(1), "") if m else ""

    s = re.sub(r'<link rel="canonical"[^>]*>\n?', "", s)
    s = re.sub(r'<link rel="alternate"[^>]*>\n?', "", s)
    s = re.sub(r'<link rel="(icon|apple-touch-icon)"[^>]*>\n?', "", s)
    s = re.sub(r'<meta property="og:[^>]*>\n?', "", s)
    s = re.sub(r'<a class="skip"[^>]*>.*?</a>\n?', "", s)
    s = re.sub(r'<header class="site-head">.*?</header>\n?', "", s, flags=re.S)
    # footer: bỏ dòng trang anh em (mở web, không cần trong app) – giữ miễn trừ, giấy phép
    s = re.sub(r"<div><p>(Trang anh em|Sister sites)[^\n]*?</p></div>", "", s)

    s = re.sub(r'(href|src)="([^"]*)"', lambda mm: f'{mm.group(1)}="{fix_link(mm.group(2), pre)}"', s)
    s = s.replace('<meta charset="utf-8">', '<meta charset="utf-8">' + HEAD_JS, 1)
    s = re.sub(r'content="width=device-width, ?initial-scale=1"',
               'content="width=device-width,initial-scale=1,viewport-fit=cover"', s)
    s = s.replace(f'<link rel="stylesheet" href="{pre}assets/style.css">',
                  f'<link rel="stylesheet" href="{pre}assets/style.css">'
                  f'<link rel="stylesheet" href="{pre}app/app.css">')
    s = s.replace("<body>", f'<body data-lang="{lang}" data-page="{rel}" data-alt="{alt}" data-root="{pre}">', 1)
    s = s.replace("</body>", f'<script src="{pre}app/index.js"></script><script src="{pre}app/app.js"></script></body>')
    p.write_text(s, encoding="utf-8")

    # chỉ mục tìm kiếm: mọi trang nội dung (bài, trang tuổi, trang thông tin), bỏ trang danh mục
    if rel.count("/") < 1 or rel in ("khung-chuong-trinh/index.html", "en/curriculum/index.html",
                                       "theo-tuoi/index.html", "en/by-age/index.html", "en/index.html"):
        continue
    main = re.search(r"<main[^>]*>(.*?)</main>", s, re.S)
    body = main.group(1) if main else ""
    body = re.sub(r'<div class="lesson-meta">.*?</div>', "", body, flags=re.S)
    title = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    title = re.sub("<[^>]+>", "", title.group(1)) if title else rel
    text = H.unescape(re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", body))).strip()
    search.append({"u": rel, "l": lang, "t": H.unescape(title), "x": text[:6000]})


# ---------- 3. Trang riêng của app: Của tôi, Tìm, Sách ----------
APP_PAGE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8">{head}
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Ăn Uống Vận Động</title>
<link rel="stylesheet" href="../assets/style.css"><link rel="stylesheet" href="app.css">
</head><body data-page="app/{name}.html" data-root="../">
<main id="main"><div class="wrap"></div></main>
<script src="index.js"></script><script src="app.js"></script></body></html>
"""
for name in ("toi", "tim", "sach"):
    (WWW / f"app/{name}.html").write_text(APP_PAGE.format(head=HEAD_JS, name=name), encoding="utf-8")

# ---------- 4. Sách – chỗ chừa sẵn (xem ghi chú đầu file) ----------
book = None
if (BOOK / "manifest.json").exists() and (APP / "build_book.py").exists():
    import build_book                                   # app/build_book.py (thêm khi có sách)
    book = build_book.build(BOOK, WWW, HEAD_JS)
    search.extend(book.pop("search", []))

idx = {"modules": modules, "search": search, "book": book}
(WWW / "app/index.js").write_text(
    "window.AUVD=" + json.dumps(idx, ensure_ascii=False, separators=(",", ":")) + ";",
    encoding="utf-8")

# kiểm tra: không còn link tuyệt đối nội bộ
bad = []
for p in WWW.rglob("*.html"):
    for h in re.findall(r'(?:href|src)="(/[^"/][^"]*|/)"', p.read_text(encoding="utf-8")):
        bad.append((p.relative_to(WWW).as_posix(), h))
if bad:
    raise SystemExit(f"Còn {len(bad)} link tuyệt đối, ví dụ: {bad[:5]}")

n_less = sum(len(m["lessons"]) for m in modules)
print(f"www/: {len(pages)} trang web, {len(modules)} phần, {n_less} bài, {len(search)} mục tìm kiếm, "
      f"sách: {'có' if book else 'chưa có (chỗ chừa sẵn)'}")
