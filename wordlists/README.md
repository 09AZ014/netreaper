# Wordlists

This directory is intentionally empty in the repository. NetReaper does not
distribute wordlists to avoid repository size issues and to allow users to
supply lists appropriate for their specific test environment.

## Recommended Sources

**rockyou.txt**
Available on most Kali Linux installations at /usr/share/wordlists/rockyou.txt.
Download: https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt

**SecLists**
A comprehensive collection maintained by the security community.
Repository: https://github.com/danielmiessler/SecLists
Install on Kali: sudo apt-get install seclists

**router_defaults.txt**
NetReaper includes a minimal built-in list of common router credentials.
This list is generated at runtime by the installer module and is not stored
in the repository.

## Expected Structure

Place wordlists in this directory with the following naming convention:

    wordlists/
    wordlists/rockyou.txt
    wordlists/common_passwords.txt
    wordlists/directories.txt
    wordlists/router_defaults.txt

NetReaper will detect all .txt files in this directory and present them
as options in the interactive selection menus.
