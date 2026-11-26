# App Android – Ăn Uống Vận Động (anuongvandong.com)

Bọc trang tĩnh `public/` thành app bằng Capacitor 8. Nội dung đóng gói sẵn, đọc được khi mất mạng.
Không tài khoản, không quảng cáo, không theo dõi; tiến độ, bài đã lưu, ghi chú chỉ nằm trên máy
(localStorage `auvd.v1`, tắt sao lưu đám mây).

```
app/build_www.py            public/ → app/www/ (link tuyệt đối → tương đối, bỏ header web, chèn khung app, sinh app/index.js)
app/shell/                  app.css, app.js – thanh trên, 5 tab (Trang chủ · Học · Sách · Trợ giúp · Của tôi), cài đặt Aa, tiến độ, ghi chú, tìm không dấu
app/capacitor.config.json   appId com.anuongvandong.app (KHÔNG đổi được sau lần tải lên Play đầu tiên – chờ Peter chốt)
app/android/                dự án Android (targetSdk 36, minSdk 24)
```

## Sách – chỗ chừa sẵn
Tab **Sách** đã có; hiện báo "Sách đang được viết". Khi sách xong:
1. Đặt dữ liệu sách (out/app/ của mã sách: `manifest.json` + `chapters/*.json`) vào `app/sach-data/` (đã .gitignore, không đưa lên GitHub công khai).
2. Thêm `app/build_book.py` có hàm `build(BOOK, WWW, HEAD_JS)` – chép khuôn từ nhánh `app` của repo trachnhiemxahoi.
3. Chạy lại `build_www.py`. Không phải sửa `app.js`.
4. Trước khi phát hành sách trong app công khai: hỏi NXB (Luật 17/2026/QH16, hiệu lực 01/3/2027 – đang đối chiếu).

## Build
```
python3 _build/build.py           # cập nhật public/ (nhánh main)
cd app && npm ci
python3 build_www.py && npx cap sync android
cd android && ./gradlew assembleDebug      # cần ANDROID_HOME / local.properties
```
Đẩy nhánh `app` → GitHub Actions build APK bản thử (artifact, giữ 30 ngày).
Nhánh `app` lấy `public/` từ `main`: trước mỗi bản app, `git merge main`.
