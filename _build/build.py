"""Sinh trang tĩnh anuongvandong.com (tiếng Việt ở /, tiếng Anh ở /en/).

    python3 _build/build.py            # bản công khai -> public/ (chỉ bài status: published)
    python3 _build/build.py --preview  # bản xem thử -> _preview/ (có cả nháp, gắn noindex)

Build DỪNG (thoát mã 1) khi bài công khai vi phạm quy tắc của dự án:
thiếu trường front matter, thiếu bản tiếng Anh, còn nhãn [Cần kiểm chứng]/[Đã xác nhận*],
thiếu mục "Ai cần thận trọng"/"Khi nào gặp nhân viên y tế", dùng từ bị cấm.
"""
import argparse
import datetime as dt
import html
import os
import re
import shutil
import sys

import markdown
import yaml

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SITE = 'https://anuongvandong.com'
GIAY_PHEP = ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/')

TRUONG_BAI = ['slug', 'order', 'status', 'title', 'short', 'age_groups', 'pillar', 'evidence_level',
              'checked', 'review_due', 'sources', 'url']
TU_CAM = ['toàn diện', 'đột phá', 'nâng tầm', 'thần kỳ', 'thải độc', 'bí quyết']
NHAN_CAM = ['[Cần kiểm chứng]', '[Đã xác nhận*]', '[To verify]', '[Verified*]']
MUC_BAT_BUOC = {'vi': ['Ai cần thận trọng', 'Khi nào gặp nhân viên y tế'],
                'en': ['Who should take care', 'When to see a health worker']}
NHAN = {  # nhãn trong bài -> lớp CSS
    'Đã xác nhận': 'xac-nhan', 'Verified': 'xac-nhan',
    'Đã xác nhận*': 'can-kiem-chung', 'Verified*': 'can-kiem-chung',
    'Suy luận': 'suy-luan', 'Inference': 'suy-luan',
    'Đánh giá chuyên môn': 'danh-gia', 'Expert judgement': 'danh-gia',
    'Cần kiểm chứng': 'can-kiem-chung', 'To verify': 'can-kiem-chung',
    'Ví dụ giả định': 'suy-luan', 'Hypothetical example': 'suy-luan',
}

NAV = {'vi': [('/', 'Trang chủ'), ('/khung-chuong-trinh/', 'Khung chương trình'), ('/theo-tuoi/', 'Theo tuổi'),
              ('/nguon-va-cap-nhat/', 'Nguồn')],
       'en': [('/en/', 'Home'), ('/en/curriculum/', 'Curriculum'), ('/en/by-age/', 'By age'),
              ('/en/sources-and-updates/', 'Sources')]}
TRO_GIUP = {'vi': '/tim-tro-giup/', 'en': '/en/find-help/'}
ANH_EM = [('tienganhcanban.com', 'https://tienganhcanban.com'), ('daynentang.com', 'https://daynentang.com'),
          ('tamhonkhoe.com', 'https://tamhonkhoe.com'), ('kynanglamviec.com', 'https://kynanglamviec.com'),
          ('trachnhiemxahoi.com', 'https://trachnhiemxahoi.com')]
HEADERS = '''/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()
  Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'none'
  X-Frame-Options: DENY
'''


class LoiNoiDung(Exception):
    pass


class Bai:
    def __init__(self, path, lang):
        raw = open(path, encoding='utf-8').read()
        m = re.match(r'^---\n(.*?)\n---\n(.*)$', raw, re.S)
        if not m:
            raise LoiNoiDung(f'{path}: thiếu front matter')
        self.meta = yaml.safe_load(m.group(1)) or {}
        self.md = m.group(2)
        self.path = os.path.relpath(path, GOC)
        self.lang = lang
        self.loai = self.meta.get('loai', 'bai')
        self.slug = self.meta.get('slug')
        self.url = self.meta.get('url')
        self.title = self.meta.get('title', '')
        self.cap = None

    @property
    def published(self):
        return self.meta.get('status') == 'published'


def doc_bai():
    ds = []
    for lang in ('vi', 'en'):
        thu_muc = os.path.join(GOC, 'content', lang)
        for fn in sorted(os.listdir(thu_muc)):
            if fn.endswith('.md'):
                ds.append(Bai(os.path.join(thu_muc, fn), lang))
    vi = {b.slug: b for b in ds if b.lang == 'vi'}
    for b in ds:
        if b.lang == 'en':
            v = vi.get(b.meta.get('pair'))
            if v:
                b.cap, v.cap = v, b
    return ds


def kiem_tra(b):
    """Trả về danh sách lỗi của một bài định đăng công khai."""
    loi = []
    if not b.url or not b.slug:
        loi.append('thiếu slug/url')
    if b.loai == 'bai':
        loi += [f'thiếu trường {k}' for k in TRUONG_BAI if b.meta.get(k) in (None, '', [])]
        for muc in MUC_BAT_BUOC[b.lang]:
            if muc not in b.md:
                loi.append(f'thiếu mục "{muc}"')
    if b.lang == 'en' and 'pair' not in b.meta:
        loi.append('bản Anh thiếu pair')
    if b.lang == 'vi' and (not b.cap or not b.cap.published):
        loi.append('chưa có bản tiếng Anh đã published')
    for n in NHAN_CAM:
        if n in b.md:
            loi.append(f'còn nhãn {n}')
    if b.lang == 'vi':
        thap = b.md.lower()
        for t in TU_CAM:
            if t in thap and t not in (b.meta.get('cho_phep_tu') or []):
                loi.append(f'dùng từ cấm "{t}"')
    if b.lang == 'en' and 'Vietnamese version is the original' not in b.md:
        loi.append('bản Anh thiếu dòng "the Vietnamese version is the original"')
    return loi


def md_html(text):
    out = markdown.markdown(text, extensions=['tables', 'attr_list', 'sane_lists'])
    out = out.replace('<table>', '<div class="table-wrap"><table>').replace('</table>', '</table></div>')

    def nhan(m):
        lop = NHAN.get(m.group(1))
        return f'<span class="nhan {lop}">{html.escape(m.group(1))}</span>' if lop else m.group(0)
    return re.sub(r'\[([^\[\]]{3,40})\](?!\()', nhan, out)


def en_alt(url, ds_url):
    return ds_url.get(url)


def trang(out, path, title, desc, body, lang='vi', alt=None, current=None, preview=False, nhap=False):
    en = lang == 'en'
    cur = ' aria-current="page"'
    nav = ''.join(f'<a href="{h}"{cur if h == current else ""}>{t}</a>' for h, t in NAV[lang])
    if en:
        nav += f'<a class="lang" href="{alt or "/"}" hreflang="vi" lang="vi">Tiếng Việt</a>'
        nav += f'<a class="help" href="{TRO_GIUP["en"]}">Find help</a>'
    else:
        nav += f'<a class="lang" href="{alt or "/en/"}" hreflang="en" lang="en">English</a>'
        nav += f'<a class="help" href="{TRO_GIUP["vi"]}">Tìm trợ giúp</a>'
    full = title if 'anuongvandong' in title.lower() else f'{title} – anuongvandong.com'
    robots = '<meta name="robots" content="noindex, nofollow">\n' if preview else ''
    hreflang = ''
    if alt:
        vi_p, en_p = (alt, path) if en else (path, alt)
        hreflang = (f'<link rel="alternate" hreflang="vi" href="{SITE}{vi_p}">\n'
                    f'<link rel="alternate" hreflang="en" href="{SITE}{en_p}">\n'
                    f'<link rel="alternate" hreflang="x-default" href="{SITE}{vi_p}">\n')
    banner = ''
    if nhap:
        banner = ('<div class="nhap-banner"><div class="wrap"><p><strong>DRAFT</strong> – not published.</p></div></div>'
                  if en else '<div class="nhap-banner"><div class="wrap"><p><strong>BẢN NHÁP</strong> – chưa đăng '
                  'công khai.</p></div></div>')
    anh_em = ' · '.join(f'<a href="{u}">{t}</a>' for t, u in ANH_EM)
    if en:
        skip, home, nav_lab = 'Skip to content', '/en/', 'Main navigation'
        foot = (f'<div><p><strong>anuongvandong.com</strong> – free self-study on eating, movement, sleep, breathing '
                f'and meditation, by age.</p><p>Educational content. Not reviewed by a health professional. '
                f'No ads, no cookies, no tracking.</p></div>'
                f'<div><p><a href="/en/find-help/">Find help</a> · <a href="/en/disclaimer/">Disclaimer</a> · '
                f'<a href="/en/privacy/">Privacy</a> · <a href="/en/sources-and-updates/">Sources</a></p>'
                f'<p>Content: <a href="{GIAY_PHEP[1]}" rel="license noopener">{GIAY_PHEP[0]}</a> · Peter Tran. '
                f'Logo and name: all rights reserved.</p></div>'
                f'<div><p>Sister sites: {anh_em}</p><p>The Vietnamese version is the original.</p></div>')
    else:
        skip, home, nav_lab = 'Bỏ qua, đến nội dung', '/', 'Điều hướng chính'
        foot = (f'<div><p><strong>anuongvandong.com</strong> – tự học miễn phí về ăn uống, vận động, giấc ngủ, '
                f'thở và thiền theo độ tuổi.</p><p>Nội dung giáo dục, chưa được chuyên gia y tế đọc duyệt. '
                f'Không quảng cáo, không cookie, không theo dõi.</p></div>'
                f'<div><p><a href="/tim-tro-giup/">Tìm trợ giúp</a> · <a href="/mien-tru/">Miễn trừ</a> · '
                f'<a href="/rieng-tu/">Quyền riêng tư</a> · <a href="/nguon-va-cap-nhat/">Nguồn</a></p>'
                f'<p>Nội dung: <a href="{GIAY_PHEP[1]}" rel="license noopener">{GIAY_PHEP[0]}</a> · Peter Tran. '
                f'Logo và tên giữ mọi quyền.</p></div>'
                f'<div><p>Trang anh em: {anh_em}</p></div>')
    doc = f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="author" content="Peter Tran">
{robots}<link rel="canonical" href="{SITE}{path}">
{hreflang}<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#1b2a41">
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>
<a class="skip" href="#noi-dung">{skip}</a>
{banner}<header class="site-head">
  <div class="wrap">
    <a class="brand" href="{home}"><img src="/assets/logo/anuongvandong-icon.svg" alt="" width="40" height="40">anuongvandong.com</a>
    <nav class="nav" aria-label="{nav_lab}">{nav}</nav>
  </div>
</header>
<main id="noi-dung"><div class="wrap">
{body}
</div></main>
<footer class="site-foot"><div class="wrap"><div class="cols">{foot}</div></div></footer>
</body>
</html>
'''
    dich = os.path.join(out, path.lstrip('/'))
    if path.endswith('/'):
        dich = os.path.join(dich, 'index.html')
    os.makedirs(os.path.dirname(dich), exist_ok=True)
    with open(dich, 'w', encoding='utf-8') as f:
        f.write(doc)


TUOI_URL = {}  # (lang, ma tuổi) -> url trang nhóm tuổi đã đăng


def the_bai(b):
    m = b.meta
    en = b.lang == 'en'
    if b.loai == 'tuoi':
        return (f'<div class="lesson-meta"><span>{"Checked" if en else "Kiểm tra"}: {html.escape(str(m.get("checked")))}'
                f'</span><span>{"Author" if en else "Tác giả"}: Peter Tran</span></div>'
                + ('<div class="box warn small"><p>Educational content, not yet reviewed by a health professional.</p></div>'
                   if en else '<div class="box warn small"><p>Nội dung giáo dục, chưa được chuyên gia y tế đọc duyệt.'
                   '</p></div>'))
    if b.loai != 'bai':
        return ''
    nhan = [('Checked' if en else 'Kiểm tra'), str(m.get('checked')),
            ('Evidence' if en else 'Mức bằng chứng'), str(m.get('evidence_level'))]
    tuoi = ', '.join(
        (f'<a href="{TUOI_URL[(b.lang, str(a))]}">{html.escape(str(a))}</a>' if (b.lang, str(a)) in TUOI_URL
         else html.escape(str(a))) for a in (m.get('age_groups') or []))
    return (f'<div class="lesson-meta"><span>{nhan[0]}: {html.escape(nhan[1])}</span>'
            f'<span>{nhan[2]}: {html.escape(nhan[3])}</span>'
            f'<span>{"Ages" if en else "Tuổi"}: {tuoi}</span>'
            f'<span>{"Author" if en else "Tác giả"}: Peter Tran</span></div>'
            + ('<div class="box warn small"><p>Educational content, not yet reviewed by a health professional. '
               'It does not replace advice from a doctor who knows your health.</p></div>' if en else
               '<div class="box warn small"><p>Nội dung giáo dục, chưa được chuyên gia y tế đọc duyệt. '
               'Bài không thay lời khuyên của bác sĩ biết rõ sức khỏe của bạn.</p></div>'))


THU_TU_TRU = [('an-uong', 'Ăn uống', 'Eating'), ('van-dong', 'Vận động', 'Movement'),
              ('ngu-nghi', 'Ngủ và nghỉ', 'Sleep and rest'), ('tho', 'Thở', 'Breathing'),
              ('thien', 'Thiền chánh niệm', 'Mindfulness meditation'), ('tam-sinh-ly', 'Tâm sinh lý theo giai đoạn đời', 'Body and mind through life stages'),
              ('phuong-phap', 'Phương pháp tối giản', 'Minimal methods'), ('hieu-dung', 'Hiểu đúng – Ngộ nhận', 'Myths and facts'),
              ('bat-dau', 'Bắt đầu ở đây', 'Start here')]


def bai_theo_tru(trang_tuoi, ma, dang):
    """Danh sách bài (cùng ngôn ngữ) có age_groups chứa mã tuổi, chia theo trụ."""
    en = trang_tuoi.lang == 'en'
    out = ''
    for tru, ten, ten_en in THU_TU_TRU:
        ds = []
        for b in dang:
            if b.lang != trang_tuoi.lang or b.loai != 'bai':
                continue
            goc = b if b.lang == 'vi' else b.cap
            if not goc or goc.meta.get('pillar') != tru:
                continue
            if ma not in [str(a) for a in (b.meta.get('age_groups') or [])]:
                continue
            ds.append(b)
        if not ds:
            continue
        ds.sort(key=lambda x: x.meta.get('order', 999))
        the = ''.join(
            f'<a class="card" href="{b.url}"><h3>{html.escape(b.title)}</h3>'
            f'<p class="small">{html.escape(str(b.meta.get("short", "")))}</p>'
            + ('' if b.published else f'<span class="tag soon">{"draft" if en else "nháp"}</span>') + '</a>'
            for b in ds)
        out += f'<h3 class="tru">{html.escape(ten_en if en else ten)}</h3><div class="grid">{the}</div>'
    return out or ('<p>No articles yet.</p>' if en else '<p>Chưa có bài.</p>')


def build(out, preview):
    ds = doc_bai()
    loi_tong = []
    dang = []
    for b in ds:
        if b.published:
            loi = kiem_tra(b)
            if loi:
                loi_tong.append(f'{b.path}: ' + '; '.join(loi))
            dang.append(b)
        elif preview:
            dang.append(b)
    if loi_tong:
        raise LoiNoiDung('\n  ' + '\n  '.join(loi_tong))

    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    shutil.copytree(os.path.join(GOC, 'assets'), os.path.join(out, 'assets'))
    for fn in ('favicon.svg', 'favicon.ico', 'apple-touch-icon.png'):
        shutil.copy(os.path.join(GOC, 'assets', 'logo', fn), os.path.join(out, fn))

    alt = {}
    for b in dang:
        if b.cap and (b.cap in dang):
            alt[b.url] = b.cap.url
    tuoi_ds = yaml.safe_load(open(os.path.join(GOC, 'data', 'tuoi.yaml'), encoding='utf-8'))['nhom']
    tuoi_ma = {t['slug']: str(t.get('ma', '')) for t in tuoi_ds}
    TUOI_URL.clear()
    for b in dang:
        if b.loai == 'tuoi' and b.published:
            vi_slug = b.slug if b.lang == 'vi' else b.meta.get('pair')
            if tuoi_ma.get(vi_slug):
                TUOI_URL[(b.lang, tuoi_ma[vi_slug])] = b.url
    da_co = set()
    for b in dang:
        noi_dung = md_html(b.md)
        if b.loai == 'tuoi':
            vi_slug = b.slug if b.lang == 'vi' else b.meta.get('pair')
            noi_dung = noi_dung.replace('<p>{{BAI_THEO_TRU}}</p>', bai_theo_tru(b, tuoi_ma.get(vi_slug), dang))
        body = (f'<article class="lesson"><h1>{html.escape(b.title)}</h1>{the_bai(b)}{noi_dung}</article>')
        trang(out, b.url, b.title, str(b.meta.get('short', b.title)), body, b.lang, alt.get(b.url),
              preview=preview, nhap=not b.published)
        da_co.add(b.url)

    import yaml as _y
    khung = _y.safe_load(open(os.path.join(GOC, 'data', 'khung.yaml'), encoding='utf-8'))['phan']
    tuoi = _y.safe_load(open(os.path.join(GOC, 'data', 'tuoi.yaml'), encoding='utf-8'))['nhom']
    co_bai = {(b.lang, b.slug if b.lang == 'vi' else b.meta.get('pair')): b for b in dang}

    def khung_html(lang):
        en = lang == 'en'
        s = ''
        for p in khung:
            items = ''
            for x in p['bai']:
                b = co_bai.get((lang, x['slug']))
                ten = html.escape(x['ten_en'] if en else x['ten'])
                if b:
                    nhan = '' if b.published else f' <span class="tag soon">{"draft" if en else "nháp"}</span>'
                    items += f'<li><a href="{b.url}">{ten}</a>{nhan}</li>'
                else:
                    ghi = []
                    if x.get('rui_ro'):
                        ghi.append('high-risk topic: draft only' if en else 'chủ đề rủi ro cao: chỉ để nháp')
                    ghi.append(('phase ' if en else 'pha ') + str(x.get('pha', 1)))
                    items += (f'<li>{ten} <span class="muted small">({"coming" if en else "sắp có"} · '
                              f'{"; ".join(ghi)})</span></li>')
            s += (f'<section class="card khung"><h2><span class="ma">{p["so"]}</span> '
                  f'{html.escape(p["ten_en"] if en else p["ten"])}</h2>'
                  f'<p class="small"><strong>{"Goal" if en else "Mục tiêu"}:</strong> '
                  f'{html.escape(p["muc_tieu_en"] if en else p["muc_tieu"])}</p><ul>{items}</ul></section>')
        return s

    def tuoi_html(lang):
        en = lang == 'en'
        rows = ''
        for t in tuoi:
            moc = t.get('moc_en' if en else 'moc') or '–'
            pha = ('Phase ' if en else 'Pha ') + str(t['pha'])
            ghi = (' · high-risk: drafts only' if en else ' · rủi ro cao: chỉ để nháp') if t.get('rui_ro') else ''
            ten = html.escape(t["ten_en"] if en else t["ten"])
            u = TUOI_URL.get((lang, str(t.get('ma', ''))))
            if u:
                ten = f'<a href="{u}">{ten}</a>'
                pha = 'Articles available' if en else 'Đã có bài'
            rows += (f'<tr><th scope="row">{ten}</th>'
                     f'<td>{html.escape(moc)}</td><td>{pha}{ghi}</td></tr>')
        hd = ('<th>Group</th><th>Ages</th><th>Status</th>' if en else '<th>Nhóm</th><th>Tuổi</th><th>Trạng thái</th>')
        return f'<div class="table-wrap"><table><thead><tr>{hd}</tr></thead><tbody>{rows}</tbody></table></div>'

    tru = [('an-uong', 'Ăn uống', 'Eating', 'Muối, đường, đĩa ăn, đạm, nước, rượu bia.',
            'Salt, sugar, the plate, protein, water, alcohol.'),
           ('van-dong', 'Vận động', 'Movement', 'Phút vận động, sức mạnh, thăng bằng, ngồi lâu.',
            'Active minutes, strength, balance, sitting.'),
           ('ngu-nghi', 'Ngủ và nghỉ', 'Sleep and rest', 'Giờ ngủ theo tuổi và thói quen giúp ngủ.',
            'Sleep hours by age and habits that help.'),
           ('tho', 'Thở', 'Breathing', 'Thở chậm, và khi nào không nên tập.', 'Slow breathing, and when not to.'),
           ('thien', 'Thiền chánh niệm', 'Mindfulness', 'Thiền thế tục, liều nhỏ, biết khi nào dừng.',
            'Secular practice, small doses, knowing when to stop.')]

    def muc(path_vi, path_en, t_vi, d_vi, b_vi, t_en, d_en, b_en, cur_vi=None, cur_en=None):
        if path_vi not in da_co:
            trang(out, path_vi, t_vi, d_vi, b_vi, 'vi', path_en, cur_vi, preview)
            da_co.add(path_vi)
        if path_en not in da_co:
            trang(out, path_en, t_en, d_en, b_en, 'en', path_vi, cur_en, preview)
            da_co.add(path_en)

    mau = co_bai.get(('vi', 'muoi'))
    mau_en = co_bai.get(('en', 'muoi'))
    the_tru = lambda en: ''.join(
        f'<div class="card"><h3>{t[2] if en else t[1]}</h3><p class="small">{t[4] if en else t[3]}</p></div>'
        for t in tru)
    muc('/', '/en/',
        'Ăn Uống Vận Động – anuongvandong.com',
        'Tự học miễn phí về ăn uống, vận động, giấc ngủ, thở và thiền theo độ tuổi, dựa trên hướng dẫn chính thức.',
        '<section class="hero"><div><p class="eyebrow">Tự học miễn phí · song ngữ</p><h1>Ăn Uống Vận Động</h1>'
        '<p class="lead">Ăn uống, vận động, giấc ngủ, thở và thiền theo từng độ tuổi. Mỗi con số có nguồn, '
        'phiên bản và ngày kiểm tra. Khi các chuẩn WHO, Việt Nam, Mỹ, Úc, Anh nói khác nhau, site đặt chúng '
        'cạnh nhau.</p><div class="cta"><a class="btn primary" href="/khung-chuong-trinh/">Xem khung chương trình</a>'
        + ''.join(f' <a class="btn" href="{TUOI_URL[("vi", m)]}">Theo tuổi: {m.replace("-", "–")}</a>' for m in ('18-39', '40-64') if ('vi', m) in TUOI_URL)
        + (f'<a class="btn" href="{mau.url}">Đọc bài mẫu: Muối</a>' if mau else '') +
        '</div></div><img src="/assets/logo/anuongvandong-logo.svg" alt="Logo Ăn Uống Vận Động" width="260" '
        'height="278"></section>'
        '<h2>Năm trụ</h2><div class="grid">' + the_tru(False) + '</div>'
        '<div class="box"><h2>Site này làm gì</h2><ul><li>Chuyển hướng dẫn chính thức và nghiên cứu có bình duyệt '
        'thành bài ngắn, dễ đọc trên điện thoại.</li><li>Pha 1: người lớn 18–64 tuổi và các phương pháp tối giản. '
        'Pha 2: trẻ em.</li><li>Không chẩn đoán, không tư vấn cá nhân, không bán gì.</li></ul></div>'
        '<div class="box warn"><p><strong>Cần cấp cứu?</strong> Xem <a href="/tim-tro-giup/">Tìm trợ giúp</a>.</p></div>',
        'Ăn Uống Vận Động – Eat Well, Move Well – anuongvandong.com',
        'Free self-study on eating, movement, sleep, breathing and meditation by age, based on official guidelines.',
        '<section class="hero"><div><p class="eyebrow">Free self-study · bilingual</p><h1>Ăn Uống Vận Động – '
        'Eat Well, Move Well</h1><p class="lead">Eating, movement, sleep, breathing and meditation for each age '
        'group. Every figure comes with its source, version and check date. Where WHO, Vietnam, the US, Australia '
        'and the UK disagree, the site shows them side by side.</p><div class="cta"><a class="btn primary" '
        'href="/en/curriculum/">See the curriculum</a>'
        + ''.join(f' <a class="btn" href="{TUOI_URL[("en", m)]}">By age: {m.replace("-", "–")}</a>' for m in ('18-39', '40-64') if ('en', m) in TUOI_URL)
        + (f'<a class="btn" href="{mau_en.url}">Sample article: Salt</a>' if mau_en else '') +
        '</div></div><img src="/assets/logo/anuongvandong-logo.svg" alt="Ăn Uống Vận Động logo" width="260" '
        'height="278"></section>'
        '<h2>Five pillars</h2><div class="grid">' + the_tru(True) + '</div>'
        '<div class="box"><h2>What the site does</h2><ul><li>Turns official guidelines and peer-reviewed research '
        'into short articles that read well on a phone.</li><li>Phase 1: adults 18–64 and minimal methods. Phase 2: '
        'children.</li><li>No diagnosis, no personal advice, nothing for sale.</li></ul></div>'
        '<p class="small muted">The site is written for Vietnamese readers; the Vietnamese version is the '
        'original.</p>'
        '<div class="box warn"><p><strong>Emergency?</strong> See <a href="/en/find-help/">Find help</a>.</p></div>',
        '/', '/en/')

    muc('/khung-chuong-trinh/', '/en/curriculum/',
        'Khung chương trình', 'Mười phần, mỗi phần có mục tiêu đo được.',
        '<h1>Khung chương trình</h1><p class="lead">Mười phần. Mỗi phần có một mục tiêu đo được. '
        'Bài có link là bài đã đăng; bài khác đang viết.</p>' + khung_html('vi'),
        'Curriculum', 'Ten parts, each with a measurable goal.',
        '<h1>Curriculum</h1><p class="lead">Ten parts. Each part has one measurable goal. Linked titles are '
        'published; the rest are being written.</p>' + khung_html('en'),
        '/khung-chuong-trinh/', '/en/curriculum/')

    muc('/theo-tuoi/', '/en/by-age/',
        'Theo tuổi', 'Các nhóm tuổi của site và tình trạng nội dung.',
        '<h1>Theo tuổi</h1><p>Mốc tuổi bám theo các hướng dẫn chính thức. Các hướng dẫn không chia tuổi giống '
        'nhau, nên mỗi bài sẽ ghi rõ mốc của từng chuẩn.</p>' + tuoi_html('vi') +
        '<p class="small muted">Nhóm "rủi ro cao" (mang thai, trẻ dưới 2 tuổi…) chỉ có bài khi có người có chuyên '
        'môn đọc duyệt.</p>',
        'By age', 'The age groups on this site and the status of their content.',
        '<h1>By age</h1><p>Age bands follow the official guidelines. The guidelines do not all split ages the same '
        'way, so each article states the bands each standard uses.</p>' + tuoi_html('en') +
        '<p class="small muted">"High-risk" groups (pregnancy, children under 2…) get articles only once a qualified '
        'reviewer has read them.</p>',
        '/theo-tuoi/', '/en/by-age/')

    trang(out, '/404.html', 'Không tìm thấy trang / Page not found', 'Trang không tồn tại.',
          '<h1>Không tìm thấy trang</h1><p>Trang này không có hoặc đã đổi địa chỉ.</p>'
          '<p><a class="btn primary" href="/">Về trang chủ</a></p><h2 lang="en">Page not found</h2>'
          '<p lang="en"><a class="btn" href="/en/">English home page</a></p>', 'vi', None, None, preview)

    with open(os.path.join(out, '_headers'), 'w', encoding='utf-8') as f:
        f.write(HEADERS + ('  X-Robots-Tag: noindex, nofollow\n' if preview else ''))
    with open(os.path.join(out, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write('User-agent: *\nDisallow: /\n' if preview else
                f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')
    homnay = dt.date.today().isoformat()
    with open(os.path.join(out, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + ''.join(f'  <url><loc>{SITE}{u}</loc><lastmod>{homnay}</lastmod></url>\n' for u in sorted(da_co))
                + '</urlset>\n')
    return dang


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', action='store_true')
    a = ap.parse_args()
    out = os.path.join(GOC, '_preview' if a.preview else 'public')
    try:
        dang = build(out, a.preview)
    except LoiNoiDung as e:
        print('DỪNG BUILD:', e, file=sys.stderr)
        sys.exit(1)
    print(f'Đã build {len(dang)} bài/trang nội dung -> {out}')


if __name__ == '__main__':
    main()
