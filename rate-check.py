#!/usr/bin/env python3
"""A separate, capped-rate diagnostic after the main concurrency sweep."""
import argparse
import importlib.util
import json
from pathlib import Path

root = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('experiment', root / 'run-experiment.py')
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', type=Path, default=Path('results/rate-check-3000'))
args = parser.parse_args()
out = args.out.resolve()
out.mkdir(parents=True, exist_ok=False)
count = int(experiment.mongo('db.getSiblingDB("mongodb_loadtest_ycsb").usertable.countDocuments({})'))
if count != 100000:
    raise RuntimeError('Run the main experiment first; 100,000 existing records required')
rows = []
for repeat in range(1, 4):
    label = f't8-target3000-r{repeat}'
    print(f'{label}: starting', flush=True)
    experiment.snapshot(out, label + '-before')
    data = experiment.execute(out, label, 'run', 8, 30, target=3000)
    experiment.snapshot(out, label + '-after')
    rows.append({'run': label, 'target_ops_s': 3000, 'threads': 8, 'metrics': data})
    (out / 'runs.json').write_text(json.dumps(rows, indent=2) + '\n')
    print(f'{label}: {data["OVERALL"]["Throughput(ops/sec)"]:.0f} ops/s; '
          f'read p99 {data["READ"]["99thPercentileLatency(us)"]/1000:.3f} ms; '
          f'intended p99 {data["Intended-READ"]["99thPercentileLatency(us)"]/1000:.3f} ms', flush=True)
