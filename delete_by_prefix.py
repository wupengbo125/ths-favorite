#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service import PortfolioManager

from datetime import date

def parse_mmdd(mmdd_str: str) -> date:
    if len(mmdd_str) != 4 or not mmdd_str.isdigit():
        return None
    today = date.today()
    try:
        month = int(mmdd_str[:2])
        day = int(mmdd_str[2:])
        d = date(today.year, month, day)
        # If the date is in the future by more than 30 days, assume it is from the previous year
        if (d - today).days > 30:
            d = date(today.year - 1, month, day)
        return d
    except ValueError:
        return None

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
        # Fetch raw groups directly to handle duplicate group names
        raw_data = manager._api.query_groups()
        parsed_groups = manager._parse_group_list(raw_data)
        
        threshold_date = parse_mmdd(args.prefix)
        deleted_count = 0
        for group_info in parsed_groups:
            name = group_info.get("name")
            group_id = group_info.get("id")
            if not name or not group_id:
                continue
                
            should_delete = False
            if threshold_date:
                if len(name) >= 4 and name[:4].isdigit():
                    group_date = parse_mmdd(name[:4])
                    if group_date and group_date <= threshold_date:
                        should_delete = True
            else:
                if name.startswith(args.prefix):
                    should_delete = True
                    
            if should_delete:
                print(f"Deleting group: {name} (ID: {group_id})")
                try:
                    manager.delete_group(group_id)
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete {name} ({group_id}): {e}")
        if threshold_date:
            print(f"Completed! Deleted {deleted_count} groups older than or equal to date '{args.prefix}'")
        else:
            print(f"Completed! Deleted {deleted_count} groups starting with '{args.prefix}'")

if __name__ == "__main__":
    main()
