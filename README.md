# Why does deterministic finality matter for settlement? I checked all 14 million Rayls mainnet blocks.

Scripts and data behind my Rayls article. Everything here is read-only: public RPC
(`https://mainnet-rpc.rayls.com`, chain ID 72957), Python 3 standard library, no wallet, no keys, no installs.

## Short answer

- **Finality:** the `finalized` block equals the `latest` block on every check, so a block is final once you see it. No confirmation wait, no reorg window.
- **Liveness:** finality does not mean the chain never stops. From genesis (30 Apr 2026) to 9 Nov 2026 I found 4 single gaps of 30 min or more, 3 degraded windows in October, and 44 gaps of 60 s or more, 24.34 hours with no new block in total. The chain was producing blocks 99.47% of the time.

## Reproduce

```bash
python3 check_rayls.py      # ~70 s: finalized vs latest (20 batched checks), cadence, 60 s live watch
python3 find_stalls.py      # about 4 to 5 min: every gap of 60 s+ since genesis -> stalls_rerun.json
python3 make_epochs.py      # ~1 min: per-epoch blocks, rounds, committee size -> epochs_rerun.csv
```

Compare your `stalls_rerun.json` with `data/stalls.json` and `epochs_rerun.csv` with `data/epochs.csv`.
New stalls after 9 Nov 2026 will show up as extra rows.

## Data (snapshot 9 Nov 2026, tip block 14,143,155)

| File | What it is |
|---|---|
| `data/stalls.json`, `data/stalls.csv` | Every gap of 60 s or more: block before/after, UTC start/end, seconds |
| `data/backwards_timestamps.csv` | Blocks stamped 60 s or more older than an earlier block |
| `data/epochs.csv` | 192 completed epochs: start/end block, seconds, blocks, last round, committee size, s per block, s per round |
| `data/check_rayls_sample_output.txt` | My run of `check_rayls.py` |
| `data/status_incidents_snapshot.json`, `data/status_maintenances_snapshot.txt` | status.rayls.com incidents and scheduled maintenances, for matching halts to announcements |

## Single gaps of 30 min or more

| From (UTC) | To (UTC) | No new block | status.rayls.com |
|---|---|---|---|
| 2026-05-05 21:59 | 2026-05-06 09:42 | 11 h 43 m | Mainnet maintenance entry, started 6 May 00:37 |
| 2026-06-21 01:05 | 2026-06-21 10:14 | 9 h 09 m | Incident "Critical Network Service Interruption" + public RCA |
| 2026-10-06 17:35 | 2026-10-06 18:06 | 31 m | Incident "Blockchain stoped producing blocks" |
| 2026-10-26 19:42 | 2026-10-26 20:22 | 40 m | Incident "Blockchain stoped producing blocks" |

Degraded windows (many short gaps): 5 Oct 16:43 to 17:25 (11 gaps, 39 m stalled, no mainnet entry found),
6 Oct 16:49 to 18:49 (17 gaps, 1 h 09 m), 26 Oct 18:53 to 20:41 (10 gaps, 1 h 31 m).
Shorter gaps: 13 May (3 m, during a mainnet maintenance entry), 19 May (1 m), 21 Jun 11:00 (4 m).

### Two halts that are not real
A naive block-to-block scan also reports 27 Jul 07:42 to 15:58 (8 h 16 m) and 21 Jun 12:46 to 15:58 (3 h 13 m).
Both are timestamp artifacts: right after block 5,777,477 (stamped 27 Jul 15:58:47) come 32 blocks stamped
between 03:42 and 09:12 that same day, up to 12 h older. The epoch records agree: epoch 87 (26 to 27 Jul) has a
full day of consensus rounds (132,772), while epoch 5 (5 to 6 May) has only 66,818.

## How it works

- Block header `nonce` = `(epoch << 32) | consensus round` (Axyl: Narwhal DAG + Bullshark).
- `find_stalls.py` reads every 500th block, then reads block by block any 500-block span that ran
  much slower than normal. A gap is measured from the newest timestamp seen so far, because Rayls
  block timestamps are not always increasing: 203 blocks carry a time 60 s or more older than an earlier block,
  up to 12 h 16 m (see `data/backwards_timestamps.csv`). A stall is a jump in the running maximum timestamp.
- `make_epochs.py` uses `rayls_epochRecord(e)`; its `parent_state` is the last block before epoch `e`.

## Limits

- Sampling: every 100th block plus a block by block read of any span whose running max moved 60 s+ and
  1.3x the local median. A single 60 s gap always trips that, so the list should be complete.
- Block timestamps come from the chain. A halt is the time between block timestamps, not a measured outage of the RPC.
- This checks the public chain only, not private Rayls subnets.

## License

MIT, see `LICENSE`.
