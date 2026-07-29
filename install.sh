#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# NetReaper Installation Script
# Author: 09azo14 | License: MIT
# Usage: sudo ./install.sh
# -----------------------------------------------------------------------------

set -euo pipefail

NETREAPER_VERSION="1.0.0"
INSTALL_DIR="/opt/netreaper"
BIN_LINK="/usr/local/bin/netreaper"
LOG_FILE="/tmp/netreaper_install.log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

log()     { echo -e "${CYAN}[INFO]${RESET} $*" | tee -a "$LOG_FILE"; }
success() { echo -e "${GREEN}[OK]${RESET} $*"   | tee -a "$LOG_FILE"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET} $*" | tee -a "$LOG_FILE"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" | tee -a "$LOG_FILE"; exit 1; }

echo "============================================================" | tee "$LOG_FILE"
echo "  NetReaper v${NETREAPER_VERSION} - Installation Script"     | tee -a "$LOG_FILE"
echo "  Author: 09azo14 | License: MIT"                            | tee -a "$LOG_FILE"
echo "  Log: $LOG_FILE"                                            | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
echo ""

if [[ "$EUID" -ne 0 ]]; then
    error "This script must be run as root. Use: sudo ./install.sh"
fi

detect_pm() {
    for pm in apt-get apt yum dnf pacman; do
        if command -v "$pm" &>/dev/null; then
            echo "$pm"
            return
        fi
    done
    error "No supported package manager found (apt, yum, dnf, pacman)."
}

PM=$(detect_pm)
log "Package manager: $PM"

log "Updating package lists..."
case "$PM" in
    apt|apt-get) apt-get update -qq >> "$LOG_FILE" 2>&1 ;;
    yum|dnf)     "$PM" check-update -q >> "$LOG_FILE" 2>&1 || true ;;
    pacman)      pacman -Sy --noconfirm >> "$LOG_FILE" 2>&1 ;;
esac

install_pkg() {
    local pkg="$1"
    local name="${2:-$1}"
    if command -v "$name" &>/dev/null; then
        success "$name is already installed"
        return
    fi
    log "Installing $name..."
    case "$PM" in
        apt|apt-get) apt-get install -y -qq "$pkg" >> "$LOG_FILE" 2>&1 ;;
        yum|dnf)     "$PM" install -y -q "$pkg"   >> "$LOG_FILE" 2>&1 ;;
        pacman)      pacman -S --noconfirm "$pkg"  >> "$LOG_FILE" 2>&1 ;;
    esac
    if command -v "$name" &>/dev/null; then
        success "$name installed"
    else
        warn "$name could not be installed. Some features may be unavailable."
    fi
}

log "Installing system tools..."
install_pkg python3        python3
install_pkg python3-pip    pip3
install_pkg nmap           nmap
install_pkg john           john
install_pkg hashcat        hashcat
install_pkg hydra          hydra
install_pkg tshark         tshark
install_pkg tcpdump        tcpdump
install_pkg aircrack-ng    aircrack-ng
install_pkg wifite         wifite
install_pkg nikto          nikto
install_pkg gobuster       gobuster
install_pkg sqlmap         sqlmap
install_pkg exploitdb      searchsploit
install_pkg masscan        masscan
install_pkg arp-scan       arp-scan
install_pkg netdiscover    netdiscover
install_pkg sslscan        sslscan
install_pkg enum4linux     enum4linux
install_pkg hping3         hping3
install_pkg netcat-openbsd nc
install_pkg ffuf           ffuf
install_pkg wfuzz          wfuzz
install_pkg dirb           dirb
install_pkg lynis          lynis
install_pkg fail2ban       fail2ban-client
install_pkg bettercap      bettercap
install_pkg ettercap-common ettercap
install_pkg hashid         hashid

log "Installing Python dependencies..."
pip3 install -r "$(dirname "$0")/requirements.txt" --quiet >> "$LOG_FILE" 2>&1
success "Python dependencies installed"

log "Creating runtime directories..."
mkdir -p "$INSTALL_DIR"
cp -r "$(dirname "$0")"/* "$INSTALL_DIR/"
mkdir -p "$INSTALL_DIR/reports"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/wordlists"

ln -sf "$INSTALL_DIR/netreaper.py" "$BIN_LINK"
chmod +x "$INSTALL_DIR/netreaper.py"
success "Symlink created: netreaper -> $BIN_LINK"

log "Generating built-in wordlists..."
cat > "$INSTALL_DIR/wordlists/router_defaults.txt" << 'WORDLIST'
admin
password
1234
12345
123456
admin123
root
toor
pass
test
guest
user
support
service
netgear
linksys
motorola
default
WORDLIST
success "Router credentials wordlist created"

echo ""
echo "============================================================"
success "NetReaper v${NETREAPER_VERSION} installed successfully"
echo "  Run with: netreaper"
echo "  Log file: $LOG_FILE"
echo "============================================================"
