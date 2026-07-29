"""
NetReaper - Interactive menu system
Author: 09azo14 | License: MIT
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import questionary
from questionary import Style as QStyle

from modules import crack, traffic, wireless, web, vuln, defense, recon, diff
from core.installer import show_tools_status
from core.logger import SessionLogger
from core.utils import show_dashboard, set_learning_mode, get_learning_mode
from core.profile import TargetProfile
from core.platform import supported_modules, os_label
from modules import cve as cve_mod

console = Console()

NETREAPER_STYLE = QStyle([
    ("qmark",        "fg:#ff0000 bold"),
    ("question",     "fg:#ffffff bold"),
    ("answer",       "fg:#00ff00 bold"),
    ("pointer",      "fg:#ff0000 bold"),
    ("highlighted",  "fg:#ff0000 bold"),
    ("selected",     "fg:#00ff00"),
    ("separator",    "fg:#444444"),
    ("instruction",  "fg:#888888"),
    ("text",         "fg:#ffffff"),
    ("disabled",     "fg:#666666 italic"),
])


def _build_main_choices():
    """Build main menu choices, disabling unsupported options on current OS."""
    support = supported_modules()
    return [
        questionary.Choice("Recon & Discovery",                value="recon"),
        questionary.Choice("Vulnerabilities & CVEs",           value="vuln"),
        questionary.Choice("Attacks & Exploits",               value="exploit"),
        questionary.Choice("Password Cracking",                value="crack"),
        questionary.Choice("Traffic Analysis",                 value="traffic"),
        questionary.Choice("Wireless & Wi-Fi",                 value="wireless", disabled=not support["wireless"]),
        questionary.Choice("Web Application Testing",          value="web"),
        questionary.Choice("Defense & Monitoring",             value="defense", disabled=not support["defense"]),
        questionary.Choice("Target Profile",                   value="profile"),
        questionary.Choice("CVE Lookup",                       value="cve"),
        questionary.Choice("View Reports",                     value="reports"),
        questionary.Choice("Scan Diff",                        value="diff"),
        questionary.Choice("Learning Mode",                    value="learn"),
        questionary.Choice("Tools & Installation",             value="tools"),
        questionary.Separator(),
        questionary.Choice("Exit",                             value="exit"),
    ]


class MainMenu:
    """Main interactive menu controller."""

    def __init__(self):
        self.logger = SessionLogger()
        self.target = None
        self.profile = TargetProfile()
        self.support = supported_modules()

    def _set_target(self) -> str:
        """Prompt user for target IP/range."""
        t = Prompt.ask(
            "\n[bold cyan] Target (IP / range e.g. 192.168.1.0/24)[/]",
            default=self.target or "192.168.1.1"
        )
        self.target = t
        return t

    def _section_header(self, title: str, color: str = "red") -> None:
        console.print(Panel(f"[bold {color}]{title}[/]", border_style=color))

    def _unsupported_os_warning(self, module: str) -> bool:
        if not self.support.get(module, True):
            console.print(f"[red] Module '{module}' is not available on {os_label()}.[/]")
            return True
        return False

    def run(self) -> None:
        """Main menu loop."""
        show_dashboard()
        while True:
            console.print()
            choice = questionary.select(
                "Main Menu:",
                choices=_build_main_choices(),
                style=NETREAPER_STYLE,
                use_indicator=True,
            ).ask()

            if choice is None or choice == "exit":
                if questionary.confirm("Exit NetReaper?").ask():
                    self.logger.close()
                    console.print("\n[bold red]Bye! - NetReaper by 09azo14[/]\n")
                    break
            elif choice == "recon":
                self._menu_recon()
            elif choice == "vuln":
                self._menu_vuln()
            elif choice == "exploit":
                self._menu_exploit()
            elif choice == "crack":
                self._menu_crack()
            elif choice == "traffic":
                self._menu_traffic()
            elif choice == "wireless":
                if self._unsupported_os_warning("wireless"):
                    continue
                self._menu_wireless()
            elif choice == "web":
                self._menu_web()
            elif choice == "defense":
                if self._unsupported_os_warning("defense"):
                    continue
                self._menu_defense()
            elif choice == "tools":
                show_tools_status()
            elif choice == "reports":
                self._menu_reports()
            elif choice == "diff":
                diff.run(self.logger)
            elif choice == "profile":
                self._menu_profile()
            elif choice == "learn":
                self._toggle_learning_mode()
            elif choice == "cve":
                self._menu_cve()

    # -- Sub-menus ---------------------------------------------------------------

    def _menu_recon(self) -> None:
        self._section_header("Recon & Discovery")
        choices = [
            questionary.Choice("Ping Sweep - Discover active hosts", value="ping_sweep"),
            questionary.Choice("ARP Scan - Local network devices",     value="arp_scan"),
            questionary.Choice("Netdiscover - Host discovery",         value="netdiscover"),
            questionary.Choice("Masscan - Fast port scan",             value="masscan"),
            questionary.Choice("Fast Port Scan (-F)",                   value="fast_ports"),
            questionary.Choice("Full Port Scan (-p-)",                  value="full_ports"),
            questionary.Choice("OS and Version Detection (-A)",        value="os_detect"),
            questionary.Choice("Stealth Scan (anti-detection)",       value="stealth"),
            questionary.Choice("NSE Scripts (vulnerabilities)",        value="scripts"),
            questionary.Choice("UDP Scan (top 200 ports)",             value="udp"),
            questionary.Choice("Custom Scan (advanced mode)",        value="custom"),
            questionary.Separator(),
            questionary.Choice("<- Back",                              value="back"),
        ]
        choice = questionary.select("Recon:", choices=choices,
                                  style=NETREAPER_STYLE).ask()
        if choice and choice != "back":
            if choice == "arp_scan":
                recon.run(choice, "", self.logger)
            else:
                target = self._set_target()
                recon.run(choice, target, self.logger, self.profile)

    def _menu_vuln(self) -> None:
        self._section_header("Vulnerabilities & CVEs")
        choices = [
            questionary.Choice("NSE vulnerability scan (nmap --script vuln)", value="nmap_vuln"),
            questionary.Choice("NSE exploit scan (nmap --script exploit)",    value="nmap_exploit"),
            questionary.Choice("NSE weak auth scan (nmap --script auth)",    value="nmap_auth"),
            questionary.Choice("NSE brute force (nmap --script brute)",      value="nmap_brute"),
            questionary.Choice("SSL/TLS vulnerability scan",                 value="ssl_vuln"),
            questionary.Choice("SMB enumeration (enum4linux)",             value="smb_enum"),
            questionary.Choice("Local system audit (lynis)",               value="lynis"),
            questionary.Choice("Search exploits (searchsploit)",           value="searchsploit"),
            questionary.Separator(),
            questionary.Choice("<- Back",                                     value="back"),
        ]
        choice = questionary.select("Vulnerabilities:", choices=choices,
                                  style=NETREAPER_STYLE).ask()
        if choice and choice != "back":
            target = self._set_target()
            vuln.run(choice, target, self.logger)

    def _menu_exploit(self) -> None:
        self._section_header("Attacks & Exploits")
        choices = [
            questionary.Choice("Search exploits by service (searchsploit)", value="search"),
            questionary.Choice("Run exploit via Metasploit",                value="msf"),
            questionary.Choice("List exploits for CVE",                     value="cve"),
            questionary.Separator(),
            questionary.Choice("<- Back",                                      value="back"),
        ]
        choice = questionary.select("Exploits:", choices=choices,
                                  style=NETREAPER_STYLE).ask()
        if choice and choice != "back":
            target = self._set_target()
            from modules import exploit
            exploit.run(choice, target, self.logger)

    def _menu_crack(self) -> None:
        self._section_header("Password Cracking & Brute Force")
        choices = [
            questionary.Choice("Hash Cracking (John the Ripper)", value="john"),
            questionary.Choice("Hash Cracking (Hashcat + GPU)",  value="hashcat"),
            questionary.Choice("Identify Hash Type",             value="hashid"),
            questionary.Choice("Brute Force SSH",                value="brute_ssh"),
            questionary.Choice("Brute Force FTP",                value="brute_ftp"),
            questionary.Choice("Brute Force HTTP Login",         value="brute_http"),
            questionary.Choice("Brute Force Router Admin",       value="brute_router"),
            questionary.Choice("Brute Force SMB / Samba",        value="brute_smb"),
            questionary.Choice("Brute Force MySQL / DB",          value="brute_db"),
            questionary.Separator(),
            questionary.Choice("<- Back",                         value="back"),
        ]
        choice = questionary.select("Password Cracking:", choices=choices,
                                    style=NETREAPER_STYLE).ask()
        if choice and choice != "back":
            crack.run(choice, self.logger)

    def _menu_traffic(self) -> None:
        self._section_header("Traffic Analysis")
        choices = [
            questionary.Choice("List network interfaces",          value="interfaces"),
            questionary.Choice("Capture all traffic (.pcap)",    value="capture_all"),
            questionary.Choice("Monitor HTTP requests",            value="http"),
            questionary.Choice("Monitor DNS queries",            value="dns"),
            questionary.Choice("Capture plain-text credentials", value="creds"),
            questionary.Choice("Monitor ARP traffic",              value="arp"),
            questionary.Choice("View active hosts in real time", value="live"),
            questionary.Separator(),
            questionary.Choice("<- Back",                           value="back"),
        ]
        choice = questionary.select("Traffic:", choices=choices,
                                    style=NETREAPER_STYLE).ask()
        if choice and choice != "back":
            traffic.run(choice, self.logger)

    def _menu_wireless(self) -> None:
        self._section_header("Wireless & Wi-Fi")
        choices = [
            questionary.Choice("Enable monitor mode",                value="monitor_on"),
            questionary.Choice("Disable monitor mode",             value="monitor_off"),
            questionary.Choice("Scan Wi-Fi networks",              value="scan"),
            questionary.Choice("Capture WPA handshake",            value="capture_hs"),
            questionary.Choice("Deauth attack (disconnect)",      value="deauth"),
            questionary.Choice("Crack WPA handshake (aircrack)",  value="crack_wpa"),
            questionary.Choice("Automatic attack (wifite)",      value="wifite"),
            questionary.Separator(),
            questionary.Choice("<- Back",                             value="back"),
        ]
        choice = questionary.select("Wireless:", choices=choices,
                                    style=NETREAPER_STYLE).ask()
        if choice and choice != "back":
            wireless.run(choice, self.logger)

    def _menu_web(self) -> None:
        self._section_header("Web Application Testing")
        choices = [
            questionary.Choice("Directory brute force (gobuster)", value="gobuster"),
            questionary.Choice("Web fuzzing (ffuf)",               value="ffuf"),
            questionary.Choice("SQL Injection scan (sqlmap)",      value="sqlmap"),
            questionary.Choice("Web vulnerability scan (nikto)",  value="nikto"),
            questionary.Choice("View HTTP headers",                value="headers"),
            questionary.Choice("SSL/TLS scan",                     value="ssl"),
            questionary.Separator(),
            questionary.Choice("<- Back",                           value="back"),
        ]
        choice = questionary.select("Web Testing:", choices=choices,
                                    style=NETREAPER_STYLE).ask()
        if choice and choice != "back":
            target = self._set_target()
            web.run(choice, target, self.logger)

    def _menu_defense(self) -> None:
        self._section_header("Defense & Monitoring")
        choices = [
            questionary.Choice("View firewall rules (iptables)", value="fw_status"),
            questionary.Choice("Block specific IP",              value="block_ip"),
            questionary.Choice("View active connections",        value="connections"),
            questionary.Choice("View ARP table",                 value="arp_table"),
            questionary.Choice("View failed login attempts",     value="failed_login"),
            questionary.Choice("View processes by CPU",          value="processes"),
            questionary.Choice("fail2ban status",                value="fail2ban"),
            questionary.Choice("View listening ports",           value="listening"),
            questionary.Separator(),
            questionary.Choice("<- Back",                         value="back"),
        ]
        choice = questionary.select("Defense:", choices=choices,
                                    style=NETREAPER_STYLE).ask()
        if choice and choice != "back":
            defense.run(choice, self.logger)

    def _menu_reports(self) -> None:
        self._section_header("Reports")
        choices = [
            questionary.Choice("List reports",                  value="list"),
            questionary.Choice("Export current session to PDF", value="pdf"),
            questionary.Separator(),
            questionary.Choice("<- Back",                        value="back"),
        ]
        choice = questionary.select("Reports:", choices=choices, style=NETREAPER_STYLE).ask()
        if choice == "list":
            self.logger.list_reports()
        elif choice == "pdf":
            self.logger.export_pdf()

    def _menu_profile(self) -> None:
        self._section_header("Target Profile")
        target = self._set_target()
        info = self.profile.get_target(target)
        if not info:
            console.print("[yellow] No profile exists for this target yet.[/]")
        else:
            from rich.table import Table
            table = Table(title=f"Profile: {target}", header_style="bold magenta")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")
            table.add_row("IP", str(info.get("ip", "")))
            table.add_row("OS", str(info.get("os", "")))
            table.add_row("Ports", ", ".join(map(str, info.get("ports", []))))
            table.add_row("Services", ", ".join(map(str, info.get("services", []))))
            table.add_row("Notes", str(info.get("notes", "")))
            table.add_row("First seen", str(info.get("first_seen", "")))
            table.add_row("Last updated", str(info.get("last_seen", "")))
            console.print(table)

    def _menu_cve(self) -> None:
        self._section_header("CVE Lookup")
        choices = [
            questionary.Choice("From latest nmap scan",      value="from_nmap"),
            questionary.Choice("Manual search by service/version", value="manual"),
            questionary.Separator(),
            questionary.Choice("<- Back",                       value="back"),
        ]
        choice = questionary.select("CVE Lookup:", choices=choices, style=NETREAPER_STYLE).ask()
        if choice and choice != "back":
            target = self._set_target()
            cve_mod.run(choice, target, self.logger)

    def _toggle_learning_mode(self) -> None:
        current = get_learning_mode()
        set_learning_mode(not current)
        status = "enabled" if not current else "disabled"
        console.print(f"[bold cyan] Learning Mode {status}.[/]")
