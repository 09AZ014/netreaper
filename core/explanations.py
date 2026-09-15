"""
NetReaper - Learning mode command explanations
Author: 09azo14 | License: MIT
"""

EXPLANATIONS_KEYWORDS = {
    # Recon / nmap
    "nmap -sn": "Sends ICMP/ARP pings to discover active hosts without port scanning.",
    "nmap -F -T4 --open": "Fast scan of the 100 most common ports, showing only open ones.",
    "nmap -sS -p-": "SYN scan of all TCP ports (1-65535) to map services.",
    "nmap -A -T4 -sV --osscan-guess": "OS detection and service version detection.",
    "nmap -sS -T2 -f --data-length": "Stealth scan: fragmented packets and decoys.",
    "nmap -sC -sV": "Runs default NSE scripts and detects service versions.",
    "nmap -sU --top-ports": "UDP scan of the 200 most common ports (slower than TCP).",
    "nmap --script vuln": "Runs NSE vulnerability detection scripts.",
    "nmap --script exploit": "Runs NSE exploitation scripts (careful in production environments).",
    "nmap --script auth": "Looks for weak / no-password authentication.",
    "nmap --script brute": "Attempts brute force via NSE scripts.",
    "arp-scan --localnet": "Discovers devices on the local network via ARP.",
    "netdiscover -r": "Passive/active discovery of hosts on the network.",
    "masscan": "Ultra-fast port scanner (be careful with rate).",
    # Vuln
    "sslscan --show-certificate": "Analyzes SSL/TLS certificates and supported ciphers.",
    "enum4linux -a": "Complete enumeration of SMB/Samba shares/users.",
    "lynis audit system": "Audits local security configuration.",
    # Crack
    "john --format=auto": "Attempts to crack hashes using a wordlist.",
    "hashcat -m": "Cracks hashes using GPU/CPU with a wordlist.",
    "hydra -l": "Brute forces services with credentials.",
    # Web
    "gobuster dir -u": "Brute forces web directories/files.",
    "ffuf -u": "Multithreaded web fuzzing.",
    "sqlmap -u": "Tests and exploits SQL injection automatically.",
    "nikto -h": "Web vulnerability scanner.",
    # Wireless
    "airmon-ng start": "Puts the interface into monitor mode.",
    "airodump-ng": "Scans Wi-Fi networks for BSSIDs and clients.",
    "aireplay-ng --deauth": "Sends deauth packets to force reconnection (capture handshake).",
    "aircrack-ng": "Attempts to crack the WPA handshake with a wordlist.",
    # Defense
    "iptables -L -n -v": "Lists active firewall rules.",
    "iptables -A INPUT -s": "Blocks traffic from a specific IP.",
    "fail2ban-client status": "Shows fail2ban jails status.",
}


def explain_command(cmd: str, console) -> None:
    """Print learning-mode explanation for a command."""
    explanation = None
    for keyword, desc in EXPLANATIONS_KEYWORDS.items():
        if keyword in cmd:
            explanation = desc
            break

    if explanation:
        console.print(f"\n[bold cyan] Learning:[/] {explanation}\n")
    else:
        message = (
            "[bold cyan] Learning:[/] This command will run the indicated tool. "
            "Analyze the output to identify ports, services, and potential vulnerabilities."
        )
        console.print(f"\n{message}\n")
