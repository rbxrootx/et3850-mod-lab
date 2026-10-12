"""LAN companion for an already-modified ET-3850. It does not install firmware."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket

from mod_shell import connect


def probe(host: str) -> dict[str, str]:
    result = {}
    for name, port in (("ssh", 22), ("stock_telnet", 23), ("mod_shell", 2323)):
        try:
            with socket.create_connection((host, port), timeout=1.5):
                result[name] = "open"
        except OSError as error:
            result[name] = f"unavailable ({type(error).__name__})"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("probe", "status", "shell"):
        command = sub.add_parser(action)
        command.add_argument("host", help="printer IP address or hostname")
        if action != "probe":
            command.add_argument("--password-file", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "probe":
        print(json.dumps(probe(args.host), indent=2))
    elif args.action == "status":
        command = ("id; uname -a; "
                   "printf 'Wi-Fi power management: '; "
                   "cat /sys/module/8723du/parameters/rtw_power_mgnt; "
                   "printf 'Wi-Fi USB suspend: '; "
                   "cat /sys/module/8723du/parameters/rtw_enusbss")
        print(json.dumps(connect(args.host, args.password_file, command), indent=2))
    else:
        connect(args.host, args.password_file)


if __name__ == "__main__":
    main()
