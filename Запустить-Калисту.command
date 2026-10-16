#!/bin/zsh
set -eu
cd "$(dirname "$0")"
task_python="../work/venv/bin/python"
if [[ ! -x "$task_python" ]]; then task_python=".venv/bin/python"; fi
if [[ ! -x "$task_python" ]]; then
  echo "Сначала установи зависимости по инструкции Игра.md."
  exit 1
fi
"$task_python" kalista_setup.py
exec "$task_python" -m streamlit run kalista_app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true --server.showEmailPrompt false --browser.gatherUsageStats false
