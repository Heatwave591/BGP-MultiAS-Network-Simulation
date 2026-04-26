"""
Route Table Collector
Collects 'show ip route bgp' from all devices and saves timestamped snapshots.
Useful for verifying BGP convergence and detecting routing changes over time.

Usage:
  python collect_routes.py
  python collect_routes.py --diff   # compare latest two snapshots
"""

import argparse
import yaml
import json
import re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException
from rich.console import Console
from rich.table import Table
from rich import box

INVENTORY_PATH = Path(__file__).parent.parent / "configs" / "inventory.yaml"
SNAPSHOTS_DIR = Path(__file__).parent.parent / "snapshots"
console = Console()


def load_inventory(path: Path) -> list[dict]:
    with open(path) as f:
        return yaml.safe_load(f)["devices"]


def parse_bgp_routes(output: str) -> list[str]:
    """Extract prefixes from 'show ip route bgp' output."""
    return re.findall(r"B\s+(\d+\.\d+\.\d+\.\d+/\d+)", output)


def collect_from_device(device: dict) -> dict:
    result = {"name": device["name"], "routes": [], "raw": "", "error": None}
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
            raw = net_connect.send_command("show ip route bgp", read_timeout=15)
            result["raw"] = raw
            result["routes"] = parse_bgp_routes(raw)
    except NetMikoTimeoutException:
        result["error"] = "Timeout"
    except NetMikoAuthenticationException:
        result["error"] = "Auth failed"
    except Exception as e:
        result["error"] = str(e)
    return result


def save_snapshot(data: dict, timestamp: str):
    SNAPSHOTS_DIR.mkdir(exist_ok=True)
    snapshot_file = SNAPSHOTS_DIR / f"routes_{timestamp}.json"
    with open(snapshot_file, "w") as f:
        json.dump(data, f, indent=2)
    console.print(f"Snapshot saved: [cyan]{snapshot_file}[/]")
    return snapshot_file


def diff_snapshots():
    snapshots = sorted(SNAPSHOTS_DIR.glob("routes_*.json"))
    if len(snapshots) < 2:
        console.print("[yellow]Need at least 2 snapshots to diff.[/]")
        return
    old_path, new_path = snapshots[-2], snapshots[-1]
    console.print(f"\nDiff: [dim]{old_path.name}[/] → [cyan]{new_path.name}[/]\n")
    with open(old_path) as f:
        old = json.load(f)
    with open(new_path) as f:
        new = json.load(f)
    for device in set(list(old.keys()) + list(new.keys())):
        old_routes = set(old.get(device, {}).get("routes", []))
        new_routes = set(new.get(device, {}).get("routes", []))
        added = new_routes - old_routes
        removed = old_routes - new_routes
        if added or removed:
            console.print(f"[bold]{device}[/]")
            for r in sorted(added):
                console.print(f"  [green]+ {r}[/]")
            for r in sorted(removed):
                console.print(f"  [red]- {r}[/]")
    console.print("")


def main():
    parser = argparse.ArgumentParser(description="Collect BGP routes from all devices")
    parser.add_argument("--diff", action="store_true", help="Diff latest two snapshots instead of collecting")
    args = parser.parse_args()

    if args.diff:
        diff_snapshots()
        return

    devices = load_inventory(INVENTORY_PATH)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    console.print(f"\n[bold cyan]Route Collection[/] — {timestamp}\n")

    all_results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(collect_from_device, d): d["name"] for d in devices}
        for future in as_completed(futures):
            r = future.result()
            all_results[r["name"]] = r

    table = Table(title="BGP Routes per Device", box=box.ROUNDED)
    table.add_column("Router", style="bold")
    table.add_column("BGP Prefixes")
    table.add_column("Count")

    for name in sorted(all_results):
        r = all_results[name]
        if r["error"]:
            table.add_row(name, f"[red]ERROR: {r['error']}[/]", "-")
        else:
            table.add_row(name, ", ".join(r["routes"]) or "[dim]none[/]", str(len(r["routes"])))

    console.print(table)
    save_snapshot(all_results, timestamp)


if __name__ == "__main__":
    main()
