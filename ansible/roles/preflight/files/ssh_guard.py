import ipaddress
import subprocess
import sys

networks = [ipaddress.ip_network(n, strict=False) for n in sys.argv[1:]]
output = subprocess.run(
    ["ss", "-Htn", "state", "established", "( sport = :22 )"],
    capture_output=True,
    text=True,
    check=False,
).stdout

outside = set()
for line in output.splitlines():
    parts = line.split()
    if len(parts) < 4:
        continue
    peer = parts[-1].rsplit(":", 1)[0].strip("[]")
    if peer.startswith("::ffff:"):
        peer = peer[7:]
    try:
        address = ipaddress.ip_address(peer)
    except ValueError:
        continue
    if address.is_loopback:
        continue
    if not any(address.version == n.version and address in n for n in networks):
        outside.add(str(address))

if outside:
    print(", ".join(sorted(outside)))
    sys.exit(1)
