#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service import PortfolioManager

def main():
    parser = argparse.ArgumentParser(description="Delete THS groups by prefix")
    parser.add_argument("prefix", help="Group name prefix to delete")
    parser.add_argument("--username", help="Login username")
    parser.add_argument("--password", help="Login password")
    parser.add_argument("--cookie-cache", help="Custom cookie cache path")
    args = parser.parse_args()

    if not args.prefix:
        print("Error: prefix is required")
        sys.exit(1)

    manager_kwargs = {}
    if args.username:
        manager_kwargs["username"] = args.username
    if args.password:
        manager_kwargs["password"] = args.password
    if args.cookie_cache:
        manager_kwargs["cookie_cache_path"] = args.cookie_cache

    with PortfolioManager(**manager_kwargs) as manager:
        groups = manager.get_all_groups(include_self_stocks=False)
        deleted_count = 0
        for name in groups.keys():
            if name.startswith(args.prefix):
                print(f"Deleting group: {name}")
                try:
                    manager.delete_group(name)
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete {name}: {e}")
        print(f"Completed! Deleted {deleted_count} groups starting with '{args.prefix}'")

if __name__ == "__main__":
    main()
