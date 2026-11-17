"""Download the official OULAD archive; extract only expected CSV files."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
URL = 'https://archive.ics.uci.edu/static/public/349/open%2Buniversity%2Blearning%2Banalytics%2Bdataset.zip'
TABLES = ['courses', 'assessments', 'studentInfo', 'studentRegistration',
          'studentAssessment', 'studentVle', 'vle']

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    archive = RAW / 'anonymisedData.zip'
    if not archive.exists():
        partial = archive.with_suffix('.part')
        with requests.get(URL, stream=True, timeout=(30, 120)) as response:
            response.raise_for_status()
            with partial.open('wb') as out:
                for block in response.iter_content(1024 * 1024):
                    out.write(block)
        with zipfile.ZipFile(partial) as z:
            if z.testzip() is not None:
                raise ValueError('Archive integrity check failed')
        partial.replace(archive)
    with zipfile.ZipFile(archive) as z:
        for table in TABLES:
            name = table + '.csv'
            members = [m for m in z.namelist() if Path(m).name == name]
            if len(members) != 1:
                raise ValueError(f'Expected exactly one {name}')
            dest = RAW / name
            if not dest.exists():
                with z.open(members[0]) as src, dest.open('wb') as out:
                    shutil.copyfileobj(src, out)
    manifest = {'source': URL, 'sha256': {}}
    for path in [archive] + [RAW / (t + '.csv') for t in TABLES]:
        with path.open('rb') as stream:
            manifest['sha256'][path.name] = hashlib.file_digest(stream, 'sha256').hexdigest()
    expected_path = ROOT / 'docs' / 'data_manifest.json'
    if expected_path.exists():
        expected = json.loads(expected_path.read_text())['sha256']
        for name, digest in expected.items():
            if manifest['sha256'].get(name) != digest:
                raise ValueError(f'Data fingerprint differs from the original experiment: {name}')
    (RAW / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print('Downloaded and verified all seven OULAD tables.', flush=True)

if __name__ == '__main__':
    main()
