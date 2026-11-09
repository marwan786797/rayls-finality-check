# Print the stall summary from find_stalls.py output: single gaps of 30 min+, and degraded windows.
# Usage: python3 list_stalls.py [stalls_rerun.json]
import json, sys, datetime as dt
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "data/stalls.json"))
P = lambda s: dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S UTC")
def hm(s): m = round(s / 60); return f"{m//60}h {m%60:02d}m" if m >= 60 else f"{m}m"
print(f"blocks 1 to {d['tip']:,}  |  {len(d['stalls'])} gaps of 60 s+  |  {d['total_stall_s']/3600:.2f} h no new block  |  {100*d['share_producing']:.2f}% producing")
print("\nsingle gaps of 30 min or more (UTC)")
for g in d["stalls"]:
    if g["gap_s"] >= 1800:
        print(f"  {g['from_utc'][:16]} to {g['to_utc'][5:16]}  {hm(g['gap_s']):>7}  after block {g['before']:,}")
eps = []
for g in d["stalls"]:
    a, b = P(g["from_utc"]), P(g["to_utc"])
    if eps and (a - eps[-1][1]).total_seconds() < 1800: eps[-1][1] = b; eps[-1][2] += g["gap_s"]; eps[-1][3] += 1
    else: eps.append([a, b, g["gap_s"], 1])
print("\ndegraded windows (many short gaps)")
for a, b, s, n in eps:
    if n > 2: print(f"  {a:%Y-%m-%d %H:%M} to {b:%H:%M}  {n:>2} gaps  {hm(s):>7} no new block")
