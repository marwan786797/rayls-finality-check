# Find every Rayls mainnet stall: 60 s or more in which the chain produced no block with a newer timestamp.
# Read-only public RPC, Python 3 stdlib, about 3 to 6 minutes. Needs rpc.py beside it.
#
# Rayls block timestamps are NOT always increasing: after some incidents a burst of late-committed
# batches carries timestamps hours older than the block before them (e.g. block 5,777,478 is stamped
# 12 h earlier than block 5,777,477). Measuring block-to-block gaps then invents stalls that never
# happened. So a stall here is a jump in the RUNNING MAXIMUM timestamp over the whole chain.
#
# Method: read every 100th block; keep the running max of those samples; any 100-block span where the
# running max moved more than 1.3x the local median span (so any hidden 60 s gap shows) is read block by
# block, together with the span before it, so a newer timestamp hidden between samples is not missed.
import datetime as dt, json, sys, time
from rpc import call, batch
def f(t): return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
def get(ns):
    ns = list(ns)
    for _ in range(4):
        try: return batch([("eth_getBlockByNumber", [hex(n), False]) for n in ns])
        except Exception: time.sleep(2)
    raise SystemExit("RPC failed")
tip = int(call("eth_blockNumber")["result"], 16)
STEP = 100
ns = list(range(1, tip, STEP)) + [tip]; T = {}
for k in range(0, len(ns), 100):
    for n, b in zip(ns[k:k+100], get(ns[k:k+100])): T[n] = int(b["timestamp"], 16)
M, m = {}, 0
for n in ns: m = max(m, T[n]); M[n] = m
D = [0] + [M[ns[i]] - M[ns[i-1]] for i in range(1, len(ns))]
def med(i):
    w = sorted(D[max(1, i - 25):i + 26]); return w[len(w) // 2]
sus = [i for i in range(1, len(ns)) if D[i] >= 60 and D[i] > 1.3 * med(i)]
# merge into block ranges, each starting one sample earlier
ranges = []
for i in sus:
    a, b = ns[max(0, i - 2)], ns[i]
    if ranges and a <= ranges[-1][1]: ranges[-1][1] = b
    else: ranges.append([a, b])
print("tip", tip, "| ranges read block by block:", len(ranges), file=sys.stderr)
stalls, backwards = [], []
for a, b in ranges:
    ts = []
    for k in range(a, b + 1, 100):
        ts += [(int(x["number"], 16), int(x["timestamp"], 16)) for x in get(range(k, min(k + 100, b + 1)))]
    hi_n, hi_t = ts[0][0], max(ts[0][1], M[a])
    for n, t in ts[1:]:
        if t < hi_t - 60: backwards.append(dict(block=n, ts_utc=f(t), behind_s=hi_t - t))
        if t > hi_t:
            if t - hi_t >= 60: stalls.append(dict(before=hi_n, after=n, from_utc=f(hi_t), to_utc=f(t), gap_s=t - hi_t))
            hi_n, hi_t = n, t
gen = T[1]; tip_t = M[tip]
down = sum(s["gap_s"] for s in stalls)
out = sys.argv[1] if len(sys.argv) > 1 else "stalls_rerun.json"
json.dump(dict(tip=tip, genesis_ts_utc=f(gen), tip_ts_utc=f(tip_t), total_stall_s=down,
               share_producing=round(1 - down / (tip_t - gen), 5), stalls=stalls,
               backwards_timestamps=backwards), open(out, "w"), indent=1)
print(f"{len(stalls)} gaps of 60 s+, total {down/3600:.2f} h, producing blocks {100*(1-down/(tip_t-gen)):.2f}% "
      f"of the time; {len(backwards)} blocks stamped 60 s+ older than an earlier block. Wrote {out}")
