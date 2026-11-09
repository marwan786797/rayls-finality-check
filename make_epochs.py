# Rebuild data/epochs.csv from Rayls' own epoch records. Read-only public RPC, Python 3 stdlib, ~1 min.
# rayls_epochRecord(e) returns the committee and parent_state = the last block before epoch e.
# Epoch e spans parent_state(e) .. parent_state(e+1). Header nonce = (epoch << 32) | round.
import csv, sys
from rpc import call
def rec(e): return call("rayls_epochRecord", [e]).get("result")
def blk(n): return call("eth_getBlockByNumber", [hex(n), False])["result"]
rows, e, r = [], 0, rec(0)
while True:
    nxt = rec(e + 1)
    if not nxt: break  # epoch e still running
    s, t = r[0]["parent_state"]["number"], nxt[0]["parent_state"]["number"]
    a, b = blk(s), blk(t)
    secs = int(b["timestamp"], 16) - int(a["timestamp"], 16)
    last_round = int(b["nonce"], 16) & 0xFFFFFFFF
    rows.append(dict(epoch=e, start_block=s, end_block=t, seconds=secs, blocks=t - s, last_round=last_round,
                     committee=len(r[0]["committee"]), avg_block_s=round(secs / (t - s), 3),
                     s_per_round=round(secs / last_round, 3)))
    e, r = e + 1, nxt
out = sys.argv[1] if len(sys.argv) > 1 else "epochs_rerun.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("wrote", out, len(rows), "completed epochs")
