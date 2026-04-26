"""
Config Push Tool
Pushes a set of IOS commands to one or more devices (filtered by name or group).
Supports dry-run mode to preview without connecting.

Usage:
  python push_config.py --device R1-AS100-RR --commands commands.txt
  python push_config.py --group asbr --commands commands.txt --dry-run
"""

import argparse
import yaml
import sys
from pathlib import Path
from datetime import datetime

from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException
from rich.console import Console
from rich.panel import Panel

INVENTORY_PATH = Path(__file__).parent.parent / "configs" / "inventory.yaml"
console = Console()


def load_inventory(path: Path) -> list[dict]:
    with open(path) as f:
        return yaml.safe_load(f)["devices"]


def filter_devices(devices: list[dict], name: str | None, group: str | None) -> list[dict]:
    if name:
        return [d for d in devices if d["name"] == name]
    if group:
        return [d for d in devices if group in d.get("groups", [])]
    return devices


def push_to_device(device: dict, commands: list[str], dry_run: bool) -> dict:
    result = {"name": device["name"], "host": device["host"], "output": "", "error": None}
    if dry_run:
        result["output"] = f"[DRY RUN] Would push {len(commands)} command(s)"
        return result
    conn_params = {
        "device_type": device["device_type"],
        "host": device["host"],
        "username": device["username"],
        "password": device["password"],
        "secret": device.get("secret", ""),
        "timeout": 10,
    }
    try:
        with ConnectHandler(**conn_params) as net_connect:
            net_connect.enable()
            output = net_connect.send_config_set(commands)
            net_connect.save_config()
            result["output"] = output
    except NetMikoTimeoutException:
        result["error"] = "Timeout"
    except NetMikoAuthenticationException:
        result["error"] = "Auth failed"
    except Exception as e:
        result["error"] = str(e)
    return result


def main():
    parser = argparse.ArgumentParser(description="Push IOS config commands to devices")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--device", help="Target a single device by name")
    target.add_argument("--group", help="Target all devices in a group")
    target.add_argument("--all", action="store_true", help="Target all devices")
    parser.add_argument("--commands", required=True, help="File with one IOS command per line")
    parser.add_argument("--dry-run", action="store_true", help="Preview without connecting")
    args = parser.parse_args()

    commands_path = Path(args.commands)
    if not commands_path.exists():
        console.print(f"[red]Commands file not found: {commands_path}[/]")
        sys.exit(1)

    commands = [line.strip() for line in commands_path.read_text().splitlines() if line.strip()]
    if not commands:
        console.print("[red]No commands found in file.[/]")
        sys.exit(1)

    all_devices = load_inventory(INVENTORY_PATH)
    targets = filter_devices(all_devices, args.device, args.group if not args.all else None)

    if not targets:
        console.print("[red]No matching devices found.[/]")
        sys.exit(1)

    mode = "[yellow]DRY RUN[/]" if args.dry_run else "[green]LIVE[/]"
    console.print(f"\n{mode} — pushing to {len(targets)} device(s)\n")
    console.print(Panel("\n".join(commands), title="Commands", expand=False))

    for device in targets:
        result = push_to_device(device, commands, args.dry_run)
        if result["error"]:
            console.print(f"[red][{result['name']}] ERROR: {result['error']}[/]")
        else:
            console.print(Panel(result["output"], title=f"[green]{result['name']}[/]", expand=False))

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"\nCompleted at {timestamp}")


if __name__ == "__main__":
    main()
