#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Py-Intruder - Asynchronous HTTP Intruder Tool
Công cụ kiểm thử xâm nhập HTTP bất đồng bộ thay thế Burp Suite Intruder.
"""

import argparse
import asyncio
import sys
import os
import httpx


async def send_request(
    client: httpx.AsyncClient,
    target_url: str,
    payload: str,
    semaphore: asyncio.Semaphore
) -> None:
    """
    Gửi một HTTP GET request bất đồng bộ sau khi thay thế payload vào URL.

    Args:
        client (httpx.AsyncClient): HTTP client bất đồng bộ dùng chung.
        target_url (str): URL mục tiêu chứa ký tự placeholders '§§'.
        payload (str): Chuỗi payload dùng để thay thế placeholders.
        semaphore (asyncio.Semaphore): Đối tượng giới hạn số lượng request song song.
    """
    # Thay thế ký tự §§ bằng payload thực tế
    formatted_url = target_url.replace("§§", payload)

    # Sử dụng semaphore để kiểm soát giới hạn workers chạy đồng thời
    async with semaphore:
        try:
            # Gửi request GET bất đồng bộ với cấu hình timeout mặc định 10 giây
            response = await client.get(formatted_url, timeout=10.0)
            
            # In kết quả định dạng cơ bản: Payload: [content] | Status: [code]
            print(f"Payload: {payload:<20} | Status: {response.status_code}")
            
        except httpx.RequestError as exc:
            # Xử lý các lỗi kết nối, DNS hoặc HTTP protocol
            print(f"Payload: {payload:<20} | Status: ERROR (Request failed: {exc})")
        except Exception as exc:
            # Xử lý các lỗi ngoại lệ phát sinh ngoài ý muốn khác
            print(f"Payload: {payload:<20} | Status: ERROR (Unexpected: {exc})")


async def run_intruder(target_url: str, wordlist_path: str, num_workers: int) -> None:
    """
    Hàm điều phối chính đọc wordlist và quản lý vòng đời của các tiến trình bất đồng bộ.

    Args:
        target_url (str): URL mục tiêu cần fuzzing.
        wordlist_path (str): Đường dẫn đến file chứa các payload.
        num_workers (int): Giới hạn số lượng request chạy song song tối đa.
    """
    # Kiểm tra sự tồn tại của file Wordlist trước khi thực thi
    if not os.path.isfile(wordlist_path):
        print(f"Lỗi: File wordlist không tồn tại tại đường dẫn: {wordlist_path}", file=sys.stderr)
        sys.exit(1)

    # Kiểm tra xem URL mục tiêu có chứa ký tự §§ hay không
    if "§§" not in target_url:
        print("Lỗi: URL mục tiêu phải chứa ký tự placeholders '§§' để thay thế payload.", file=sys.stderr)
        sys.exit(1)

    # Đọc danh sách payload từ file wordlist
    try:
        with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
            # Loại bỏ khoảng trắng và dòng trống ở đầu/cuối của mỗi dòng
            payloads = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Lỗi khi đọc file wordlist: {e}", file=sys.stderr)
        sys.exit(1)

    if not payloads:
        print("Lỗi: File wordlist rỗng.", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Bắt đầu kiểm thử với {len(payloads)} payloads.")
    print(f"[*] Số lượng luồng song song (Workers): {num_workers}")
    print("-" * 60)

    # Khởi tạo Semaphore để giới hạn số lượng request song song thực tế hoạt động
    semaphore = asyncio.Semaphore(num_workers)

    # Khởi tạo AsyncClient để tái sử dụng connection pool, tối ưu hiệu năng
    async with httpx.AsyncClient() as client:
        # Tạo danh sách các task bất đồng bộ
        tasks = [
            send_request(client, target_url, payload, semaphore)
            for payload in payloads
        ]
        # Kích hoạt thực thi đồng thời tất cả các task bằng asyncio.gather
        await asyncio.gather(*tasks)

    print("-" * 60)
    print("[*] Hoàn thành quá trình quét.")


def main() -> None:
    """
    Hàm entry point của script. Cấu hình argparse và tiếp nhận các đối số từ CLI.
    """
    parser = argparse.ArgumentParser(
        description="Py-Intruder - Công cụ fuzzer HTTP bất đồng bộ hiệu năng cao."
    )
    
    # Định nghĩa các tham số đầu vào cho chương trình
    parser.add_argument(
        "-u", "--url",
        required=True,
        help="URL mục tiêu (cần chứa ký tự '§§' để chèn payload, ví dụ: http://example.com/?q=§§)"
    )
    parser.add_argument(
        "-f", "--wordlist",
        required=True,
        help="Đường dẫn đến file wordlist (chứa danh sách payload)"
    )
    parser.add_argument(
        "-c", "--workers",
        type=int,
        default=10,
        help="Số lượng kết nối song song (Mặc định: 10)"
    )

    args = parser.parse_args()

    # Thực thi vòng lặp sự kiện bất đồng bộ chính (Asyncio Event Loop)
    try:
        asyncio.run(run_intruder(args.url, args.wordlist, args.workers))
    except KeyboardInterrupt:
        print("\n[!] Tiến trình bị hủy bởi người dùng.")
        sys.exit(0)


if __name__ == "__main__":
    main()
