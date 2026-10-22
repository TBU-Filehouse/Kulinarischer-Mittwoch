"""Run local QS, bind results to the source, keep product acceptance separate."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def source_hash():
    files = set()
    for directory in ('app', 'tests', 'scripts', 'docs'):
        base = ROOT / directory
        if base.exists():
            files.update(p for p in base.rglob('*') if p.is_file()
                         and '__pycache__' not in p.parts
                         and p.suffix in {'.py', '.sql', '.html', '.css', '.md', '.json'})
    files.update(ROOT.glob('*.md'))
    files.update(ROOT.glob('requirements*.txt'))
    files.add(ROOT / '.gitignore')
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.relative_to(ROOT).as_posix().encode('utf-8') + b'\0')
        digest.update(path.read_bytes() + b'\0')
    return digest.hexdigest()


def run_step(name, args):
    start = time.monotonic()
    try:
        child_env = os.environ.copy()
        child_env['PYTHONIOENCODING'] = 'utf-8'
        process = subprocess.run(args, cwd=ROOT, env=child_env, capture_output=True, text=True,
                                 encoding='utf-8', errors='replace', timeout=120)
        code = process.returncode
        output = process.stdout + process.stderr
    except OSError as exc:
        code, output = 127, f'Pruefschritt konnte nicht gestartet werden: {exc}'
    except subprocess.TimeoutExpired:
        code, output = 124, 'Zeitlimit ueberschritten (120 Sekunden).'
    return {'name': name, 'exit_code': code,
            'dauer_sekunden': round(time.monotonic() - start, 3), 'ausgabe': output}


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    (ROOT / 'test-results').mkdir(exist_ok=True)
    before = source_hash()
    steps = [run_step('dependencies', [sys.executable, '-m', 'pip', 'check']),
             run_step('logic_http', [sys.executable, '-m', 'pytest', '-q', 'tests',
                       '--ignore=tests/e2e', '--tb=short', '--junitxml=test-results/logic-http.xml']),
             run_step('browser_e2e', [sys.executable, '-m', 'pytest', '-q', 'tests/e2e',
                       '--browser', 'chromium', '--tracing', 'retain-on-failure',
                       '--screenshot', 'only-on-failure', '--output', 'test-results/e2e',
                       '--tb=short', '--junitxml=test-results/e2e.xml'])]
    after = source_hash()
    success = all(step['exit_code'] == 0 for step in steps) and before == after
    report = {
        'zeitpunkt_utc': datetime.now(timezone.utc).isoformat(),
        'umfang': 'AP1-AP4 transaktionale Koch-/Gerichtformulare und Chromium-E2E; keine Gesamtproduktabnahme',
        'quellstand_sha256': before, 'quellstand_sha256_nachher': after,
        'quellstand_unveraendert': before == after,
        'technisch_erfolgreich': success, 'produkt_abgenommen': False, 'schritte': steps,
    }
    directory = ROOT / '.harness'
    directory.mkdir(exist_ok=True)
    (directory / 'result.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    for step in steps:
        print(f"{step['name']}: Exit {step['exit_code']}")
        print(step['ausgabe'].strip())
    print('AP1-AP4 technisch erfolgreich: ' + str(success))
    print('Produktabnahme NICHT BELEGT; technischer Erfolg ist keine Abnahme.')
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
