#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取 XYZ 格式地图瓦片，构建本地瓦片库（供 Apache 地图服务器使用）。

用法示例：
    python3 scripts/fetch_tiles.py --center 28.228,112.937 --min-zoom 10 --max-zoom 14

说明：
    - 瓦片按 tiles/{z}/{x}/{y}.png 组织，与 Apache Alias /tiles 目录对应；
    - 下载后按文件大小过滤坏瓦片，并生成 tiles.json 清单；
    - 仅用于学习演示，请遵守目标瓦片服务的使用政策。
"""
import argparse
import json
import math
import os
import sys
import time
import urllib.request

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = "map-tile-server-demo/1.0 (learning project)"
RETRY = 3
INTERVAL = 0.3  # 两次请求间隔（秒），避免给瓦片服务造成压力
MIN_GOOD_SIZE = 1024  # 正常 PNG 瓦片通常大于 1KB


def deg2num(lat, lon, z):
    """经纬度 -> XYZ 瓦片行列号（Web Mercator 反算）。"""
    n = 2 ** z
    xtile = (lon + 180.0) / 360.0 * n
    ytile = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return int(xtile), int(ytile)


def fetch_tile(z, x, y, out_dir):
    """下载单个瓦片，失败重试。"""
    url = TILE_URL.format(z=z, x=x, y=y)
    dest = os.path.join(out_dir, str(z), str(x), f"{y}.png")
    if os.path.exists(dest) and os.path.getsize(dest) > MIN_GOOD_SIZE:
        return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, RETRY + 1):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            if len(data) >= MIN_GOOD_SIZE:
                with open(dest, "wb") as f:
                    f.write(data)
                return True
            print(f"  [skip] 疑似坏瓦片 z{z}/{x}/{y} ({len(data)}B)")
            return False
        except Exception as exc:  # noqa: BLE001
            if attempt < RETRY:
                time.sleep(INTERVAL * attempt)
            else:
                print(f"  [fail] z{z}/{x}/{y}: {exc}")
    return False


def main():
    ap = argparse.ArgumentParser(description="XYZ 瓦片抓取工具")
    ap.add_argument("--center", required=True,
                    help="中心点经纬度，格式 lat,lon，如 28.228,112.937")
    ap.add_argument("--min-zoom", type=int, default=10)
    ap.add_argument("--max-zoom", type=int, default=14)
    ap.add_argument("--span", type=float, default=0.02,
                    help="抓取范围（度），越大瓦片越多")
    ap.add_argument("--out", default="tiles", help="输出目录，默认 tiles/")
    args = ap.parse_args()

    lat, lon = map(float, args.center.split(","))
    if not (args.min_zoom <= args.max_zoom):
        ap.error("--min-zoom 必须小于等于 --max-zoom")

    manifest = []
    total = 0
    for z in range(args.min_zoom, args.max_zoom + 1):
        x0, y0 = deg2num(lat + args.span, lon - args.span, z)
        x1, y1 = deg2num(lat - args.span, lon + args.span, z)
        xs = range(min(x0, x1), max(x0, x1) + 1)
        ys = range(min(y0, y1), max(y0, y1) + 1)
        count = len(xs) * len(ys)
        total += count
        print(f"[z{z}] 计划抓取 {count} 张瓦片 ...")
        for x in xs:
            for y in ys:
                if fetch_tile(z, x, y, args.out):
                    manifest.append({"z": z, "x": x, "y": y})
                time.sleep(INTERVAL)

    with open(os.path.join(args.out, "tiles.json"), "w", encoding="utf-8") as f:
        json.dump({"source": "demo", "count": len(manifest), "tiles": manifest}, f,
                  ensure_ascii=False)

    print(f"\n完成：共抓取 {len(manifest)} 张有效瓦片（计划 {total} 张）")
    print(f"瓦片目录：{os.path.abspath(args.out)}")
    if len(manifest) < total:
        print("提示：部分瓦片下载失败，可稍后重跑本脚本补齐（已存在瓦片会跳过）。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
