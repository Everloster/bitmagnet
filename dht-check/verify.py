#!/usr/bin/env python3
"""DHT Bootstrap Node Verifier

Sends a real DHT ping (BEP-5) to each node and records the result.
Supports two modes:
  - local:  run directly on this machine
  - ssh:    run via SSH on a remote VPS (default)

Usage:
  python3 verify.py                     # verify via VPS SSH
  python3 verify.py --local             # verify locally
  python3 verify.py --timeout 5         # custom timeout per node
  python3 verify.py --json nodes.json   # custom json path
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import textwrap
from datetime import date, datetime
from pathlib import Path

DEFAULT_JSON = Path(__file__).parent / "dht-bootstrap-nodes.json"
DHT_PING_MSG = b'd1:ad2:id20:abcdefghij0123456789e1:q4:ping1:t2:aa1:y1:qe'
DEFAULT_TIMEOUT = 3


def verify_local(nodes: list, timeout: int) -> list:
    """Verify nodes by sending DHT ping directly from this machine."""
    results = []
    for node in nodes:
        host, port = node["host"], node["port"]
        entry = {"host": host, "port": port}
        try:
            resolved = socket.gethostbyname(host) if not host[0].isdigit() else host
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(timeout)
            s.sendto(DHT_PING_MSG, (resolved, port))
            s.recvfrom(1024)
            entry.update(status="alive", resolved_ip=resolved)
        except socket.gaierror:
            entry.update(status="dns_fail", resolved_ip=None)
        except socket.timeout:
            entry.update(status="dead", resolved_ip=None)
        except Exception as e:
            entry.update(status="error", resolved_ip=None, error=str(e))
        finally:
            try:
                s.close()
            except Exception:
                pass
        results.append(entry)
    return results


def verify_via_ssh(nodes: list, timeout: int, ssh_cmd: str) -> list:
    """Verify nodes by running a Python script on the VPS via SSH (piped via stdin)."""
    node_args = json.dumps([{"host": n["host"], "port": n["port"]} for n in nodes])
    remote_script = textwrap.dedent(f"""\
        import json, socket
        msg = b'd1:ad2:id20:abcdefghij0123456789e1:q4:ping1:t2:aa1:y1:qe'
        nodes = json.loads('{node_args}')
        results = []
        for n in nodes:
            host, port = n["host"], n["port"]
            entry = {{"host": host, "port": port}}
            try:
                resolved = socket.gethostbyname(host) if not host[0].isdigit() else host
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout({timeout})
                s.sendto(msg, (resolved, port))
                s.recvfrom(1024)
                entry.update(status="alive", resolved_ip=resolved)
            except socket.gaierror:
                entry.update(status="dns_fail", resolved_ip=None)
            except socket.timeout:
                entry.update(status="dead", resolved_ip=None)
            except Exception as e:
                entry.update(status="error", resolved_ip=None, error=str(e))
            finally:
                try: s.close()
                except: pass
            results.append(entry)
        print(json.dumps(results))
    """)

    try:
        result = subprocess.run(
            ssh_cmd.split() + ["python3"],
            input=remote_script,
            capture_output=True, text=True,
            timeout=timeout * len(nodes) + 30
        )
        if result.returncode != 0:
            print(f"SSH error: {result.stderr.strip()}", file=sys.stderr)
            return []
        return json.loads(result.stdout.strip())
    except subprocess.TimeoutExpired:
        print("SSH command timed out", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Failed to parse SSH output: {e}", file=sys.stderr)
        return []


def update_json(json_path: Path, results: list, method: str):
    """Merge verification results into the JSON data file."""
    with open(json_path) as f:
        data = json.load(f)

    today = date.today().isoformat()
    result_map = {(r["host"], r["port"]): r for r in results}

    for node in data["nodes"]:
        key = (node["host"], node["port"])
        if key in result_map:
            r = result_map[key]
            node["status"] = r["status"]
            node["last_verified"] = today
            node["verified_from"] = method
            if r.get("resolved_ip"):
                node["resolved_ip"] = r["resolved_ip"]

    data["last_scan"] = datetime.now().isoformat(timespec="seconds")
    data["scan_method"] = method

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def print_report(json_path: Path):
    """Print a summary table of node status."""
    with open(json_path) as f:
        data = json.load(f)

    alive = [n for n in data["nodes"] if n["status"] == "alive"]
    dead = [n for n in data["nodes"] if n["status"] != "alive"]

    print(f"\n{'='*60}")
    print(f"  DHT Bootstrap Node Report — {data.get('last_scan', 'N/A')}")
    print(f"  Method: {data.get('scan_method', 'N/A')}")
    print(f"  Auto-update .env: {data.get('auto_update_env', False)}")
    print(f"{'='*60}")

    print(f"\n  ALIVE ({len(alive)}):")
    for n in alive:
        ip_info = f" -> {n.get('resolved_ip', '')}" if n.get("resolved_ip") else ""
        print(f"    {n['host']}:{n['port']}{ip_info}  [{n.get('source', '')}]")

    print(f"\n  DEAD/UNREACHABLE ({len(dead)}):")
    for n in dead:
        print(f"    {n['host']}:{n['port']}  [{n['status']}] [{n.get('source', '')}]")

    print(f"\n  Suggested .env value:")
    env_nodes = ",".join(f"{n['host']}:{n['port']}" for n in alive)
    print(f"    DHT_CRAWLER_BOOTSTRAP_NODES={env_nodes}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Verify DHT bootstrap nodes")
    parser.add_argument("--local", action="store_true", help="Verify from local machine")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout per node (seconds)")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON, help="Path to nodes JSON file")
    default_ssh = os.environ.get("DHT_CHECK_SSH_CMD",
                                  "ssh -o ConnectTimeout=10 user@your-vps-host")
    parser.add_argument("--ssh-cmd", default=default_ssh,
                        help="SSH command to reach VPS (or set DHT_CHECK_SSH_CMD env var)")
    args = parser.parse_args()

    with open(args.json) as f:
        data = json.load(f)

    nodes = data["nodes"]
    method = "local" if args.local else "vps"

    print(f"Verifying {len(nodes)} nodes via {method}...")

    if args.local:
        results = verify_local(nodes, args.timeout)
    else:
        results = verify_via_ssh(nodes, args.timeout, args.ssh_cmd)

    if not results:
        print("No results obtained. Check connectivity.", file=sys.stderr)
        sys.exit(1)

    update_json(args.json, results, method)
    print_report(args.json)


if __name__ == "__main__":
    main()
