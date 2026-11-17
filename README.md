# Early Prediction of Student Withdrawal

**ES 678 · Aditya Gupta · 24110011**

Can information available after two, four and six weeks identify future course
withdrawal on a later offering when only the highest-risk 10% can be flagged?

On FFF 2014J, full-feature logistic regression identifies **19.8%, 22.5%, and 22.9%**
of future withdrawals at days 14, 28, and 42, compared with inactivity's **15.6%,
18.5%, and 16.3%**. Paired recall intervals favor logistic regression in this one
offering. Boosted-tree recall improvements are inconclusive at the 10% budget.
Most withdrawals are still missed; prediction does not establish outreach benefit.

## Read the submission

- [Research question, methods, results and limitations](docs/STUDY.md)
- [Executed analysis notebook and interactive budget explorer](notebooks/01_project_analysis.ipynb)
- [Exact protocol and feature dictionary](docs/protocol.md)
- [Complete evidence tables](results/EVIDENCE.md)
- [AI-use disclosure and citations](docs/AI_USE_AND_REFERENCES.md)

The paper is submitted separately and is intentionally excluded from this repository.

## Setup

Use Python 3.12. From the repository root in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

On macOS/Linux replace `.\.venv\Scripts\python` with `.venv/bin/python`.
The requirements pin the direct dependencies and principal numerical/notebook
packages used for the experiment; this is not a full transitive environment lock.

## Explore results without downloading data or retraining

The notebook contains saved outputs. For its live interaction:

```powershell
.\.venv\Scripts\python -m jupyterlab notebooks/01_project_analysis.ipynb
```

Run all cells. Select the cutoff, dynamic/common cohort, and an alert budget from
5–20%. The explorer uses included student-level predictions and exact split records,
with compact aggregate results as a fallback. Raw OULAD tables and model binaries
are not needed. Non-primary budgets
are retrospective sensitivity analyses, not another model-selection exercise.

## Reproduce from raw data

```powershell
.\.venv\Scripts\python scripts/reproduce.py
```

This downloads and checks OULAD, runs tests, rebuilds six snapshots, trains 24 model
variants, evaluates the later offering, audits 48 raw-record rows, rebuilds all
analyses, verifies the original results, and executes the notebook. Allow several
minutes plus download time, and about 600 MB of disk space excluding the environment.
Generated raw data, feature snapshots and model binaries stay local and are ignored
by Git. Exact split/fold records, test predictions and the sampled-row audit are
included for verification. The command overwrites generated outputs.

Keep `config.json` unchanged to reproduce the submission. Verification compares
66 metric rows with `reference_metrics.csv`, six snapshot and seven raw-table
SHA-256 hashes with `reference_manifest.json`, and prediction/split consistency.
Do not replace reference values to hide discrepancies.

For individual stages (use the environment's Python):

```powershell
python scripts/download_data.py
python -m unittest discover -s tests -v
python -m withdrawal.run --stage prepare
python -m withdrawal.run --stage train
python -m withdrawal.run --stage evaluate
python scripts/audit_rows.py
python -m withdrawal.submission
python -m withdrawal.submission --verify
python scripts/execute_notebook.py
```

## Data access and provenance

OULAD is provided by Kuzilek, Hlosta and Zdrahal through the
[Open University](https://research.stem.open.ac.uk/ouanalyse/dataset/) and
[UCI repository](https://doi.org/10.24432/C5KK69) under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The downloader uses the UCI archive (about 47 MB compressed, 464 MB of CSVs).
No account or credentials are required. [The data manifest](docs/data_manifest.json)
records the download source and checksums. For offline use, place the original
archive and seven CSVs in `data/raw/` before running the workflow.

Development is FFF 2013J, final test is FFF 2014J, and all 117 overlapping student
IDs are removed from development. Exact split/fold records are included in
`results/splits/` and deterministically regenerated under seed 678. Test predictions
are included in `results/predictions/day14.csv`, `day28.csv` and `day42.csv`; the
48-row raw-record audit is `results/predictions/row_audit.csv`. Snapshot fingerprints
verify identical membership and features. Missing values, eligibility rules and feature boundaries are documented
in the protocol. Split records, predictions, audits and derived error examples retain OULAD's pseudonymous identifiers
and dataset attribution; they are not real-world identities.

## Minimal repository structure

| Folder/file | Purpose |
|---|---|
| `withdrawal/` | Preparation, models, evaluation, reporting and notebook explorer |
| `scripts/` | Download, complete reproduction, row audit and notebook execution |
| `tests/` | Leakage, chronology, metrics, pipeline and interaction checks |
| `notebooks/` | One executed analysis notebook |
| `docs/` | Reasoning, protocol, data provenance, AI use and citations |
| `results/` | Aggregate tables, figures, exact splits/folds, predictions and row audit |
| `config.json` | Frozen experimental settings |
| `requirements.txt` | Pinned software dependencies |

The repository includes all model-comparison metrics, paired confidence intervals,
both-family ablations, cohort counts and combined CV results (`cv_results.csv`).
`reference_metrics.csv` is retained separately as the original reproducibility
benchmark. Exact splits/folds and student-level prediction/audit CSVs are included
as small reproducibility artifacts with pseudonymous OULAD IDs. Individual CV files,
raw datasets, feature snapshots, model binaries, logs, environments, caches, archives,
and the paper folder remain excluded.

## AI-use disclosure

AI tools, including OpenAI Codex, were used during this project. All reported
results were computed from the OULAD experiments. See [references](docs/AI_USE_AND_REFERENCES.md).
