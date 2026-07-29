# Module: Reconnaissance and Discovery

## Overview

The reconnaissance module provides network mapping capabilities using Nmap
and ARP-layer tools. Its purpose is to identify active hosts, open ports,
running services, and operating system characteristics on the target network
before deeper testing begins.

All operations in this module are read-only from the perspective of the
target. No exploit payloads are sent.

---

## Scan Profiles

### Ping Sweep

**Description:**
Sends ICMP echo requests to all addresses in the target range. Hosts that
respond are considered active. Hosts behind firewalls that drop ICMP may not
appear. No ports are probed; this is the lowest-impact discovery method.

**Command constructed:**
```
nmap -sn <target>/24
```

**Flags explained:**
- `-sn`: Disable port scanning. Perform host discovery only.

**Expected output:**
```
Nmap scan report for 192.168.1.1
Host is up (0.0012s latency).
```

**Limitations:**
Hosts that block ICMP will not appear. Use ARP Scan for more complete
discovery on local network segments.

---

### ARP Scan

**Description:**
Sends ARP requests across the local subnet. ARP operates at the data link
layer and cannot be filtered by host-level firewalls, making this the most
reliable local discovery method. Requires root and the arp-scan tool.

**Command constructed:**
```
arp-scan --localnet
```

**Expected output:**
```
192.168.1.1   aa:bb:cc:dd:ee:ff   TP-LINK TECHNOLOGIES
```

**Limitations:**
Works only on the local network segment. Cannot discover hosts behind routers.

---

### Fast Port Scan

**Description:**
Scans the 100 most commonly used TCP ports using TCP SYN. Returns results
quickly by limiting port range and using aggressive timing.

**Command constructed:**
```
nmap -F -T4 --open <target>
```

**Flags:**
- `-F`: Top 100 ports only.
- `-T4`: Aggressive timing.
- `--open`: Show only open ports.

---

### Full Port Scan

**Description:**
Scans all 65535 TCP ports using TCP SYN. The most thorough enumeration
available, but the slowest. Allow significant time for completion.

**Command constructed:**
```
nmap -sS -p- -T3 --open <target>
```

**Flags:**
- `-sS`: TCP SYN scan. Requires root.
- `-p-`: All 65535 ports.
- `-T3`: Normal timing.

---

### OS and Service Detection

**Description:**
Combines TCP SYN scanning with service version detection and operating
system fingerprinting. Produces the most complete picture of a target's
attack surface. Requires root.

**Command constructed:**
```
nmap -A -T4 -sV --osscan-guess <target>
```

**Flags:**
- `-A`: Enable OS detection, version detection, script scanning, traceroute.
- `-sV`: Service version detection.
- `--osscan-guess`: Attempt OS detection even when confidence is low.

---

### Stealth Scan

**Description:**
TCP SYN scan using fragmented packets, decoy addresses, and reduced timing
to minimize detection likelihood. Modern IDS/IPS solutions may still detect
this scan. The label refers to reduced network signature, not guaranteed
invisibility.

**Command constructed:**
```
nmap -sS -T2 -f --data-length 200 -D RND:5 <target>
```

**Flags:**
- `-T2`: Polite timing. Longer probe delays.
- `-f`: Fragment IP packets.
- `--data-length 200`: Append random data to alter packet signature.
- `-D RND:5`: Five random decoy addresses.

---

### NSE Script Scan

**Description:**
Runs Nmap's default script set plus service version detection. The default
category includes safe enumeration, banner grabbing, and misconfiguration
identification. Does not run exploit or brute force scripts.

**Command constructed:**
```
nmap -sC -sV <target>
```

**Flags:**
- `-sC`: Default script category.
- `-sV`: Service version detection.

---

### UDP Scan

**Description:**
Scans the 200 most common UDP ports. UDP scanning is inherently slower and
less reliable than TCP scanning because UDP is connectionless and many hosts
rate-limit ICMP port-unreachable responses.

**Command constructed:**
```
nmap -sU --top-ports 200 -T3 <target>
```

**Flags:**
- `-sU`: UDP scan.
- `--top-ports 200`: Most common UDP ports.

---

### Custom Scan

**Description:**
Direct entry of Nmap flags. The target address is appended automatically.
Use when predefined profiles do not cover the required scan type.

**Command constructed:**
```
nmap <user-supplied flags> <target>
```

Nmap reference: https://nmap.org/book/man.html

---

## Output Files

Each scan writes output to the session report directory in Nmap normal
format (-oN). The file is named using the profile and target address:

```
reports/<session>/nmap_<profile>_<target>.txt
```

---

## Required Tools

| Tool | Package | Purpose |
|---|---|---|
| nmap | nmap | All profiles except ARP Scan |
| arp-scan | arp-scan | ARP Scan profile |
