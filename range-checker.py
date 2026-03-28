"""
range-checker.py
────────────────
Ping sweep + SSH port discovery across an IP range.

Use Case:
    In service provider environments with mixed device fleets, SSH may be
    listening on different ports across devices — some on the standard port 22,
    others on a non-standard port (e.g. 2282) for security hardening.

    Before running bulk configuration changes across a fleet, you need to
    know which port each device is accessible on. This script:

      1. Ping sweeps the entire IP range, skipping unreachable hosts
      2. For each reachable host, attempts SSH on port 2282 first, then port 22
      3. Writes results to two separate files (ssh2282.txt and ssh22.txt)

    The output files feed directly into bulk execution tools — you know
    exactly which port to use for each device before you touch them.

    Pairs well with tikExec.py for pre-flight inventory before a fleet
    configuration push.

Usage:
    1. Set start_ip and end_ip for your target subnet range
    2. Set username and password
    3. Run:  python range-checker.py
    4. Results written to ssh22.txt and ssh2282.txt

Dependencies:
    paramiko

Author: semantical-monster
"""

import socket
import subprocess
import time

import paramiko
from paramiko import AuthenticationException, SSHException

# ── Configuration ──────────────────────────────────────────────────────────────

start_ip = [10, 105, 10,   2]
end_ip   = [10, 105, 11, 254]

USERNAME = "admin"
PASSWORD = "password"   # <-- set before running

# Ports to probe, in order of preference
PORTS = [2282, 22]

OUTPUT_FILES = {
    2282: "ssh2282.txt",
    22:   "ssh22.txt",
}

# ── IP range generator ─────────────────────────────────────────────────────────

def ip_range(start: list, end: list):
    """
    Yield every IPv4 address from start to end (inclusive).
    Handles octet rollover correctly across /16 and larger ranges.
    """
    current = list(start)
    while current != end:
        yield ".".join(map(str, current))
        current[3] += 1
        for i in (3, 2, 1):
            if current[i] > 255:
                current[i] = 0
                current[i-1] += 1
    yield ".".join(map(str, end))

# ── Ping check ─────────────────────────────────────────────────────────────────

def is_pingable(ip: str) -> bool:
    """Return True if the host responds to a single ICMP ping."""
    try:
        result = subprocess.run(
            ["ping", "-c", "1", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  [ping error] {ip}: {e}")
        return False

# ── SSH check ──────────────────────────────────────────────────────────────────

def check_ssh(ip: str, port: int) -> bool:
    """
    Attempt an SSH connection to ip:port.
    Returns True if authentication succeeds or fails with valid credentials
    (meaning the port is open and SSH is running).
    Returns False on connection error, timeout, or socket failure.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"  [ssh] {ip}:{port} ...", end=" ", flush=True)
        client.connect(
            ip,
            port=port,
            username=USERNAME,
            password=PASSWORD,
            timeout=10,
            banner_timeout=15,
            look_for_keys=False,
        )
        print("OK")
        return True

    except AuthenticationException:
        # Auth failed but SSH is listening — port is open
        print("auth failed (port open)")
        return True

    except SSHException as e:
        print(f"SSH error: {e}")

    except EOFError:
        print("EOFError (no banner)")
        if client.get_transport():
            client.get_transport().close()

    except socket.error as e:
        print(f"socket error: {e}")

    finally:
        client.close()
        time.sleep(1)

    return False

# ── Main ───────────────────────────────────────────────────────────────────────

handles = {port: open(path, "w") for port, path in OUTPUT_FILES.items()}

try:
    for ip in ip_range(start_ip, end_ip):
        print(f"\n─── {ip}")

        if not is_pingable(ip):
            print("  unreachable — skipping")
            continue

        found = False
        for port in PORTS:
            if check_ssh(ip, port):
                handles[port].write(ip + "\n")
                found = True
                break
            time.sleep(1)

        if not found:
            print(f"  no SSH response on any port")

finally:
    for f in handles.values():
        f.close()

print("\nDone.")
print(f"  Port 22   → {OUTPUT_FILES[22]}")
print(f"  Port 2282 → {OUTPUT_FILES[2282]}")
