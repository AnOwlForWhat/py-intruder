#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Py-Intruder - Asynchronous HTTP Intruder Tool
Cong cu brute-force HTTP bat dong bo ho tro chao payload vao ca URL va Headers.
"""

import argparse
import asyncio
import sys
import os
import itertools
import httpx


async def send_request(
    client: httpx.AsyncClient,
    target_url: str,
    raw_headers: list,
    payload1: str,
    payload2: str,
    semaphore: asyncio.Semaphore,
    results: list
) -> None:
    """
    Gui request GET bat dong bo va chen payload vao URL hoac Headers.

    Args:
        client (httpx.AsyncClient): Client HTTP bat dong bo dung chung.
        target_url (str): URL muc tieu.
        raw_headers (list): Danh sach cac header tho co the chua placeholder.
        payload1 (str): Payload thay the cho §§ hoac §1§.
        payload2 (str): Payload thay the cho §2§ (neu co).
        semaphore (asyncio.Semaphore): Bo gioi han so request chay song song.
        results (list): List de luu lai ket qua sau khi scan xong.
    """
    # Xu ly thay the payload trong URL
    formatted_url = target_url
    if "§§" in target_url:
        formatted_url = formatted_url.replace("§§", payload1)
    elif "§1§" in target_url or "§2§" in target_url:
        formatted_url = formatted_url.replace("§1§", payload1).replace("§2§", payload2)

    # Xu ly thay the payload trong Headers
    headers = {}
    for raw_header in raw_headers:
        if ":" in raw_header:
            key, val = raw_header.split(":", 1)
            key = key.strip()
            val = val.strip()

            # Thay the placeholder trong gia tri header
            if "§§" in val:
                val = val.replace("§§", payload1)
            elif "§1§" in val or "§2§" in val:
                val = val.replace("§1§", payload1).replace("§2§", payload2)
            
            headers[key] = val

    async with semaphore:
        try:
            # Gui request voi custom headers, bo qua xac thuc SSL
            response = await client.get(formatted_url, headers=headers, timeout=10.0)
            status_code = response.status_code
        except httpx.RequestError as exc:
            status_code = f"ERROR (Connection failed: {exc})"
        except Exception as exc:
            status_code = f"ERROR (Unexpected: {exc})"

        result_entry = {
            "p1": payload1,
            "p2": payload2,
            "status": status_code
        }
        results.append(result_entry)

        # In ket qua thoi gian thuc ra man hinh console
        if payload2:
            print(f"Payload 1: {payload1:<5} | Payload 2: {payload2:<5} | Status: {status_code}")
        else:
            print(f"Payload: {payload1:<15} | Status: {status_code}")


def load_wordlist(source: str) -> list:
    """
    Doc file wordlist hoac tu dong tao day so tu range:X-Y.
    """
    if source.startswith("range:"):
        try:
            parts = source.split(":")[1].split("-")
            start, end = int(parts[0]), int(parts[1])
            return [str(i) for i in range(start, end + 1)]
        except Exception as e:
            print(f"Error parsing range format '{source}': {e}", file=sys.stderr)
            sys.exit(1)

    if not os.path.isfile(source):
        print(f"Error: Wordlist file not found at: {source}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(source, "r", encoding="utf-8", errors="ignore") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file '{source}': {e}", file=sys.stderr)
        sys.exit(1)


async def run_intruder(
    target_url: str,
    raw_headers: list,
    w1_list: list,
    w2_list: list,
    is_cb: bool,
    num_workers: int
) -> None:
    """
    Ham dieu phoi chinh doc payload va chay chuong trinh scan.
    """
    # Gop toan bo cac vung can quet de kiem tra su ton tai cua placeholder
    combined_targets = target_url + "".join(raw_headers)
    
    has_single = "§§" in combined_targets
    has_double = "§1§" in combined_targets and "§2§" in combined_targets

    if not has_single and not has_double:
        print("Error: Target URL or Headers must contain either '§§' (Sniper) or both '§1§' and '§2§' (Cluster Bomb).", file=sys.stderr)
        sys.exit(1)

    if is_cb:
        combinations = list(itertools.product(w1_list, w2_list))
    else:
        combinations = [(p1, "") for p1 in w1_list]

    total_requests = len(combinations)
    print(f"[*] Starting scan with {total_requests} total requests.")
    print(f"[*] Concurrency limit (Workers): {num_workers}")
    print("-" * 60)

    semaphore = asyncio.Semaphore(num_workers)
    results = []

    limits = httpx.Limits(max_keepalive_connections=num_workers, max_connections=num_workers)
    async with httpx.AsyncClient(verify=False, limits=limits) as client:
        tasks = [
            send_request(client, target_url, raw_headers, p1, p2, semaphore, results)
            for p1, p2 in combinations
        ]
        await asyncio.gather(*tasks)

    print("-" * 60)
    print("[*] Scan completed.")

    if is_cb:
        print("\n[*] Summary of successful hits (Status 500 / Errors):")
        try:
            sorted_results = sorted(results, key=lambda x: int(x["p1"]))
        except ValueError:
            sorted_results = sorted(results, key=lambda x: x["p1"])

        for r in sorted_results:
            if r["status"] == 500:
                print(f"Position: {r['p1']:<4} | Character: {r['p2']:<4} | Status: {r['status']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Py-Intruder - High-performance asynchronous fuzzer supporting Sniper and Cluster Bomb."
    )
    
    # URL muc tieu
    parser.add_argument(
        "-u", "--url",
        required=True,
        help="Target URL"
    )

    # Thiet lap Header tuy chon (ho tro truyen nhieu lan)
    parser.add_argument(
        "-H", "--header",
        action="append",
        default=[],
        help="Custom HTTP Header (e.g. -H 'Cookie: session=xyz'). Can contain placeholders."
    )

    # Option bat tat cac che do scan
    parser.add_argument(
        "--sniper",
        action="store_true",
        help="Force Sniper attack mode"
    )
    parser.add_argument(
        "--cb",
        action="store_true",
        help="Force Cluster Bomb attack mode"
    )

    # Nguon nap wordlist
    parser.add_argument(
        "-f", "--wordlist",
        help="Path to primary wordlist or range (e.g. range:1-20)"
    )
    parser.add_argument(
        "-f2", "--wordlist2",
        help="Path to secondary wordlist"
    )

    # Tu dong sinh payload
    parser.add_argument(
        "-az",
        action="store_true",
        help="Generate and use lowercase alphabet (a-z) as payload"
    )
    parser.add_argument(
        "-09",
        dest="zero_nine",
        action="store_true",
        help="Generate and use digits (0-9) as payload"
    )
    
    # So luong workers chay dong thoi
    parser.add_argument(
        "-c", "--workers",
        type=int,
        default=10,
        help="Number of concurrent connections (Default: 10)"
    )

    args = parser.parse_args()

    # Bieu dien nguyen trang bo qua SSL warnings
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except ImportError:
        pass

    # Gop chuoi ky tu tu dong
    generated_chars = ""
    if args.az:
        generated_chars += "abcdefghijklmnopqrstuvwxyz"
    if args.zero_nine:
        generated_chars += "0123456789"
    generated_list = list(generated_chars) if generated_chars else []

    # Xac dinh che do chay
    combined_targets = args.url + "".join(args.header)
    is_cb = args.cb or (not args.sniper and "§1§" in combined_targets and "§2§" in combined_targets)

    w1_list = []
    w2_list = []

    if is_cb:
        if args.wordlist:
            w1_list = load_wordlist(args.wordlist)
        else:
            print("Error: Primary wordlist (-f) is required for Cluster Bomb mode.", file=sys.stderr)
            sys.exit(1)

        if args.wordlist2:
            w2_list = load_wordlist(args.wordlist2)
        elif generated_list:
            w2_list = generated_list
        else:
            print("Error: Secondary wordlist (-f2) or generator flags (-az / -09) required for Cluster Bomb mode.", file=sys.stderr)
            sys.exit(1)
    else:
        if args.wordlist:
            w1_list = load_wordlist(args.wordlist)
        elif generated_list:
            w1_list = generated_list
        else:
            print("Error: Wordlist (-f) or generator flags (-az / -09) required for Sniper mode.", file=sys.stderr)
            sys.exit(1)

    try:
        asyncio.run(run_intruder(args.url, args.header, w1_list, w2_list, is_cb, args.workers))
    except KeyboardInterrupt:
        print("\n[!] Process interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
