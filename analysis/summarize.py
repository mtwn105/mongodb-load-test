#!/usr/bin/env python3
"""Derive reporting values directly from all retained repetitions."""
from pathlib import Path
from statistics import median
import json
import re

root = Path(__file__).resolve().parents[1]
folder = root / 'results/experiment-1'
rows = json.loads((folder / 'runs.json').read_text())
assert len(rows) == 12, 'Wait for all 12 runs; do not summarize a selected subset'
def number(value):
    if isinstance(value, dict):
        return (value['high'] << 32) + (value['low'] & 0xffffffff)
    return value

report = {'runs': [], 'groups': []}
for row in rows:
    before = json.loads((folder / f'{row["run"]}-before.json').read_text())
    after = json.loads((folder / f'{row["run"]}-after.json').read_text())
    elapsed = (number(after['status']['uptimeMillis']) - number(before['status']['uptimeMillis'])) / 1000
    usage = int(after['cpu_stat']['usage_usec']) - int(before['cpu_stat']['usage_usec'])
    throttled = int(after['cpu_stat']['nr_throttled']) - int(before['cpu_stat']['nr_throttled'])
    periods = int(after['cpu_stat']['nr_periods']) - int(before['cpu_stat']['nr_periods'])
    row['server_average_cpu_cores'] = usage / 1e6 / elapsed
    row['cpu_throttled_periods'] = throttled
    row['cpu_total_periods'] = periods
    row['cpu_throttled_period_fraction'] = throttled / periods
    time_text = (folder / f'{row["run"]}-generator.txt').read_text()
    user = float(re.search(r'User time \(seconds\): ([\d.]+)', time_text)[1])
    system = float(re.search(r'System time \(seconds\): ([\d.]+)', time_text)[1])
    row['generator_cpu_seconds'] = user + system
    row['generator_average_cpu_cores'] = (user + system) / (row['runtime_ms'] / 1000)
    report['runs'].append(row)
for threads in (1, 8, 32, 64):
    group = [r for r in rows if r['threads'] == threads]
    assert len(group) == 3
    result = {'threads': threads}
    for metric in ('throughput_ops_s','read_p50_ms','read_p95_ms','read_p99_ms','update_p99_ms',
                   'server_average_cpu_cores','cpu_throttled_period_fraction','generator_average_cpu_cores'):
        values = [r[metric] for r in group]
        result[metric] = {'median': median(values), 'min': min(values), 'max': max(values)}
    report['groups'].append(result)
report['total_measured_operations'] = sum(r['read_operations'] + r['update_operations'] for r in rows)
(root / 'results/analysis.json').write_text(json.dumps(report, indent=2) + '\n')
for g in report['groups']:
    print(g['threads'], {k: round(v['median'], 3) for k,v in g.items() if isinstance(v,dict)})
print('Total measured operations:', report['total_measured_operations'])

rate_rows = json.loads((root / 'results/rate-check-3000/runs.json').read_text())
assert len(rate_rows) == 3
report['rate_check'] = {}
for name, op, metric in [('throughput_ops_s','OVERALL','Throughput(ops/sec)'), ('read_p99_us','READ','99thPercentileLatency(us)'), ('intended_read_p99_us','Intended-READ','99thPercentileLatency(us)'), ('update_p99_us','UPDATE','99thPercentileLatency(us)')]:
    values = [r['metrics'][op][metric] for r in rate_rows]
    report['rate_check'][name] = {'median':median(values),'min':min(values),'max':max(values)}
(root / 'results/analysis.json').write_text(json.dumps(report, indent=2) + '\n')
print('Capped-rate check:', report['rate_check'])
