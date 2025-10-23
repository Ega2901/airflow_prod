#!/usr/bin/env bash
###############################################################################
# cleanup_removed_dags.sh
# Удаляет из БД Airflow DAG-и, чьих файлов больше нет в dags_folder.
# (так они пропадают из UI без «серых»/broken записей)
###############################################################################
set -euo pipefail

# ▸ Даем scheduler-у время перечитать DagBag после копирования новых файлов.
sleep 25                # при желании уменьшите/увеличьте

###############################################################################
# 1. Airflow ≥ 2.9 : команда «dags sync --delete» уже все делает сама
###############################################################################
if airflow dags sync --delete --help &>/dev/null; then
  echo "[cleanup] Airflow ≥ 2.9 — используем dags sync --delete"
  airflow dags sync --delete
  exit 0
fi

###############################################################################
# 2. Fallback для старых версий (≤ 2.8)
###############################################################################
echo "[cleanup] Старый Airflow — удаляем DAG-и вручную"

# Получаем JSON: [{"dag_id": "...", "fileloc": "...", ...}, ...]
LIST=$(airflow dags list --output json 2>/dev/null || echo "[]")
[ -z "$LIST" ] && LIST="[]"

python - "$LIST" <<'PY'
import json, pathlib, subprocess, sys

dags = json.loads(sys.argv[1] or "[]")
removed = 0

for entry in dags:
    fileloc = pathlib.Path(entry.get("fileloc", ""))
    dag_id  = entry["dag_id"]
    if not fileloc.exists():
        print(f"[cleanup] Deleting orphaned DAG {dag_id}")
        subprocess.run(["airflow", "dags", "delete", dag_id, "--yes"],
                       check=True)
        removed += 1

print(f"[cleanup] Done. Removed {removed} DAG(s)." )
PY
