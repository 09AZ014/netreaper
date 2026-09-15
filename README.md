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
- [CLI Options](#cli-options)
- [Non-interactive Module Commands](#non-interactive-module-commands)
- [Watch Mode](#watch-mode)
- [Configuration](#configuration)
- [Docker](#docker)
- [Module Reference](#module-reference)
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
for CVE-based exploit lookup, and with the NVD API for CVE detail lookup.

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

**Scan Comparison and Watch Mode**
Stores scan results as structured snapshots and compares two runs to report
new or missing hosts, opened or closed ports, and service or OS changes. Watch
mode re-runs a scan on an interval and raises an alert, optionally to a webhook,
when the comparison detects a change.

**Target Profiles**
Persistent per-target notes, discovered ports, services and operating system
information, stored locally and reused across sessions.

**Learning Mode**
Explains what a command does and why it is being run before executing it,
intended for operators who are new to the underlying tools.

**Automatic Dependency Management**
Detects the system package manager, waits for package-manager locks, recovers
from interrupted package states, and installs missing tools. Checks all tools
on startup without reinstalling those already present.

**Non-interactive CLI**
Every module action can also be run directly from the command line with
subcommands, targets and options, for scripting and CI use.

**Cross-platform Support**
Detects the host operating system and adapts command construction accordingly.
Modules whose underlying tools are unavailable on the host are marked as such
rather than failing at run time.

**Session Reporting**
Logs all executed commands, their full output, target addresses, timestamps,
and module context to a structured session directory. Reports are saved in
both plain text and HTML format. Sessions can be consolidated into a PDF
document.

---

## System Requirements

**Operating System**
Linux, Windows 10/11 and macOS are supported. The most complete tool coverage
is on Linux; tested on Kali Linux 2023.x, Ubuntu 22.04 LTS, Debian 12 and
ParrotOS 5.x. Some modules require kernel support for raw sockets and wireless
monitor mode, which is only available on Linux. The Wireless and Defense
modules are therefore disabled on Windows because the underlying tools are not
available there.

**Python Version**
Python 3.8 or later. Python 3.10 or later is recommended.

**Privileges**
Root privileges (or sudo) are required for most scanning modules. Specifically,
raw socket operations used by Nmap SYN scanning, ARP scanning, monitor mode
management, and packet capture all require elevated permissions. On Windows,
an elevated administrator shell is required for equivalent operations.
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

**Linux / macOS**

```bash
git clone https://github.com/09AZ014/netreaper.git
cd netreaper
sudo ./install.sh
```

The installation script will:
- Detect the system package manager
- Wait for any active package-manager lock and recover from an interrupted
  package state before installing
- Install all required system tools individually, skipping those already present
- Install Python dependencies from requirements.txt
- Copy the project to /opt/netreaper
- Create a system-wide symlink at /usr/local/bin/netreaper
- Generate a built-in wordlist for router credential testing

After installation, run NetReaper from any directory:

```
netreaper
```

**Windows**

Open PowerShell or Command Prompt in the project folder and run one of:

```powershell
# PowerShell
.\install.ps1
```

```bat
REM Command Prompt
install.bat
```

### Option 2: Manual Installation

Install system tools using your package manager. The full list of tools and
their per-distribution package names is documented in
[docs/guides/dependencies.md](docs/guides/dependencies.md).

Install Python dependencies:

```
pip install -r requirements.txt
```

Run directly from the project directory:

```
python3 netreaper.py
```

On Windows:

```powershell
python netreaper.py
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

The test suite runs under `pytest` as well as the standard library
`unittest` runner:

```
python3 -m pytest tests/ -v
# or
python3 -m unittest discover -s tests -p 'test_*.py' -v
# or
python3 tests/run_tests.py
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

### Run a scan without the menu

```
python3 netreaper.py --quick --target 192.168.1.0/24
```

---

## CLI Options

| Option | Description |
|--------|-------------|
| `--quick` | Ping sweep followed by a fast port scan, without the menu |
| `--quiet` | Suppress the banner; print command output only |
| `--target` | Target host or range (falls back to the configuration file) |
| `--learn` | Enable learning mode (explain commands before running them) |
| `--install` | Check for and install missing tools before running |
| `--list` | List all non-interactive module actions and exit |
| `--update` | Pull the latest source and refresh tools |
| `--version` | Print the version and exit |

---

## Non-interactive Module Commands

Any module action can be run without entering the interactive menu. The
subcommands reuse the same module entry points as the menu, so behaviour is
identical.

```bash
python3 netreaper.py recon ping_sweep --target 192.168.1.0/24
python3 netreaper.py recon os_detect --target 192.168.1.10
python3 netreaper.py web nikto --target 192.168.1.20
python3 netreaper.py web gobuster --target 192.168.1.20
python3 netreaper.py vuln nmap_vuln --target 192.168.1.10
python3 netreaper.py --list
```

Run `python3 netreaper.py --list` to print every available action with its
module. When `--target` is omitted, the value from the configuration file is
used. Actions that genuinely require additional input (for example
`web sqlmap`) still prompt for it, and report a usage error instead of raising
a traceback when no terminal is attached.

---

## Watch Mode

Watch mode re-runs a scan on a fixed interval and compares the result with the
previous run. It covers the `recon`, `nmap`, `web` and `vuln` modules. Changes
are printed to the terminal, saved to the session directory, and optionally
POSTed to a webhook.

Two comparison strategies are selected automatically:

- **Semantic** when the output is host/port oriented (recon, nmap, and the
  nmap-backed vulnerability scans). Reports new or missing hosts, opened or
  closed ports, service version changes and OS changes.
- **Findings** otherwise (web scanners, sslscan, lynis, enum4linux). Reports
  result lines that appeared or disappeared. Progress output, timestamps,
  per-run request counters and volatile HTTP headers such as `Date` are
  filtered out so they do not raise false alerts.

```bash
# Re-run a ping sweep every 5 minutes
python3 netreaper.py watch --module recon --action ping_sweep --target 192.168.1.0/24

# Poll open ports every minute, stop after 10 runs, alert a webhook
python3 netreaper.py watch --module recon --action fast_ports -t 192.168.1.10 \
  --interval 60 --count 10 --webhook https://example.com/netreaper-hook

# Watch a web server for new findings every 10 minutes
python3 netreaper.py watch --module web --action nikto -t 192.168.1.20 --interval 600

# Watch vulnerability scan results every 15 minutes
python3 netreaper.py watch --module vuln --action nmap_vuln -t 192.168.1.10 --interval 900
```

| Option | Description |
|--------|-------------|
| `--module` | `recon`, `nmap`, `web` or `vuln` (default `recon`) |
| `--action` | Action to watch (see `--list`) |
| `--target` | Target host or range (falls back to the configuration file) |
| `--interval` | Seconds between runs (default from `watch_interval`) |
| `--count` | Stop after N runs; `0` runs until interrupted |
| `--webhook` | POST change alerts to this URL as JSON |

Actions that ask for input on every run (for example `web gobuster` and
`web ffuf`) would block; set the `wordlist` key or the `NETREAPER_WORDLIST`
environment variable to run them unattended.

The same feature is available from the menu under **Watch Mode**. Change
reports are saved to the session directory as `watch_change_runN.txt`.

---

## Configuration

NetReaper reads optional defaults from `data/config.json`. The file is created
the first time a value is saved and is not required for normal operation.

```json
{
    "target": "",
    "interface": "",
    "wordlist": "",
    "wordlist_dir": "",
    "timeouts": {
        "command": 300,
        "scan": 900,
        "install": 420
    },
    "nvd_api_key": "",
    "learning_mode": false,
    "watch_interval": 300,
    "watch_webhook": ""
}
```

| Key | Description |
|-----|-------------|
| `target` | Default host or range used when `--target` is not given |
| `interface` | Preferred network interface, offered first in interface prompts |
| `wordlist` | Wordlist path used without prompting (required for unattended web scans) |
| `wordlist_dir` | Directory searched for `.txt` wordlists instead of `wordlists/` |
| `timeouts.command` | Default timeout in seconds for a single command |
| `timeouts.scan` | Default timeout in seconds for long scans |
| `timeouts.install` | Timeout in seconds for a package installation |
| `nvd_api_key` | NVD API key used for CVE lookups (raises the anonymous rate limit) |
| `learning_mode` | Start in learning mode |
| `watch_interval` | Default seconds between watch-mode runs |
| `watch_webhook` | URL that watch-mode change alerts are POSTed to |

Every value can also be supplied through the environment, which takes
precedence over the file:

| Environment variable | Key |
|----------------------|-----|
| `NETREAPER_TARGET` | `target` |
| `NETREAPER_INTERFACE` | `interface` |
| `NETREAPER_WORDLIST` | `wordlist` |
| `NETREAPER_WORDLIST_DIR` | `wordlist_dir` |
| `NETREAPER_NVD_API_KEY` | `nvd_api_key` |
| `NETREAPER_LEARNING_MODE` | `learning_mode` |
| `NETREAPER_WATCH_INTERVAL` | `watch_interval` |
| `NETREAPER_WATCH_WEBHOOK` | `watch_webhook` |

---

## Docker

The repository ships a `Dockerfile` and a `docker-compose.yml`.

### Build

```bash
docker build -t netreaper:latest .
```

### Run interactive

```bash
docker run -it --rm --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/wordlists:/app/wordlists \
  netreaper:latest
```

### Run a one-shot scan

```bash
docker run --rm --cap-add=NET_RAW --cap-add=NET_ADMIN \
  netreaper:latest --quick --target 192.168.1.0/24
```

### Docker Compose

```bash
# Interactive mode (recommended)
docker-compose run --rm netreaper

# One-shot scan
docker-compose run --rm netreaper --quick --target 192.168.1.1
```

**Notes**
- The image is based on `kalilinux/kali-rolling` and includes the listed
  pentest tools, so the final size may be several GB.
- Wireless modules require `--privileged` and `network_mode: host` for Wi-Fi
  interface access.
- `NET_RAW` and `NET_ADMIN` capabilities are required for raw-socket scanning
  and packet capture.

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

Operational guides and per-distribution package tables are in
[docs/guides/](docs/guides/).

---

## Reports and Logging

Every NetReaper session creates a timestamped directory under `reports/`:

```
reports/
reports/2024-01-15_14-30-22/
reports/2024-01-15_14-30-22/session.log
reports/2024-01-15_14-30-22/nmap_recon_192.168.1.1.txt
reports/2024-01-15_14-30-22/watch_change_run3.txt
```

The session log records every command executed, the target address, the
module that issued it, the timestamp, and the full output. Module reports
contain the raw output of the specific tool.

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

Static analysis used by the CI workflow:

```
flake8 . --max-line-length=100 --count --statistics --exclude=.venv,build,dist
mypy . --ignore-missing-imports --no-strict-optional
bandit -r . -ll -x ./tests
```

---

## Project Structure

```
netreaper/
├── netreaper.py          Entry point. Parses the CLI, initializes the session
│                         and launches the menu.
├── install.sh            System installation script for Linux / macOS.
├── install.ps1           Installation script for Windows (PowerShell).
├── install.bat           Installation script for Windows (Command Prompt).
├── Dockerfile            Container image definition.
├── docker-compose.yml    Compose service with the required capabilities.
├── setup.py              Python package configuration for pip installation.
├── requirements.txt      Python dependency list.
├── LICENSE               MIT License.
├── README.md             This file.
│
├── core/                 Internal framework components.
│   ├── banner.py         ASCII art header and startup display.
│   ├── config.py         Configuration file and environment defaults.
│   ├── explanations.py   Learning-mode explanations for each action.
│   ├── installer.py      System tool detection and automatic installation.
│   ├── logger.py         Session logging and report generation.
│   ├── menu.py           Interactive menu system and navigation controller.
│   ├── parser.py         Output parsers for scan results.
│   ├── platform.py       Operating system detection and command adaptation.
│   ├── profile.py        Persistent per-target profile storage.
│   ├── snapshot.py       Structured scan snapshots for comparison.
│   ├── utils.py          Shared utilities: command execution, interface
│   │                     selection, wordlist selection, input validation.
│   └── watch.py          Interval re-scanning and change alerting.
│
├── modules/              Security testing modules. Each exposes a
│   │                     run(action, target, logger) entry point.
│   ├── crack.py          Hash cracking (John, Hashcat) and brute force (Hydra).
│   ├── cve.py            CVE lookup against the NVD API.
│   ├── defense.py        Firewall inspection, connection monitoring, log analysis.
│   ├── diff.py           Semantic comparison of two scan reports.
│   ├── exploit.py        Exploit Database lookup via searchsploit.
│   ├── nmap_scan.py      Nmap-based reconnaissance with predefined scan profiles.
│   ├── recon.py          Reconnaissance and discovery actions.
│   ├── traffic.py        Packet capture and traffic analysis (tshark, tcpdump).
│   ├── vuln.py           Vulnerability scanning (NSE scripts, sslscan, enum4linux).
│   ├── web.py            Web application testing (gobuster, sqlmap, nikto, ffuf).
│   └── wireless.py       Wireless auditing (aircrack-ng suite, wifite).
│
├── tests/                Automated test suite.
│   ├── conftest.py       Shared pytest fixtures and mock definitions.
│   ├── run_tests.py      Standard library unittest runner.
│   └── test_*.py         Per-module unit tests.
│
├── docs/                 Extended documentation.
│   ├── modules/          Per-module reference documentation.
│   └── guides/           Operational guides and reference tables.
│
├── data/                 Runtime configuration and target profiles.
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
3. Run mypy and resolve type errors in changed files.
4. Add or update tests for any changed behavior.
5. Update the relevant documentation file in docs/modules/ if the change
   affects user-facing behavior.
6. Write commit messages in the imperative mood and in English.

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## Troubleshooting

**"Permission denied" when running scans**
Most scanning operations require root. Run with sudo or as root.

**A tool reports "command not found" inside NetReaper**
Run the installation check from the Tools and Installation menu. The installer
waits for package-manager locks, recovers from an interrupted package state,
and reports any tool that is genuinely unavailable on the current distribution
so it can be installed manually.

**"dpkg was interrupted" during installation**
The installer detects this and runs `dpkg --configure -a` followed by
`apt-get -f install -y` automatically before retrying. If it persists, run
those two commands manually and re-run the installation.

**No wireless interfaces appear in the wireless module**
The adapter may not support monitor mode. Verify with: `iw list | grep monitor`
A compatible adapter is required. Wireless modules are unavailable on Windows.

**tshark prompts for group membership**
Add your user to the wireshark group: `sudo usermod -aG wireshark $USER`
Log out and back in for the change to take effect.

**Web scans in watch mode keep prompting**
Set the `wordlist` configuration key or the `NETREAPER_WORDLIST` environment
variable so the wordlist is not selected interactively on every run.

**Reports directory fills disk space**
Session data is never deleted automatically. Remove old sessions from the
reports/ directory manually.
