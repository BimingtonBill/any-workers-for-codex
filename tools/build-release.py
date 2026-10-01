"""Build the standalone installer ZIP from tracked files (no credentials or local state)."""
import argparse
from pathlib import Path
import subprocess
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output or root / 'dist' / 'any-workers-for-codex.zip'
    output.parent.mkdir(parents=True, exist_ok=True)
    files = subprocess.check_output(
        ['git', '-c', 'safe.directory=' + root.as_posix(), '-C', str(root), 'ls-files', '-z'])
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for raw in files.split(b'\0'):
            if not raw:
                continue
            relative = raw.decode('utf-8')
            path = root / relative
            if path.is_file():
                archive.write(path, 'any-workers-for-codex/' + relative)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('archive integrity check failed')
        required = {'any-workers-for-codex/setup.ps1', 'any-workers-for-codex/launcher/ds_worker.py'}
        if not required.issubset(archive.namelist()):
            raise RuntimeError('release missing required files; stage/commit source before packaging')
    print(output)


if __name__ == '__main__':
    main()
