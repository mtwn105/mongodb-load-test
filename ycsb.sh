#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mode="${1:-}"
case "$mode" in
  load) action=-load ;;
  run) action=-t ;;
  *) echo 'Usage: ./ycsb.sh load|run [YCSB arguments]' >&2; exit 2 ;;
esac
shift
if [[ ! -f .tools/lib/core-0.17.0.jar ]]; then
  echo 'Run ./setup.sh first.' >&2; exit 2
fi
exec java -Xms256m -Xmx1g -cp 'target/classes:.tools/lib/*' site.ycsb.Client "$action" -db site.ycsb.db.MongoDbClient "$@"
