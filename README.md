# MikrotikExecutor

> A two-step toolkit for managing MikroTik RouterOS device fleets over SSH — discover which port each device is listening on, then push configuration changes across all of them in one run.

---

## Tools

| Script | Purpose |
|--------|---------|
| `range-checker.py` | Ping sweep + SSH port discovery across an IP range |
| `tikExec.py` | Bulk command executor across a device fleet |

These two scripts are designed to be used in sequence. `range-checker.py` builds the inventory. `tikExec.py` uses it.

---

## The Problem

In SP/WISP environments with mixed MikroTik fleets, SSH doesn't always run on the same port. Some devices sit on the standard port 22, others on a non-standard port (such as 2282) as a basic security hardening measure. Before running a bulk configuration push, you need to know which port each device is accessible on — otherwise your automation either fails silently or requires manual lookup per device.

---

## Step 1 — range-checker.py

Scans an IP range and sorts reachable devices by SSH port into two output files.

**What it does:**
1. Ping sweeps the range — skips unreachable hosts immediately
2. Probes each live host on port 2282 first, then falls back to port 22
3. Writes results to `ssh2282.txt` and `ssh22.txt`

**Setup:**

```python
start_ip = [10, 105, 10,   2]
end_ip   = [10, 105, 11, 254]

USERNAME = "admin"
PASSWORD = "your_password_here"
PORTS    = [2282, 22]   # probed in this order
```

**Run:**

```bash
python range-checker.py
```

**Output:**
```
─── 10.105.10.5
  [ssh] 10.105.10.5:2282 ... OK

─── 10.105.10.6
  unreachable — skipping

─── 10.105.10.7
  [ssh] 10.105.10.7:2282 ... socket error: Connection refused
  [ssh] 10.105.10.7:22 ... OK

Done.
  Port 22   → ssh22.txt
  Port 2282 → ssh2282.txt
```

> **Note:** Authentication failures are treated as successful port discovery — if SSH rejects the credentials, the port is open. The IP is still written to the output file.

---

## Step 2 — tikExec.py

Bulk command executor. Reads a list of IPs from `ipList.txt`, SSHs into each one, runs every command in the `COMMANDS` list, and logs the output.

The `COMMANDS` list is the only thing you need to change between jobs — add, remove, or swap commands freely. The loop handles everything else.

**Setup:**

```python
USERNAME = "admin"
PASSWORD = "your_password_here"
SSH_PORT = 2282        # use 22 or 2282 depending on which group you're targeting

COMMANDS = [
    "ip dns set allow-remote-requests=no",
    "ip service set winbox address=10.0.0.0/8",
    "ip service set www address=10.0.0.0/8",
    "ip service set ssh address=10.0.0.0/8",
]
```

Populate `ipList.txt` from whichever `range-checker` output file matches the port you've set:

```
10.105.10.5
10.105.10.7
10.105.11.2
```

**Run:**

```bash
python tikExec.py
```

Console gives live pass/fail feedback. `results.txt` logs per-device command output — MikroTik RouterOS returns no output on successful commands, so `(no output)` means it worked.

---

## Full Workflow

```bash
# 1. Discover SSH ports across the fleet
python range-checker.py
# → produces ssh22.txt and ssh2282.txt

# 2. Push changes to port 2282 devices
#    Copy ssh2282.txt → ipList.txt, set SSH_PORT = 2282
python tikExec.py

# 3. Push changes to port 22 devices
#    Copy ssh22.txt → ipList.txt, set SSH_PORT = 22
python tikExec.py
```

---

## Default Commands (Security Hardening Example)

`tikExec.py` ships with a MikroTik security hardening example:

| Command | What It Does |
|---------|-------------|
| `ip dns set allow-remote-requests=no` | Disables open DNS resolver — prevents DNS amplification |
| `ip service set winbox address=10.0.0.0/8` | Restricts Winbox to RFC1918 addresses only |
| `ip service set www address=10.0.0.0/8` | Restricts HTTP management to RFC1918 |
| `ip service set ssh address=10.0.0.0/8` | Restricts SSH to RFC1918 |

---

## Requirements

- Python 3.x
- [Paramiko](https://www.paramiko.org/)

```bash
pip install -r requirements.txt
```

> ⚠️ Shared credentials across a managed device fleet is common in SP/WISP environments. Do not commit credentials to version control.

---

## Stack
