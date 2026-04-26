# Multi-AS BGP Network Simulation with Traffic Engineering

A fully functional 3-AS BGP network simulated in GNS3, demonstrating ISP-grade routing concepts including Route Reflection, eBGP peering, and traffic engineering via LOCAL_PREF. Paired with a Python automation toolkit using Netmiko.

---

## Topology

```
         AS 100 (ISP Core)
        +----------------------+
        |  R1 - Route          |
        |  Reflector           |
        +----+------------+----+
             |    iBGP    |
        +----+----+  +----+----+
        |   R2    |  |   R3   |
        | ASBR-1  |  | ASBR-2 |
        +----+----+  +----+----+
             | eBGP       | eBGP
        +----+----+  +----+--------+
        |  AS 200 |  |   AS 300   |
        |   R4    |  |    R5      |
        | Customer|  |  Peer ISP  |
        +---------+  +------------+
```

| AS  | Role       | Routers                        |
|-----|------------|-------------------------------|
| 100 | ISP Core   | R1 (Route Reflector), R2, R3  |
| 200 | Customer   | R4                            |
| 300 | Peer ISP   | R5                            |

---

## IP Addressing

| Link         | Subnet          | Left End     | Right End    |
|--------------|-----------------|--------------|--------------|
| R1–R2 (iBGP) | 10.1.12.0/30    | 10.1.12.1    | 10.1.12.2    |
| R1–R3 (iBGP) | 10.1.13.0/30    | 10.1.13.1    | 10.1.13.2    |
| R2–R4 (eBGP) | 172.16.24.0/30  | 172.16.24.1  | 172.16.24.2  |
| R3–R5 (eBGP) | 172.16.35.0/30  | 172.16.35.1  | 172.16.35.2  |

---

## Features Demonstrated

- **iBGP Route Reflector** — R1 reflects routes between R2 and R3, eliminating full-mesh requirement
- **OSPF IGP** — loopback reachability inside AS100 for iBGP sessions
- **eBGP peering** — AS100 peers with customer (AS200) and peer ISP (AS300)
- **Traffic Engineering via LOCAL_PREF** — customer routes preferred (150) over peer routes (100)
- **Prefix filtering** — inbound/outbound prefix-lists on all eBGP sessions prevent route leaking
- **Route-maps** — policy applied per neighbor for fine-grained control

---

## Lab Environment

- **GNS3** 2.2.58.1 on Windows + GNS3 VM in VirtualBox
- **FRRouting (FRR)** 8.2.2 as router OS
- **Python** 3.x + Netmiko for automation

---

## Project Structure

```
├── bgp-multias-lab/
│   ├── configs/
│   │   ├── R1-AS100-RR.cfg
│   │   ├── R2-AS100-ASBR1.cfg
│   │   ├── R3-AS100-ASBR2.cfg
│   │   ├── R4-AS200-Customer.cfg
│   │   └── R5-AS300-PeerISP.cfg
│   └── README.md
├── netmiko-automation/
│   ├── configs/
│   │   └── inventory.yaml
│   ├── scripts/
│   │   ├── bgp_audit.py       # Concurrent BGP health check
│   │   ├── push_config.py     # Config deployment with dry-run
│   │   └── collect_routes.py  # Route snapshots + diff
│   └── README.md
├── BGP-MultiAS.gns3           # GNS3 project file
└── BGP_Project_Notes.pdf      # Project notes
```

---

## Python Automation

Install dependencies:
```bash
pip install -r netmiko-automation/requirements.txt
```

Check BGP health across all routers:
```bash
python netmiko-automation/scripts/bgp_audit.py
```

Push a config change to all ASBRs (dry-run first):
```bash
python netmiko-automation/scripts/push_config.py --group asbr --commands cmds.txt --dry-run
python netmiko-automation/scripts/push_config.py --group asbr --commands cmds.txt
```

Snapshot BGP routes and diff after a topology change:
```bash
python netmiko-automation/scripts/collect_routes.py
python netmiko-automation/scripts/collect_routes.py --diff
```

---

## Verification

Confirmed working output from R1 after full topology came up:

```
R1-AS100-RR# show bgp summary
Neighbor   AS    Up/Down    PfxRcd
10.0.0.2   100   00:03:49   1       ← R2 Established
10.0.0.3   100   00:02:18   0       ← R3 Established

R1-AS100-RR# show ip bgp
Network            Next Hop       LocPrf  Path
10.0.0.0/16        0.0.0.0                32768 i
192.168.200.0/24   172.16.24.2    150     0 200 i
```
