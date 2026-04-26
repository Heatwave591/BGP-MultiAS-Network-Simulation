"""
BGP Neighbor Audit Tool
Connects to all devices in inventory, collects BGP neighbor state,
and reports any sessions not in Established state.
"""

import yaml
import sys
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException
from rich.console import Console
from rich.table import Table
from rich import box

INVENTORY_PATH = Path(__file__).parent.parent / "configs" / "inventory.yaml"
console = Console()


def load_inventory(path: Path) -> list[dict]:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data["devices"]


def parse_bgp_summary(output: str) -> list[dict]:
    """Parse 'show bgp summary' output into a list of neighbor dicts."""
    neighbors = []
    # Match lines like: 10.0.0.2  4  100  ...  Established
    pattern = re.compile(
        r"^(\d+\.\d+\.\d+\.\d+)\s+(\d+)\s+(\d+)\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(\S+)",
        re.MULTILINE,
    )
    for match in pattern.finditer(output):
        neighbors.append(
            {
                "neighbor": match.group(1),
                "as": match.group(3),
                "state": match.group(4),
            }
        )
    return neighbors


def audit_device(device: dict) -> dict:
    conn_params = {
        "device_type": device["device_type"],
        "host": device["host"],
        "username": device["username"],
        "password": device["password"],
        "secret": device.get("secret", ""),
        "timeout": 10,
    }
    result = {"name": device["name"], "host": device["host"], "neighbors": [], "error": None}
    try:
        with ConnectHandler(**conn_params) as net_connect:
            net_connect.enable()
            output = net_connect.send_command("show bgp summary", read_timeout=15)
            result["neighbors"] = parse_bgp_summary(output)
    except NetMikoTimeoutException:
        result["error"] = "Timeout"
    except NetMikoAuthenticationException:
        result["error"] = "Auth failed"
    except Exception as e:
        result["error"] = str(e)
    return result


def main():
    devices = load_inventory(INVENTORY_PATH)
    console.print(f"\n[bold cyan]BGP Audit[/] — {len(devices)} devices\n")

    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(audit_device, d): d["name"] for d in devices}
        for future in as_completed(futures):
            results.append(future.result())

    table = Table(title="BGP Neighbor State", box=box.ROUNDED)
    table.add_column("Router", style="bold")
    table.add_column("Neighbor")
    table.add_column("Peer AS")
    table.add_column("State")
    table.add_column("Status")

    issues = 0
    for r in sorted(results, key=lambda x: x["name"]):
        if r["error"]:
            table.add_row(r["name"], "-", "-", "-", f"[red]ERROR: {r['error']}[/]")
            issues += 1
            continue
        if not r["neighbors"]:
            table.add_row(r["name"], "-", "-", "-", "[yellow]No BGP neighbors[/]")
            continue
        for n in r["neighbors"]:
            state = n["state"]
            status = "[green]OK[/]" if state == "Established" else "[red]DOWN[/]"
            if state != "Established":
                issues += 1
            table.add_row(r["name"], n["neighbor"], n["as"], state, status)

    console.print(table)
    if issues:
        console.print(f"\n[bold red]{issues} issue(s) detected.[/]")
        sys.exit(1)
    else:
        console.print("\n[bold green]All BGP sessions Established.[/]")


if __name__ == "__main__":
    main()
