#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Py-Intruder - Asynchronous HTTP Intruder Tool
Cong cu fuzzer va brute-force HTTP bat dong bo hieu nang cao.
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
    Gui request GET bat dong bo sau khi chen payload vao URL.

    Args:
        client (httpx.AsyncClient): Client HTTP bat dong bo dung chung.
        target_url (str): URL muc tieu co chua ky tu §§.
        payload (str): Payload dung de thay the §§.
        semaphore (asyncio.Semaphore): Bo gioi han so request chay song song.
    """
    # Thay ky tu §§ bang payload thuc te
    formatted_url = target_url.replace("§§", payload)

    # Dung semaphore de gioi han so luong request chay cung luc
    async with semaphore:
        try:
            # Gui request GET kem theo timeout 10 giay
            response = await client.get(formatted_url, timeout=10.0)
            
            # In ra ket qua theo dung format
            print(f"Payload: {payload:<20} | Status: {response.status_code}")
            
        except httpx.RequestError as exc:
            # Log loi neu khong ket noi duoc hoac bi timeout
            print(f"Payload: {payload:<20} | Status: ERROR (Request failed: {exc})")
        except Exception as exc:
            # Bat cac loi ngoai le khac phat sinh
            print(f"Payload: {payload:<20} | Status: ERROR (Unexpected: {exc})")


async def run_intruder(target_url: str, wordlist_path: str, num_workers: int) -> None:
    """
    Doc file wordlist va quan ly viec gui cac request bat dong bo.

    Args:
        target_url (str): URL muc tieu can test.
        wordlist_path (str): Duong dan file wordlist chua payload.
        num_workers (int): So luong luong chay song song.
    """
    # Check xem file wordlist co ton tai thuc su khong
    if not os.path.isfile(wordlist_path):
        print(f"Error: Wordlist file not found at: {wordlist_path}", file=sys.stderr)
        sys.exit(1)

    # Bat buoc URL phai co ky tu §§ de map payload
    if "§§" not in target_url:
        print("Error: Target URL must contain '§§' placeholder.", file=sys.stderr)
        sys.exit(1)

    # Doc toan bo payload tu file, bo dong trong va khoang trang thua
    try:
        with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
            payloads = [line.strip() for line in f if line.strip()]
        # Truong hop dac biet can catch
    except Exception as e:
        print(f"Error reading wordlist: {e}", file=sys.stderr)
        sys.exit(1)

    if not payloads:
        print("Error: Wordlist file is empty.", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Starting intruder with {len(payloads)} payloads.")
    print(f"[*] Concurrency limit (Workers): {num_workers}")
    print("-" * 60)

    # Khoi tao semaphore de kiem soat luong
    semaphore = asyncio.Semaphore(num_workers)

    # Dung chung mot client session de tiet kiem tai nguyen va tang toc
    async with httpx.AsyncClient() as client:
        # Tao list cac task can chay
        tasks = [
            send_request(client, target_url, payload, semaphore)
            for payload in payloads
        ]
        # Chay tat ca cac task cung mot luc
        await asyncio.gather(*tasks)

    print("-" * 60)
    print("[*] Scan completed.")


def main() -> None:
    """
    Ham entry point de cau hinh argparse va chay event loop.
    """
    parser = argparse.ArgumentParser(
        description="Py-Intruder - High-performance asynchronous HTTP fuzzer."
    )
    
    # Dinh nghia cac tham so dong lenh
    parser.add_argument(
        "-u", "--url",
        required=True,
        help="Target URL containing '§§' placeholder (e.g., http://example.com/?q=§§)"
    )
    parser.add_argument(
        "-f", "--wordlist",
        required=True,
        help="Path to the wordlist file"
    )
    parser.add_argument(
        "-c", "--workers",
        type=int,
        default=10,
        help="Number of concurrent workers (Default: 10)"
    )

    args = parser.parse_args()

    # Chay async event loop de xu ly
    try:
        asyncio.run(run_intruder(args.url, args.wordlist, args.workers))
    except KeyboardInterrupt:
        print("\n[!] Process interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
