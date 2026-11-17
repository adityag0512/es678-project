"""Execute and save the analysis notebook after the experiment has completed."""
from pathlib import Path
import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
path = root / 'notebooks' / '01_project_analysis.ipynb'
notebook = nbformat.read(path, as_version=4)
NotebookClient(notebook, timeout=180, kernel_name='python3',
               resources={'metadata': {'path': str(root)}}).execute()
nbformat.validate(notebook)
nbformat.write(notebook, path)
print('Executed and saved all analysis notebook cells.')
