# anuongvandong.com

Website tự học miễn phí, song ngữ Việt – Anh, về ăn uống, vận động, giấc ngủ, thở và thiền theo độ tuổi. Tác giả: **Peter Tran**.

- Nội dung: CC BY 4.0. Logo và tên "Ăn Uống Vận Động": giữ mọi quyền.
- Không cookie, không theo dõi, không quảng cáo.

## Build

```
pip install markdown pyyaml
python3 _build/build.py            # bản công khai -> public/
python3 _build/build.py --preview  # có cả nháp -> _preview/ (không commit)
python3 _build/art/logo_art.py     # sinh 3 phương án logo
```

Cloudflare Pages: build command để trống, output `public`. Push `main` là tự đăng.

## Cấu trúc

```
data/khung.yaml     khung chương trình (10 phần)
data/tuoi.yaml      nhóm tuổi
content/vi/*.md     bài tiếng Việt (bản gốc)
content/en/*.md     bài tiếng Anh (pair: slug bài Việt)
content/nhap/       nháp chủ đề rủi ro cao (.gitignore)
_build/build.py     sinh trang; dừng build nếu bài công khai vi phạm quy tắc
_build/art/         vẽ logo bằng mã
```
