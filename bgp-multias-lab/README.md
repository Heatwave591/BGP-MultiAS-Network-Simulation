# BGP Multi-AS Simulation Lab (GNS3)

## Topology Overview

```
         AS 100 (ISP Core)
        ┌──────────────────┐
        │  R1 (RR)         │
        │  10.0.0.1        │
        │  iBGP Route      │
        │  Reflector       │
        └────┬────────┬────┘
             │        │
        iBGP │        │iBGP
             │        │
        ┌────▼──┐  ┌──▼────┐
        │  R2   │  │  R3   │
        │ASBR-1 │  │ASBR-2 │
        └────┬──┘  └──┬────┘
             │        │
       eBGP  │        │eBGP
             │        │
     ┌───────▼─┐  ┌───▼───────┐
     │ AS 200  │  │  AS 300   │
     │ R4      │  │  R5       │
     │ Customer│  │ Peer ISP  │
     └─────────┘  └───────────┘
```

## AS Design

| AS    | Role         | Routers | Loopbacks       |
|-------|--------------|---------|-----------------|
| 100   | ISP Core     | R1,R2,R3| 10.0.0.x/32     |
| 200   | Customer     | R4      | 192.168.200.1/24|
| 300   | Peer ISP     | R5      | 192.168.300.1/24|

## IP Addressing Plan

| Link         | Network         | R1 end       | R2/R3/R4/R5 end |
|--------------|-----------------|--------------|-----------------|
| R1-R2 (iBGP) | 10.1.12.0/30    | 10.1.12.1    | 10.1.12.2       |
| R1-R3 (iBGP) | 10.1.13.0/30    | 10.1.13.1    | 10.1.13.2       |
| R2-R4 (eBGP) | 172.16.24.0/30  | 172.16.24.1  | 172.16.24.2     |
| R3-R5 (eBGP) | 172.16.35.0/30  | 172.16.35.1  | 172.16.35.2     |

## GNS3 Setup Requirements

- **Image**: Cisco IOSv or IOS-XE (CSR1000v) — 15.x+ for full BGP feature support
- **RAM per router**: 512MB minimum (1GB recommended for CSR1000v)
- **GNS3 version**: 2.2+

## Lab Objectives

1. Configure iBGP with Route Reflector (R1) inside AS 100
2. Establish eBGP sessions between AS 100 and AS 200/300
3. Advertise and filter prefixes using prefix-lists and route-maps
4. Implement BGP communities for traffic engineering
5. Demonstrate BGP path selection (AS-path, LOCAL_PREF, MED)
6. Simulate a link failure and observe BGP reconvergence

## Router Configurations

See `configs/` directory for full IOS configs.

## Key Concepts Demonstrated

- iBGP full-mesh avoidance via Route Reflector
- eBGP multihop (optional)
- BGP prefix filtering (inbound/outbound)
- LOCAL_PREF for outbound path preference
- MED for inbound traffic influence
- BGP communities (well-known + private)
