#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import sys
import os
import time

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass


def inject(s, p1, p2):
    if not s:
        return ""
    if "§§" in s:
        return s.replace("§§", p1)
    return s.replace("§1§", p1).replace("§2§", p2)


async def send_req(client, method, url, hdrs, data, p1, p2, sem, res):
    # build request targets
    target_url = inject(url, p1, p2)
    
    headers = {}
    for h in hdrs:
        if ":" in h:
            k, v = h.split(":", 1)
            headers[k.strip()] = inject(v.strip(), p1, p2)

    target_data = inject(data, p1, p2)

    async with sem:
        t0 = time.time()
        try:
            if method.upper() == "POST":
                resp = await client.request(method, target_url, headers=headers, content=target_data, timeout=20.0)
            else:
                resp = await client.request(method, target_url, headers=headers, timeout=20.0)
            status = resp.status_code
        except Exception:
            status = "ERR"
        
        dt = time.time() - t0
        res.append({"p1": p1, "p2": p2, "status": status, "time": dt})
        
        # log realtime ket qua
        if p2:
            print(f"P1: {p1:<4} | P2: {p2:<4} | Status: {status:<5} | Time: {dt:.2f}s")
        else:
            print(f"Payload: {p1:<12} | Status: {status:<5} | Time: {dt:.2f}s")


def parse_req(path):
    if not os.path.isfile(path):
        print(f"File ko ton tai: {path}", file=sys.stderr)
        sys.exit(1)
        
    lines = open(path, "r", encoding="utf-8", errors="ignore").read().splitlines()
    if not lines:
        print("File rong", file=sys.stderr)
        sys.exit(1)
        
    parts = lines[0].split()
    method = parts[0]
    req_path = parts[1]
    
    hdrs = []
    body_idx = -1
    host = ""
    
    for i in range(1, len(lines)):
        line = lines[i].strip()
        if not line:
            body_idx = i + 1
            break
        if line.lower().startswith("host:"):
            host = line.split(":", 1)[1].strip()
        hdrs.append(line)
        
    body = "\n".join(lines[body_idx:]) if body_idx != -1 and body_idx < len(lines) else ""
    url = f"https://{host}{req_path}"
    return method, url, hdrs, body


def read_list(src):
    # ho tro parser range so
    if src.startswith("range:"):
        try:
            start, end = map(int, src.split(":")[1].split("-"))
            return [str(i) for i in range(start, end + 1)]
        except:
            print("Loi parse range", file=sys.stderr)
            sys.exit(1)
            
    if not os.path.isfile(src):
        print(f"Ko thay file: {src}", file=sys.stderr)
        sys.exit(1)
        
    return [line.strip() for line in open(src, "r", encoding="utf-8", errors="ignore") if line.strip()]


async def run(method, url, hdrs, data, w1, w2, is_cb, workers, t_limit):
    combined = url + "".join(hdrs) + data
    if "§§" not in combined and ("§1§" not in combined or "§2§" not in combined):
        print("Thieu placeholder", file=sys.stderr)
        sys.exit(1)

    # dung vong lap long nhau thay vi itertools de nhin tu nhien hon
    combos = []
    if is_cb:
        for p1 in w1:
            for p2 in w2:
                combos.append((p1, p2))
    else:
        for p1 in w1:
            combos.append((p1, ""))

    print(f"[*] Total: {len(combos)} requests | Workers: {workers}")
    print("-" * 60)

    sem = asyncio.Semaphore(workers)
    res = []
    
    limits = httpx.Limits(max_keepalive_connections=workers, max_connections=workers)
    async with httpx.AsyncClient(verify=False, limits=limits) as client:
        tasks = [
            send_req(client, method, url, hdrs, data, p1, p2, sem, res)
            for p1, p2 in combos
        ]
        await asyncio.gather(*tasks)

    print("-" * 60)
    print("[*] Scan completed.")

    # in ket qua thong ke o day
    if is_cb:
        print("\n[*] Summary:")
        try:
            sorted_res = sorted(res, key=lambda x: int(x["p1"]))
        except ValueError:
            sorted_res = sorted(res, key=lambda x: x["p1"])

        pw = {}
        for r in sorted_res:
            hit = (t_limit > 0 and r["time"] >= t_limit) or (t_limit == 0 and r["status"] == 500)
            if hit:
                print(f"Pos: {r['p1']:<4} | Char: {r['p2']:<4} | Status: {r['status']:<5} | Time: {r['time']:.2f}s")
                try:
                    pw[int(r["p1"])] = r["p2"]
                except:
                    pass

        # ghep pass cuoi cung
        if pw:
            max_pos = max(pw.keys())
            out = "".join(pw.get(i, "_") for i in range(1, max_pos + 1))
            print("-" * 60)
            print(f"[*] Password: {out}")
            print("-" * 60)


def main():
    parser = argparse.ArgumentParser(description="Py-Intruder")
    parser.add_argument("-u", "--url")
    parser.add_argument("-r", "--raw")
    parser.add_argument("-H", "--header", action="append", default=[])
    parser.add_argument("--sniper", action="store_true")
    parser.add_argument("--cb", action="store_true")
    parser.add_argument("-f", "--wordlist")
    parser.add_argument("-f2", "--wordlist2")
    parser.add_argument("-az", action="store_true")
    parser.add_argument("-09", dest="zero_nine", action="store_true")
    parser.add_argument("-c", "--workers", type=int, default=10)
    parser.add_argument("-t", "--time", type=float, default=0.0)

    args = parser.parse_args()
    
    url = args.url
    hdrs = args.header
    data = ""
    method = "GET"

    if args.raw:
        method, url, parsed_hdrs, data = parse_req(args.raw)
        hdrs = parsed_hdrs + hdrs

    if not url:
        print("Loi: Thieu URL hoac file request tho", file=sys.stderr)
        sys.exit(1)

    chars = ""
    if args.az:
        chars += "abcdefghijklmnopqrstuvwxyz"
    if args.zero_nine:
        chars += "0123456789"
    gens = list(chars) if chars else []

    combined = url + "".join(hdrs) + data
    is_cb = args.cb or (not args.sniper and "§1§" in combined and "§2§" in combined)

    w1 = []
    w2 = []

    if is_cb:
        if args.wordlist:
            w1 = read_list(args.wordlist)
        else:
            sys.exit("Error: Thieu wordlist 1")

        if args.wordlist2:
            w2 = read_list(args.wordlist2)
        elif gens:
            w2 = gens
        else:
            sys.exit("Error: Thieu wordlist 2")
    else:
        if args.wordlist:
            w1 = read_list(args.wordlist)
        elif gens:
            w1 = gens
        else:
            sys.exit("Error: Thieu wordlist")

    try:
        asyncio.run(run(method, url, hdrs, data, w1, w2, is_cb, args.workers, args.time))
    except KeyboardInterrupt:
        print("\n[!] User stop.")
        sys.exit(0)


if __name__ == "__main__":
    main()
