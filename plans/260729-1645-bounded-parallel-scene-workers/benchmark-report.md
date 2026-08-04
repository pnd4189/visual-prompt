# Benchmark Report — Bounded Parallel Pass-2 (2026-08-04)

Plan: `plans/260729-1645-bounded-parallel-scene-workers/` Phase 4.
Target: Pass-2 wall-clock ≥ ~1.8× serial on the same local batch; shortfall from
rate limits → tune `VP_WORKERS` down, NEVER loosen gates.

## Deterministic layer (measured in-session, this machine)

| Component | Fixture | Median | Note |
|---|---|---|---|
| Similarity gate (post-join, image) | 120 distinct scenes | **2.80s** (5 runs 2.78–2.87) | unchanged serial gate; runs once after join, not per worker |
| `worker_manifest.py` validate + verify-run | 40-scene worker range | **0.65 ms** | ownership fence overhead is zero |
| Contract test suite | 54 tests + 3 subtests | ~4.1s | includes 120-scene gate overhead bound (<30s) |

Conclusion: the parallel scaffolding adds no material gate overhead; the
deterministic layer is not the bottleneck — model wall-clock is.

## Gate parity (serial vs parallel)

- Identical gate set, identical order, coordinator-only, post-join: legit →
  grounding → scene artifacts → music artifacts → similarity (image/video/music)
  → anchor/safety --fix → final artifacts → final similarity → copy/cache →
  history → completion manifest. Verified by: 54-test suite green; worker modes
  (head/plan/worker/tail) never touch history/markers (TOML contract + harness
  modes + test locks).
- No threshold loosened: no `--soft/--near/--max-*` default changed; fail-closed
  exits unchanged (validated in `WorkerProtocolContractTests`).

## Live model benchmark — PROTOCOL (deferred to first real batch)

Live Pass-2 wall-clock requires real agy runs (hours + Gemini quota), so it is
measured on the next real batch, not simulated here:

1. Pick one input file with ≥120 scenes; run it serially first
   (`VP_WORKERS` unset) on a fresh local workdir; record per-file wall-clock
   from the driver log.
2. Re-run the SAME file with `VP_WORKERS=3` (fresh workdir, same model/style);
   the driver prints `parallel pass-2: N workers, Xs` for the fan-out segment.
3. Compare total per-file wall-clock (conservative — includes serial head/tail)
   and the fan-out segment vs serial Pass-2 share. Pass criterion: Pass-2
   ≥ ~1.8× serial; if Gemini per-minute rate limiting caps throughput, record
   the ceiling and tune `VP_WORKERS` DOWN (3 → 2). Gates are never loosened.
4. Known risk (plan Phase 2/3): cross-worker boundary duplication surfaces only
   at join — track first-pass similarity pass rate on that run; rewrite-loop
   cost is the efficiency loss term.

## Rollback verification

- Rollback = unset `VP_WORKERS` (config flip) + driver restart; no data
  migration. Locked by tests: serial DRYRUN emits no `parallel pass-2` marker;
  full pipeline semantics unchanged without the env (suite green).
- Any head/freeze/fan-out/join failure at runtime falls back to serial
  full generation inside the same retry loop (valid partial scenes reused via
  cache keys).

## Rollout guard

- No visual-prompt batch driver was running at verification time (checked `ps`;
  only unrelated pdf-convert sessions active).
- Enabling on the active batch requires an EXPLICIT user restart with
  `VP_WORKERS` set — the driver never opts in by itself.
