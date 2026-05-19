#!/usr/bin/env python3

import argparse
import os
import sys
import concurrent.futures
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from service import PortfolioManager

logger.remove()

add_lock = threading.Lock()


def get_suffix(code: str) -> str:
    first_char = code[0]
    if first_char == "6":
        return ".SH"
    elif first_char == "0":
        return ".SZ"
    elif first_char == "8" or first_char == "4":
        return ".BJ"
    else:
        return ".SZ"


def add_stock(manager: PortfolioManager, group_name: str, code: str) -> str:
    code = code.strip()
    if not code:
        return "skip"

    code = code.replace(".SH", "").replace(".SZ", "").replace(".BJ", "")
    suffix = get_suffix(code)
    symbol = f"{code}{suffix}"

    try:
        with add_lock:
            manager.add_item_to_group(group_name, symbol)
        return f"ok: {symbol}"
    except Exception as e:
        return f"fail: {symbol} - {e}"


def main():
    parser = argparse.ArgumentParser(description="批量添加股票到分组")
    parser.add_argument("txt_file", help="股票代码文件路径")
    parser.add_argument("--workers", type=int, default=10, help="并发数 (默认10)")
    parser.add_argument("--username", help="登录账号")
    parser.add_argument("--password", help="登录密码")
    args = parser.parse_args()

    if not os.path.isfile(args.txt_file):
        print(f"错误: 文件不存在: {args.txt_file}")
        sys.exit(1)

    group_name = os.path.basename(args.txt_file).replace(".txt", "")

    with open(args.txt_file, "r") as f:
        codes = [line.strip() for line in f if line.strip()]

    # 默认倒序处理，实现先进先出（后加入的在同花顺自选股最上面，所以倒序插入才能维持文本原有顺序）
    codes.reverse()

    print(f"=== 开始处理: {group_name} ===")
    print(f"共 {len(codes)} 只股票，并发数: {args.workers}")

    manager = PortfolioManager(username=args.username, password=args.password)

    print("创建分组...")
    try:
        manager.add_group(group_name)
        print(f"已创建分组: {group_name}")
    except Exception as e:
        print(f"分组可能已存在: {e}")

    print("添加股票到分组...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(add_stock, manager, group_name, code): code
            for code in codes
        }

        failed = []

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result.startswith("ok:"):
                print(f"[+] {result[4:]}")
            elif result == "skip":
                pass
            else:
                failed.append(result)
                print(f"[-] {result[6:]}")

        if failed:
            print()
            print(f"共 {len(failed)} 个失败")

    print(f"=== 完成: {len(codes) - len(failed)} 成功, {len(failed)} 失败 ===")


if __name__ == "__main__":
    main()