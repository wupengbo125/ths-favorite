#!/usr/bin/env python3

import argparse
import csv
import os
import sys
import concurrent.futures
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from service import PortfolioManager

logger.remove()

add_lock = threading.Lock()

# CSV 中允许出现的股票代码列名；同时出现多列视为歧义,直接报错
CSV_CODE_COLUMNS = ("ts_code", "stock_code")


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


def _read_codes_from_csv(file_path: str) -> list:
    """读取 CSV 中 ts_code 或 stock_code 列;两列同时存在或都缺失则报错,空文件返回空列表。"""
    with open(file_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        # 0 字节文件或没有表头,视为空文件,不报错也不上传
        if reader.fieldnames is None:
            return []

        present = [c for c in CSV_CODE_COLUMNS if c in reader.fieldnames]
        if len(present) == 0:
            raise ValueError(
                f"CSV 缺少股票代码列:需要 {' 或 '.join(CSV_CODE_COLUMNS)},"
                f"实际列为: {list(reader.fieldnames)}"
            )
        if len(present) > 1:
            raise ValueError(
                f"CSV 同时存在 {present} 列,无法判断以哪列为准,请只保留一列"
            )

        code_col = present[0]
        codes = []
        for row in reader:
            value = (row.get(code_col) or "").strip()
            if value:
                codes.append(value)
        return codes


def _read_codes_from_txt(file_path: str) -> list:
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def read_codes(file_path: str) -> list:
    """按扩展名分发:.csv 走列解析,其它按一行一个代码读取。"""
    if file_path.lower().endswith(".csv"):
        return _read_codes_from_csv(file_path)
    return _read_codes_from_txt(file_path)


def _derive_group_name(file_path: str) -> str:
    base = os.path.basename(file_path)
    for ext in (".csv", ".txt"):
        if base.lower().endswith(ext):
            return base[: -len(ext)]
    return base


def main():
    parser = argparse.ArgumentParser(description="批量添加股票到分组 (支持 .csv / .txt)")
    parser.add_argument(
        "input_file",
        help="股票代码文件路径 (.csv 需含 ts_code 或 stock_code 列;.txt 一行一个代码)",
    )
    parser.add_argument("--workers", type=int, default=10, help="并发数 (默认10)")
    parser.add_argument("--username", help="登录账号")
    parser.add_argument("--password", help="登录密码")
    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        print(f"错误: 文件不存在: {args.input_file}")
        sys.exit(1)

    group_name = _derive_group_name(args.input_file)

    codes = read_codes(args.input_file)

    if not codes:
        print(f"=== 文件为空,跳过上传: {args.input_file} ===")
        return

    # 默认倒序处理,实现先进先出(后加入的在同花顺自选股最上面,所以倒序插入才能维持文本原有顺序)
    codes.reverse()

    print(f"=== 开始处理: {group_name} ===")
    print(f"共 {len(codes)} 只股票,并发数: {args.workers}")

    manager = PortfolioManager(username=args.username, password=args.password)

    print("创建分组...")
    try:
        existing_groups = manager.get_all_groups(use_cache=False)
        if group_name in existing_groups:
            print(f"分组已存在: {group_name}，跳过创建。")
        else:
            manager.add_group(group_name)
            print(f"已创建分组: {group_name}")
    except Exception as e:
        print(f"创建分组失败: {e}")

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