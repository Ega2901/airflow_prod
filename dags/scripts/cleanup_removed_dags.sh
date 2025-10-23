#!/usr/bin/env bash
set -euo pipefail

OLD=$(airflow dags list --output json | \
      python -c 'import sys,json; print("\n".join(sorted(d["dag_id"] for d in json.load(sys.stdin))))')

sleep 10

NEW=$(airflow dags list --output json | \
      python -c 'import sys,json; print("\n".join(sorted(d["dag_id"] for d in json.load(sys.stdin))))')

for dag in $OLD; do
  grep -qx "$dag" <<< "$NEW" || {
    echo "Deleting orphaned DAG $dag"
    airflow dags delete "$dag" --yes
  }
done
