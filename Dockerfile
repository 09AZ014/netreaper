# NetReaper Dockerfile
# Author: 09azo14 | License: MIT
#
# Build:
#   docker build -t netreaper:latest .
#
# Run interactive:
#   docker run -it --rm --cap-add=NET_RAW --cap-add=NET_ADMIN \
#     -v $(pwd)/reports:/app/reports \
#     -v $(pwd)/wordlists:/app/wordlists \
#     netreaper:latest
#
# Run one-shot quick scan:
#   docker run --rm --cap-add=NET_RAW --cap-add=NET_ADMIN \
#     netreaper:latest --quick --target 192.168.1.0/24

FROM kalilinux/kali-rolling:latest

ARG UID=1000
ARG GID=1000
ARG USERNAME=netreaper

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system pentest tools and Python runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    nmap \
    hydra \
    john \
    hashcat \
    nikto \
    sqlmap \
    tshark \
    tcpdump \
    aircrack-ng \
    wifite \
    gobuster \
    ffuf \
    wfuzz \
    dirb \
    sslscan \
    enum4linux \
    hping3 \
    netcat-openbsd \
    masscan \
    arp-scan \
    netdiscover \
    lynis \
    fail2ban \
    bettercap \
    ettercap-common \
    hashid \
    exploitdb \
    metasploit-framework \
    theharvester \
    smbclient \
    responder \
    crackmapexec \
    libcap2-bin \
    sudo \
    git \
    iproute2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Create non-root user. Privileged operations should be run with --privileged/--user root.
RUN groupadd -g ${GID} ${USERNAME} \
    && useradd -u ${UID} -g ${GID} -m -s /bin/bash ${USERNAME}

# Allow non-root user to run raw socket scans (nmap -sS) without sudo
RUN setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip /usr/bin/nmap \
    && setcap cap_net_raw,cap_net_admin+eip $(which tcpdump)

# Setup application directory
RUN mkdir -p /app/reports /app/logs /app/wordlists /app/data \
    && chown -R ${USERNAME}:${USERNAME} /app

# Copy application code
COPY --chown=${USERNAME}:${USERNAME} . /app

WORKDIR /app
USER ${USERNAME}

# Make sure required directories exist at runtime
RUN mkdir -p /app/reports /app/logs /app/wordlists /app/data

# Basic smoke test
RUN python3 netreaper.py --help

VOLUME ["/app/reports", "/app/wordlists", "/app/data"]

ENTRYPOINT ["python3", "netreaper.py"]
CMD ["--help"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 netreaper.py --help || exit 1

