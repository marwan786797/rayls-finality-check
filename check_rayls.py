# Check Rayls mainnet finality tag + block cadence yourself. Python 3, no installs.
# Usage: python3 check_rayls.py            (read-only, public RPC, no wallet)
import json, time, urllib.request
RPC = "https://mainnet-rpc.rayls.com"
def rpc(method, params=[]):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(RPC, body, {"content-type": "application/json", "user-agent": "check"})
    return json.load(urllib.request.urlopen(req, timeout=20))["result"]

# 1) Is the newest block already final? Ask for both tags in ONE batched request, 20 times.
def both():
    body = json.dumps([{"jsonrpc": "2.0", "id": i, "method": "eth_getBlockByNumber", "params": [t, False]}
                       for i, t in enumerate(["finalized", "latest"])]).encode()
    req = urllib.request.Request(RPC, body, {"content-type": "application/json", "user-agent": "check"})
    r = sorted(json.load(urllib.request.urlopen(req, timeout=20)), key=lambda x: x["id"])
    return r[0]["result"], r[1]["result"]
same = 0
for _ in range(20):
    fin, lat = both(); same += fin["hash"] == lat["hash"]; time.sleep(0.3)
print(f"finalized  #{int(fin['number'],16):,}  {fin['hash']}")
print(f"latest     #{int(lat['number'],16):,}  {lat['hash']}")
print(f"finalized == latest in {same}/20 checks")

# 2) Cadence over the last 1,000 blocks (nonce = epoch<<32 | consensus round)
tip = int(lat["number"], 16)
a, b = rpc("eth_getBlockByNumber", [hex(tip - 1000), False]), lat
secs = int(b["timestamp"], 16) - int(a["timestamp"], 16)
rounds = (int(b["nonce"], 16) & 0xFFFFFFFF) - (int(a["nonce"], 16) & 0xFFFFFFFF)
print(f"last 1,000 blocks: {secs/1000:.3f} s per block, {secs/rounds:.3f} s per round, epoch {int(b['nonce'],16)>>32}")

# 3) Live: watch the tip for 60 seconds
seen, times, end = None, [], time.time() + 60
while time.time() < end:
    n = int(rpc("eth_blockNumber"), 16)
    if n != seen: times.append(time.time()); seen = n
    time.sleep(0.05)
gaps = sorted(y - x for x, y in zip(times, times[1:]))
print(f"live 60 s: {len(gaps)} new blocks, median gap {gaps[len(gaps)//2]:.3f} s")
