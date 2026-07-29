 ```
 ███▄    █ ▓█████▄▄▄█████▓    ██▀███  ▓█████ ▄▄▄       ██▓███  ▓█████  ██▀███
 ██ ▀█   █ ▓█   ▀▓  ██▒ ▓▒   ▓██ ▒ ██▒▓█   ▒████▄    ▓██░  ██▒▓█   ▀ ▓██ ▒ ██▒
▓██  ▀█ ██▒▒███  ▒ ▓██░ ▒░   ▓██ ░▄█ ▒▒███  ▒██  ▀█▄  ▓██░ ██▓▒▒███   ▓██ ░▄█ ▒
▓██▒  ▐▌██▒▒▓█  ▄░ ▓██▓ ░    ▒██▀▀█▄  ▒▓█  ░██▄▄▄▄██ ▒██▄█▓▒ ▒▓█  ▄ ▒██▀▀█▄
██░   ▓██░░▒████▒ ▒██▒ ░    ░██▓ ▒██▒░▒████▒▓█   ▓██▒▒██▒ ░  ░░▒████▒░██▓ ▒██▒
░ ▒░   ▒ ▒ ░░ ▒░ ░ ▒ ░░      ░ ▒▓ ░▒▓░░░ ▒░ ░▒▒   ▓▒█░▒▓▒░ ░  ░░░ ▒░ ░░ ▒▓ ░▒▓░
 ```
# NetReaper

NetReaper is a command-line security testing framework designed for use in
isolated, off-grid network laboratory environments. It provides a unified
interactive interface for executing reconnaissance, vulnerability assessment,
traffic analysis, wireless auditing, and credential testing operations against
target infrastructure that has been explicitly prepared for security testing.

The tool is intended for security professionals, penetration testers, and
network administrators who operate controlled test labs. It is not designed
for, and must not be used against, any network or system without documented
authorization from its owner.

---

## Legal Notice

NetReaper is provided for authorized security testing and educational purposes
only. The author assumes no liability for any damage or legal consequence
arising from unauthorized or improper use. Using this tool against any system,
network, or device without explicit written authorization from the owner is
illegal under computer crime laws in most jurisdictions, including but not
limited to the Computer Fraud and Abuse Act (CFAA) in the United States and
the Computer Misuse Act in the United Kingdom.

By using NetReaper, you accept full legal responsibility for your actions.

---

## License

MIT License. Copyright (c) 2024 09azo14.

See [LICENSE](LICENSE) for the full license text.

---

## Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Module Reference](#module-reference)
- [Configuration](#configuration)
- [Reports and Logging](#reports-and-logging)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)

---

## Features

**Reconnaissance and Discovery**
Maps the target network using multiple complementary techniques including
ICMP ping sweeps, ARP-layer device discovery, TCP SYN scanning, UDP scanning,
operating system fingerprinting, and service version detection. Supports
predefined scan profiles ranging from minimal footprint stealth scans to
aggressive comprehensive audits.

**Vulnerability Assessment**
Runs Nmap NSE vulnerability and exploit scripts against discovered services,
performs SSL/TLS configuration analysis, SMB enumeration, and system-level
auditing via Lynis. Integrates with the Exploit Database through searchsploit
for CVE-based exploit lookup.

**Password and Credential Testing**
Supports dictionary attacks and incremental brute force against password hashes
using John the Ripper and Hashcat. Performs online credential testing against
SSH, FTP, HTTP, SMB, RDP, and database services using Hydra. Includes automatic
hash type identification via hashid.

**Traffic Analysis**
Captures and filters network traffic using tshark and tcpdump. Provides
preconfigured filters for HTTP request monitoring, DNS query inspection,
cleartext credential extraction, and ARP activity surveillance. Saves captures
in standard pcap format compatible with Wireshark.

**Wireless Auditing**
Manages adapter monitor mode, scans for 802.11 networks, captures WPA/WPA2
handshakes, performs deauthentication attacks, and runs offline handshake
cracking via aircrack-ng. Supports automated multi-target WiFi assessment
through wifite.

**Web Application Testing**
Performs directory and file enumeration via gobuster and ffuf, SQL injection
discovery via sqlmap, comprehensive web vulnerability scanning via nikto, and
SSL configuration testing. Supports both GET parameter and form-based SQL
injection discovery.

**Defense and Monitoring**
Provides read access to iptables rule sets, active connection tables, ARP
cache, routing tables, authentication log analysis, process inspection, and
fail2ban status. Also supports writing firewall rules to block specific hosts.

**Automatic Dependency Management**
Detects the system package manager and installs any missing tools before use.
Checks all tools on startup without reinstalling those already present.

**Session Reporting**
Logs all executed commands, their full output, target addresses, timestamps,
and module context to a structured session directory. Reports are saved in
both plain text and HTML format. Sessions can be consolidated into a PDF
document.

---

## System Requirements

**Operating System**
Linux only. Tested on Kali Linux 2023.x, Ubuntu 22.04 LTS, Debian 12,
and ParrotOS 5.x. Some modules require kernel support for raw sockets and
wireless monitor mode.

**Python Version**
Python 3.8 or later. Python 3.10 or later is recommended.

**Privileges**
Root privileges (or sudo) are required for most scanning modules. Specifically,
raw socket operations used by Nmap SYN scanning, ARP scanning, monitor mode
management, and packet capture all require elevated permissions.
NetReaper does not run all operations as root; it requests sudo only for the
individual commands that require it.

**Network Interface**
A standard Ethernet or wireless network adapter. Wireless modules require
an adapter that supports monitor mode and packet injection.

**Disk Space**
Minimum 200 MB for the application and dependencies. Traffic captures and
reports may require additional space depending on session duration and activity.

---

## Installation

### Option 1: Automated Installation (Recommended)

Clone the repository and run the installation script as root:

```
git clone https://github.com/09AZ014/netreaper.git
cd netreaper
sudo ./install.sh
```

The installation script will:
- Detect the system package manager
- Install all required system tools individually, skipping those already present
- Install Python dependencies from requirements.txt
- Copy the project to /opt/netreaper
- Create a system-wide symlink at /usr/local/bin/netreaper
- Generate a built-in wordlist for router credential testing

After installation, run NetReaper from any directory:

```
netreaper
```

### Option 2: Manual Installation

Install system tools using your package manager. The full list of tools and
their package names is documented in [docs/guides/dependencies.md](docs/guides/dependencies.md).

Install Python dependencies:

```
pip install -r requirements.txt
```

Run directly from the project directory:

```
python3 netreaper.py
```

### Option 3: Development Setup

```
git clone https://github.com/09AZ014/netreaper.git
cd netreaper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock flake8 mypy bandit
python3 netreaper.py
```

---

## Quick Start

Run NetReaper:

```
sudo netreaper
```

The interface presents a top-level menu. Use the arrow keys to navigate and
Enter to select. Press Ctrl+C at any point to cancel a running operation and
return to the menu. The session is logged automatically; no manual setup is
required.

### First run - discover devices on the local network

1. Select "Reconnaissance and Discovery"
2. Select "ARP Scan - local network devices"
3. Review the list of discovered hosts
4. Note the IP addresses for subsequent scans

### Scan a specific target

1. Select "Reconnaissance and Discovery"
2. Select "Service Version Detection"
3. Enter the target IP address when prompted
4. Review open ports and service versions in the output

---

## Module Reference

Detailed documentation for each module is available in the [docs/modules/](docs/modules/) directory:

| Module | Documentation |
|---|---|
| Reconnaissance | [docs/modules/recon.md](docs/modules/recon.md) |
| Vulnerability Assessment | [docs/modules/vuln.md](docs/modules/vuln.md) |
| Password Cracking | [docs/modules/crack.md](docs/modules/crack.md) |
| Traffic Analysis | [docs/modules/traffic.md](docs/modules/traffic.md) |
| Wireless Auditing | [docs/modules/wireless.md](docs/modules/wireless.md) |
| Web Application Testing | [docs/modules/web.md](docs/modules/web.md) |
| Defense and Monitoring | [docs/modules/defense.md](docs/modules/defense.md) |

---

## Configuration

NetReaper does not require a configuration file for standard operation.
Runtime parameters such as target addresses, interfaces, wordlists, and
scan options are entered interactively through the menu system.

---

## Reports and Logging

Every NetReaper session creates a timestamped directory under `reports/`:

```
reports/
reports/2024-01-15_14-30-22/
reports/2024-01-15_14-30-22/session.log
reports/2024-01-15_14-30-22/nmap_recon_192.168.1.1.txt
```

The session log records every command executed, the target address, the
module that issued it, the timestamp, and the full output.

To view past sessions, select "View Reports" from the main menu.

To export a session to PDF, select the session from the reports menu and
choose the PDF export option.

---

## Testing

Run the test suite:

```
python3 -m pytest tests/ -v
```

Run with coverage report:

```
python3 -m pytest tests/ --cov=. --cov-report=term-missing
```

Run a specific module's tests:

```
python3 -m pytest tests/test_logger.py -v
```

The test suite uses mocks for all external tool invocations. No network
access, root privileges, or external tools are required to run the tests.

---

## Project Structure

```
netreaper/
├── netreaper.py          Entry point. Initializes the session and launches the menu.
├── install.sh            System installation script for Linux.
├── setup.py              Python package configuration for pip installation.
├── requirements.txt      Python dependency list.
├── LICENSE               MIT License.
├── README.md             This file.
│
├── core/                 Internal framework components.
│   ├── banner.py         ASCII art header and startup display.
│   ├── installer.py      System tool detection and automatic installation.
│   ├── logger.py         Session logging and report generation.
│   ├── menu.py           Interactive menu system and navigation controller.
│   └── utils.py          Shared utilities: command execution, interface
│                         selection, wordlist selection, input validation.
│
├── modules/              Security testing modules.
│   ├── crack.py          Hash cracking (John, Hashcat) and brute force (Hydra).
│   ├── defense.py        Firewall inspection, connection monitoring, log analysis.
│   ├── nmap_scan.py      Nmap-based reconnaissance with predefined scan profiles.
│   ├── traffic.py        Packet capture and traffic analysis (tshark, tcpdump).
│   ├── vuln.py           Vulnerability scanning (NSE scripts, sslscan, enum4linux).
│   ├── web.py            Web application testing (gobuster, sqlmap, nikto, ffuf).
│   └── wireless.py       Wireless auditing (aircrack-ng suite, wifite).
│
├── tests/                Automated test suite.
│   ├── conftest.py       Shared pytest fixtures and mock definitions.
│   └── test_*.py         Per-module unit tests.
│
├── docs/                 Extended documentation.
│   ├── modules/          Per-module reference documentation.
│   └── guides/           Operational guides and reference tables.
│
├── reports/              Runtime-generated session reports.
├── logs/                 Runtime-generated log files.
└── wordlists/            User-supplied wordlists.
```

---

## Contributing

This project is maintained by 09azo14. Contributions are accepted via pull
request against the main branch.

Before submitting a pull request:
1. Run the full test suite and confirm zero failures.
2. Run flake8 and resolve all E-level errors.
3. Add or update tests for any changed behavior.
4. Update the relevant documentation file in docs/modules/ if the change
   affects user-facing behavior.

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## Troubleshooting

**"Permission denied" when running scans**
Most scanning operations require root. Run with sudo or as root.

**A tool reports "command not found" inside NetReaper**
Run the installation check from the Tools and Installation menu. If a tool
cannot be installed automatically, the menu displays the manual installation
command.

**No wireless interfaces appear in the wireless module**
The adapter may not support monitor mode. Verify with: `iw list | grep monitor`
A compatible adapter is required.

**tshark prompts for group membership**
Add your user to the wireshark group: `sudo usermod -aG wireshark $USER`
Log out and back in for the change to take effect.

**Reports directory fills disk space**
Session data is never deleted automatically. Remove old sessions from the
reports/ directory manually.
