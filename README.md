# Py-Intruder

Công cụ kiểm thử xâm nhập HTTP bất đồng bộ hiệu năng cao viết bằng Python, được thiết kế để thay thế cho tính năng Burp Suite Intruder (bản Community vốn giới hạn tốc độ). 

Công cụ sử dụng thư viện `httpx` và cơ chế `asyncio` để tối ưu hóa việc gửi yêu cầu đồng thời (concurrency), giúp tăng tốc độ quét lỗ hổng bảo mật, brute-force hoặc fuzzing đường dẫn web.

## Tính năng nổi bật
* **Tốc độ vượt trội**: Tận dụng tối đa sức mạnh của xử lý bất đồng bộ (Asynchronous I/O) giúp hoàn thành hàng nghìn request chỉ trong vài giây.
* **Kiểm soát luồng thông minh**: Hỗ trợ cơ chế Semaphore giới hạn số lượng request song song (Workers) để tránh quá tải hệ thống đích hoặc gây nghẽn băng thông.
* **Nhắm mục tiêu linh hoạt**: Tự động phát hiện ký tự `§§` trong URL mục tiêu để chèn payload từ wordlist (tương tự như chế độ Sniper).

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

```bash
python intruder.py -u <TARGET_URL> -f <WORDLIST_PATH> -c <NUM_WORKERS>
```

### Các tham số cấu hình:
* `-u`, `--url`: URL mục tiêu cần kiểm tra, chứa ký tự `§§` tại vị trí muốn thay thế payload (Ví dụ: `http://example.com/login?user=§§`).
* `-f`, `--wordlist`: Đường dẫn đến file wordlist chứa danh sách payload (mỗi dòng một payload).
* `-c`, `--workers`: Số lượng request gửi đi song song tại một thời điểm (Mặc định: 10).

### Ví dụ thực tế:
```bash
python intruder.py -u "https://httpbin.org/anything?name=§§" -f payloads.txt -c 20
```

## Định dạng đầu ra (Output)
Chương trình hiển thị trực tiếp kết quả phản hồi của từng request trên console theo định dạng:
```text
Payload: [nội_dung_payload] | Status: [mã_trạng_thai_HTTP]
```
Nếu có lỗi kết nối hoặc timeout xảy ra, chương trình sẽ hiển thị thông báo lỗi tương ứng thay vì mã trạng thái.
