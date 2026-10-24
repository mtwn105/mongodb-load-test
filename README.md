# MongoDB load testing with YCSB

A reproducible local concurrency experiment: MongoDB 8.0.34, 100,000 records, 95% point reads / 5% single-field updates, 1/8/32/64 threads and three repeats. Raw results, HDR histograms and server snapshots are included after execution.

## Requirements

- Docker Engine with Compose, Java JDK 21, Maven and Python 3.11+.
- Linux/WSL2 for the full evidence-collection script (`/usr/bin/time`, cgroup v2 counters and `sha256sum`).
- Internet access for the pinned image and Maven artifacts. No Atlas account or paid service is required.

## Run it

From this directory:

```bash
./setup.sh
docker compose up -d --wait
python3 run-experiment.py --out results/my-experiment
```

Expect roughly seven minutes plus initial downloads and loading. The script loads a fresh collection, verifies the inserted count, captures an explain plan, runs a 20-second server-cache warm-up, then executes twelve 30-second measurements. Each measurement uses a new JVM. JIT/connection ramp and client initialization after the YCSB timer starts remain in its measurements. Concurrency order rotates across repeats to reduce a simple order bias. There is no target rate in the main sweep.

It refuses an existing output directory and a nonempty lab collection. The default URI is deliberately fixed to the local port and disposable mongodb_loadtest_ycsb database. It is not a production/Atlas load tool. The binding prints its URI; use these local no-secret settings for this project.

The server is standalone, unauthenticated, bound to localhost:27028, limited to two CPUs and 2 GiB RAM, with a 0.5 GiB WiredTiger cache. The exact image digest is pinned in compose.yaml. The volume persists across restarts. CPU quota is a shared scheduling limit, not dedicated CPU isolation.

## Run one YCSB command

```bash
./ycsb.sh run -s -P workload.properties -threads 8 \
  -p maxexecutiontime=30 \
  -p 'mongodb.url=mongodb://127.0.0.1:27028/mongodb_loadtest_ycsb?w=1&readPreference=primary&readConcernLevel=local&maxPoolSize=128&retryWrites=false&waitQueueTimeoutMS=2000&connectTimeoutMS=5000&socketTimeoutMS=5000&serverSelectionTimeoutMS=5000'
```

Run this only after data has been loaded. The wrapper directly invokes YCSB's standard site.ycsb.Client and the unmodified synchronous MongoDB binding. The two binding source files are included because the standalone binding JAR is not published at the attempted Maven coordinate. Provenance and upstream Apache license are in vendor/.

YCSB core 0.17.0 and Java driver 3.8.0 are historical pinned dependencies, not a recommendation for a current application driver. They were exercised against this server for the documented CRUD workload. JAXB API is explicitly included for Java 21 histogram export. DEPENDENCIES.sha256 and vendor/SHA256SUMS verify exact artifacts/source; setup checks both.

## What is measured

Each document has ten 100-byte fields, plus BSON field/key/type overhead. Reads return all fields by _id; updates use _id and $set one field. Uniform key selection deliberately differs from stock workload B's Zipfian default. Only the normal _id index exists. Writes request w:1 and no j:true; write retries are disabled. It does not measure majority acknowledgment, failover, replication or transactions.

READ/UPDATE latencies are measured around binding calls by YCSB, in microseconds; convert to milliseconds by dividing by 1,000. Return=OK counts must equal operations. The script checks this instead of relying on the Java process exit code. The overall throughput metric can otherwise count unsuccessful attempts. Successful operation latency and failed-operation latency are separate.

At the configured large operationcount, maxexecutiontime ends each run. YCSB finite synchronous workers form a closed-loop test: slowing responses reduce arrivals. `measurement.interval=both` also exports intended measurements; without -target these are not a fixed-arrival-rate experiment. For a capped diagnostic run add `-target 2000`, compare achieved rate and Intended-READ latency, and preserve the output. This is still a finite-worker scheduler rather than independent incoming API traffic.

## Evidence layout

- results/environment.json: actual server/host/runtime versions and configured resource limits.
- results/experiment-1/: measured stdout, stderr/status intervals, HDR logs, exact commands, generator /usr/bin/time reports, serverStatus/collection/cgroup snapshots, runs.json and runs.csv.
- results/smoke-*: small live connectivity/load/read/update checks, separate from the experiment.
- results/attempt-1-jaxb/: an unsuccessful histogram-export attempt, retained and excluded from results.
- RESULTS.md: generated interpretation and limitations after analysis.

Snapshots before/after include diagnostic queries and process overhead; CPU deltas are coarse evidence, not synchronized per-operation profiling. Shared WSL2/Docker Desktop resources and fresh JVMs contribute variation. Data/cache size and run duration limit what these results establish.

## Capped-rate follow-up

After the main experiment, run `python3 rate-check.py --out results/my-rate-check` for three 30-second runs at an aggregate 3,000 ops/s target using eight threads. Inspect READ and Intended-READ latency separately. The recorded results/rate-check-3000/ preserves this follow-up.

## Reset and cleanup

```bash
docker compose down
```

This stops the lab and retains data. To repeat the full loading experiment from an empty lab:

```bash
docker compose down -v
docker compose up -d --wait
python3 run-experiment.py --out results/another-experiment
```

The `-v` command deletes this project's disposable MongoDB volume. It does not remove saved results. Do not run multiple copies simultaneously using the same project name/port.

## Article

Companion article by Amit Wani: “Can Your Self-Hosted MongoDB Handle the Load?” Public Medium link is pending publication. See VALIDATION.md for executed checks and limits.
