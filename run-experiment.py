#!/usr/bin/env python3
"""Run the documented local YCSB concurrency experiment and preserve raw evidence."""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent
URI = ('mongodb://127.0.0.1:27028/mongodb_loadtest_ycsb?w=1&readPreference=primary'
       '&readConcernLevel=local&maxPoolSize=128&retryWrites=false'
       '&waitQueueTimeoutMS=2000&connectTimeoutMS=5000&socketTimeoutMS=5000&serverSelectionTimeoutMS=5000')
CONTAINER = 'mongodb-loadtest-ycsb-mongo-1'


def docker(*args):
    return subprocess.check_output(['docker', *args], text=True).strip()


def mongo(js):
    return docker('exec', CONTAINER, 'mongosh', '--quiet', '--eval', js)


def metrics(path):
    result = {}
    for row in csv.reader(path.read_text().splitlines()):
        if len(row) == 3 and row[0].startswith('['):
            try:
                result.setdefault(row[0].strip('[]'), {})[row[1].strip()] = float(row[2])
            except ValueError:
                pass
    return result


def validate(path, names):
    data = metrics(path)
    for name in names:
        m = data.get(name, {})
        if m.get('Operations', 0) <= 0 or m.get('Return=OK') != m['Operations']:
            raise RuntimeError(f'{path.name}: missing metrics or failed {name} operations')
        if any(k.startswith('Return=') and k != 'Return=OK' and v for k, v in m.items()):
            raise RuntimeError(f'{path.name}: non-OK {name} status')
    return data


def snapshot(out, name):
    data = json.loads(mongo('JSON.stringify({status:db.serverStatus(),stats:db.getSiblingDB("mongodb_loadtest_ycsb").usertable.stats()})'))
    data['cpu_stat'] = dict(line.split() for line in docker('exec', CONTAINER, 'cat', '/sys/fs/cgroup/cpu.stat').splitlines())
    (out / f'{name}.json').write_text(json.dumps(data, indent=2) + '\n')


def execute(out, label, mode, threads, seconds=None, recordcount=100000, target=None):
    args = ['./ycsb.sh', mode, '-s', '-P', 'workload.properties', '-threads', str(threads),
            '-p', f'recordcount={recordcount}', '-p', f'mongodb.url={URI}',
            '-p', 'hdrhistogram.fileoutput=true', '-p', f'hdrhistogram.output.path={out}/{label}-']
    if target:
        args += ['-target', str(target)]
    if seconds:
        args += ['-p', f'maxexecutiontime={seconds}']
    command = ['/usr/bin/time', '-v', '-o', str(out / f'{label}-generator.txt'), *args]
    (out / f'{label}-command.json').write_text(json.dumps(args, indent=2) + '\n')
    with (out / f'{label}.txt').open('w') as stdout, (out / f'{label}.stderr').open('w') as stderr:
        subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr, check=True, timeout=(seconds or 300) + 120)
    return validate(out / f'{label}.txt', ('INSERT',) if mode == 'load' else ('READ', 'UPDATE'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('results/experiment-1'))
    parser.add_argument('--seconds', type=int, default=30)
    args = parser.parse_args()
    if args.seconds < 10:
        parser.error('--seconds must be at least 10')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    count = int(mongo('db.getSiblingDB("mongodb_loadtest_ycsb").usertable.countDocuments({})'))
    if count:
        raise RuntimeError('Lab collection is nonempty. Use a new disposable Compose volume before a new experiment.')
    print('Loading 100,000 records...', flush=True)
    loaded = execute(out, 'load', 'load', 8)
    count = int(mongo('db.getSiblingDB("mongodb_loadtest_ycsb").usertable.countDocuments({})'))
    if count != 100000 or loaded['INSERT']['Return=OK'] != count:
        raise RuntimeError('Load count mismatch')
    plan = mongo('const d=db.getSiblingDB("mongodb_loadtest_ycsb"); const key=d.usertable.findOne()._id; JSON.stringify(d.usertable.find({_id:key}).limit(1).explain("executionStats"))')
    (out / 'explain.json').write_text(json.dumps(json.loads(plan), indent=2) + '\n')
    print('Warming the server cache for 20 seconds (separate JVM)...', flush=True)
    execute(out, 'warmup', 'run', 8, 20)
    rows = []
    for repeat, order in enumerate(((1, 8, 32, 64), (64, 32, 8, 1), (8, 64, 1, 32)), 1):
        for threads in order:
            label = f't{threads}-r{repeat}'
            print(f'{label}: starting {args.seconds}s run', flush=True)
            snapshot(out, label + '-before')
            started = datetime.now(timezone.utc).isoformat()
            m = execute(out, label, 'run', threads, args.seconds)
            snapshot(out, label + '-after')
            row = {'run': label, 'started_utc': started, 'threads': threads,
                   'throughput_ops_s': m['OVERALL']['Throughput(ops/sec)'],
                   'runtime_ms': m['OVERALL']['RunTime(ms)']}
            for op in ('READ', 'UPDATE'):
                row[op.lower() + '_operations'] = int(m[op]['Operations'])
                for p in (50, 95, 99):
                    row[f'{op.lower()}_p{p}_ms'] = m[op][f'{p}thPercentileLatency(us)'] / 1000
            rows.append(row)
            (out / 'runs.json').write_text(json.dumps(rows, indent=2) + '\n')
            print(f'{label}: {row["throughput_ops_s"]:.0f} ops/s, read p99 {row["read_p99_ms"]:.2f} ms', flush=True)
    with (out / 'runs.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f'Completed {len(rows)} validated measurement runs. Evidence: {out}', flush=True)


if __name__ == '__main__':
    main()
