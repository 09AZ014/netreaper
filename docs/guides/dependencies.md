# Dependency Reference

This document lists every external tool that NetReaper uses, the Linux package
that provides it, the module that requires it, and installation notes.

## System Tools

| Tool | Package (apt) | Module | Notes |
|---|---|---|---|
| nmap | nmap | Recon, Vuln | Requires root for SYN and OS detection |
| john | john | Crack | John the Ripper password cracker |
| hashcat | hashcat | Crack | Requires GPU/CPU OpenCL drivers for performance |
| hydra | hydra | Crack | Online brute force |
| tshark | tshark | Traffic | CLI Wireshark dissector |
| tcpdump | tcpdump | Traffic | Requires root or CAP_NET_RAW |
| aircrack-ng | aircrack-ng | Wireless | Full suite: airmon-ng, airodump-ng, aireplay-ng |
| wifite | wifite | Wireless | Automated WPA/WPS attack wrapper |
| nikto | nikto | Web | Web server scanner |
| gobuster | gobuster | Web | Directory and DNS brute force |
| sqlmap | sqlmap | Web | SQL injection scanner |
| searchsploit | exploitdb | Vuln | Requires exploitdb database update: searchsploit -u |
| masscan | masscan | Recon | Requires root; extremely fast |
| arp-scan | arp-scan | Recon | Requires root |
| netdiscover | netdiscover | Recon | Requires root |
| sslscan | sslscan | Vuln | SSL/TLS configuration auditing |
| enum4linux | enum4linux | Vuln | SMB and Samba enumeration |
| hping3 | hping3 | Advanced | Packet crafting; requires root |
| nc | netcat-openbsd | Utility | Netcat (OpenBSD variant) |
| ffuf | ffuf | Web | Web fuzzer |
| wfuzz | wfuzz | Web | Web fuzzer |
| dirb | dirb | Web | Web content scanner |
| lynis | lynis | Vuln | Local system auditor |
| fail2ban-client | fail2ban | Defense | Intrusion prevention status |
| bettercap | bettercap | Wireless | Network attacker and MITM framework |
| ettercap | ettercap-common | Traffic | MITM and traffic manipulation |
| hashid | hashid | Crack | Hash type identification |
| msfconsole | metasploit-framework | Vuln | Exploit framework; large install |

## Python Dependencies

| Package | Version | Purpose |
|---|---|---|
| rich | >=13.0.0 | Terminal formatting, tables, progress bars, panels |
| questionary | >=2.0.0 | Interactive selection menus |
| InquirerPy | >=0.3.4 | Extended interactive prompts |
| fpdf2 | >=2.7.0 | PDF report generation |
| colorama | >=0.4.6 | Cross-platform ANSI color support |
| tabulate | >=0.9.0 | Plain-text table formatting |
| requests | >=2.31.0 | HTTP client |
| paramiko | >=3.0.0 | SSH client |

## Notes on Specific Tools

**tshark and group membership**
On Debian/Ubuntu, tshark allows capture only by members of the wireshark group:
```
sudo usermod -aG wireshark $USER
```
Alternatively, run NetReaper as root.

**hashcat and OpenCL**
Hashcat uses GPU acceleration via OpenCL or CUDA. On systems without a
supported GPU, hashcat falls back to CPU mode (significantly slower).
Install OpenCL drivers appropriate for your hardware.

**metasploit-framework**
Metasploit is a large package requiring database initialization on first run.
The NetReaper installer skips Metasploit if installation takes too long.
Install manually:
```
sudo apt-get install metasploit-framework
sudo msfdb init
```

**wifite**
Wifite requires a wireless adapter supporting monitor mode and packet
injection. Verify with:
```
iw list | grep "Supported interface modes" -A 10
```
Monitor mode must appear in the supported modes list.
