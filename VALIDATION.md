# Executed validation — 2026-10-24 UTC

This project was executed against a real local MongoDB server. No database response, result chart or benchmark number was fabricated.

## Successful live checks

- Docker Compose started the pinned official MongoDB image and passed its mongosh ping healthcheck. Actual server version: 8.0.34.
- Setup compiled the two unmodified YCSB 0.17.0 synchronous binding sources against core 0.17.0 / driver 3.8.0. Java 21.0.12.1. JAXB API 2.3.1 fixed histogram export on this runtime.
- Live smoke load: 1,000 INSERT operations, all Return=OK. Live smoke run: 959 READ + 41 UPDATE, all Return=OK. Raw smoke files retained.
- Full experiment fresh load: 100,000 INSERT operations, all Return=OK; MongoDB collection count separately checked at 100,000.
- Explain captured for an actual loaded _id: EXPRESS_IXSCAN on _id_, one key/document examined and one document returned.
- Separate 20-second server-cache warm-up completed successfully. Each measured run used a fresh JVM; server-cache warm-up does not remove JIT, connection ramp and initialization after YCSB's timer starts.
- Twelve 30-second measurements: 1/8/32/64 threads, three rotating repeats; 2,753,371 READ/UPDATE operations, every status OK.
- Three additional 30-second capped-rate runs: eight threads, aggregate -target 3000. All read/update statuses OK. Achieved rate and operation/intended latency retained separately.
- Before/after serverStatus, collection stats and cgroup CPU snapshots, /usr/bin/time generator reports, exact command arguments, raw stdout/stderr and HDR interval logs saved for all measurements.
- `python3 analysis/summarize.py` passed its completeness assertions and generated results/analysis.json from every repetition. It converts Mongo shell high/low BSON integer representations when deriving elapsed CPU rates.
- `sha256sum -c DEPENDENCIES.sha256` and `sha256sum -c vendor/SHA256SUMS`: all eight runtime JARs and three source/license files verified.
- `bash -n setup.sh ycsb.sh` and Python compilation of both runners and analysis: passed.
- JFreeChart 1.5.5 plotting source compiled and rendered charts directly from all twelve recorded CSV rows. All three repeats are drawn; lines connect per-metric medians. Plot source includes a full-run count guard.

## Method and limitations

See RESULTS.md and results/environment.json for environment, workload, observations, ranges and qualifications. The server uses a two-CPU quota and 2 GiB memory limit on shared Docker Desktop/WSL2 hardware; CPU quota is not dedicated-core isolation. Storage is an uncharacterized Docker named volume. Small warmed data, short windows, historical client and local shared generator are material limits.

No API, production, remote VPS, replication, failover, transaction, aggregation or sustained soak test was performed. Operation p99 does not include all incoming-traffic queueing. Capped-rate Intended-READ p99 was materially higher; the project does not claim that an application arrival-rate SLO passed. Server CPU deltas include diagnostic overhead. No exclusive causal attribution to CPU quota is claimed.

## Failed preparation attempts retained

- Initial environment checks inside the filesystem sandbox denied Docker/network/GitHub access. Approved execution outside that sandbox succeeded; these were not enduring service-access failures.
- The GitHub release archive download stalled after 392,842 of 7,539,511 bytes / 120 seconds. The attempted Maven binding JAR coordinate was unavailable. Two pinned upstream binding source files were fetched and their Apache license retained instead.
- An initial full load inserted 100,000 records but failed HDR export on Java 21 (missing javax.xml.bind.DatatypeConverter). Output is retained in results/attempt-1-jaxb, excluded from measurements. Only the lab usertable collection was then reset before the successful fresh-load experiment.
- Python plotting dependency resolution stalled; charts were produced with JFreeChart fetched from Maven Central instead.

The article's preview/export checks are recorded in the enclosing blog workspace's validation.md; they are not part of the database benchmark.
