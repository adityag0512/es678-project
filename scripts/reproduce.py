"""One command to reproduce and verify the submitted experiment."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
env = os.environ.copy()
env.setdefault('LOKY_MAX_CPU_COUNT', '2')
commands = [
    ['scripts/download_data.py'],
    ['-m', 'unittest', 'discover', '-s', 'tests', '-v'],
    ['-m', 'withdrawal.run'],
    ['scripts/audit_rows.py'],
    ['-m', 'withdrawal.submission'],
    ['-m', 'withdrawal.submission', '--verify'],
    ['scripts/execute_notebook.py'],
]
for command in commands:
    print('\nRunning: ' + ' '.join([sys.executable] + command), flush=True)
    subprocess.run([sys.executable] + command, cwd=ROOT, env=env, check=True)
print('\nReproduction complete. Open notebooks/01_project_analysis.ipynb.')
