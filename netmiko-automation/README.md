# Network Automation Toolkit (Netmiko)

Python automation scripts targeting the BGP Multi-AS GNS3 lab.

## Scripts

| Script | Purpose |
|--------|---------|
| `bgp_audit.py` | Poll all devices, report any BGP session not in Established state |
| `push_config.py` | Push IOS config commands to one device, a group, or all devices |
| `collect_routes.py` | Snapshot BGP route tables; diff two snapshots to detect changes |

## Setup

```bash
pip install -r requirements.txt
```

Edit `configs/inventory.yaml` to match your GNS3 management IPs.

## Usage Examples

```bash
# Check all BGP neighbors across the lab
python scripts/bgp_audit.py

# Push a prefix-list update to all ASBRs (dry-run first)
python scripts/push_config.py --group asbr --commands my_commands.txt --dry-run
python scripts/push_config.py --group asbr --commands my_commands.txt

# Collect a route snapshot, then diff after a topology change
python scripts/collect_routes.py
# ... simulate a link failure in GNS3 ...
python scripts/collect_routes.py
python scripts/collect_routes.py --diff
```

## Connecting GNS3 Routers

1. In GNS3, add a **Cloud** node and connect it to your host NIC (or use a loopback adapter).
2. Add a management interface to each router and assign IPs matching `inventory.yaml`.
3. Enable SSH on each router:
   ```
   ip domain-name lab.local
   crypto key generate rsa modulus 2048
   ip ssh version 2
   line vty 0 4
    transport input ssh
    login local
   username admin privilege 15 secret cisco
   ```
