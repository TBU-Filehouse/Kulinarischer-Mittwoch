"""G5 commit scanner: no secrets, real names, personal paths or local data in the repository."""
from pathlib import Path
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import scan_commit  # noqa: E402

# Built at runtime so this test file itself never contains a scannable secret.
GITHUB_TOKEN='ghp_'+'a1B2'*9
AWS_KEY='AKIA'+'ABCDEFGHIJKLMNOP'
PRIVATE_KEY='-----BEGIN '+'RSA PRIVATE KEY-----'
USER_PATH='C:'+'\\Users\\maxmustermann\\projekt'


def scan(tmp_path,files,denylist=None):
    for name,content in files.items():
        path=tmp_path/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(content,encoding='utf-8')
    return scan_commit.scan(tmp_path,list(files),denylist or [])


def rules(findings):
    return {finding.rule for finding in findings}


@pytest.mark.parametrize('content,rule',[
    (f'token = "{GITHUB_TOKEN}"','secret'),
    (f'key={AWS_KEY}','secret'),
    (PRIVATE_KEY,'secret'),
    ('KUMI_SECRET'+'_KEY=abcdef123456','secret'),
    ('pass'+'word = "hunter2hunter2"','secret'),
    (f'log path {USER_PATH}','personal-path'),
    ('siehe /ho'+'me/maxmustermann/x','personal-path'),
    ('Kontakt: erika.beispiel'+'@firma.de','email'),
])
def test_dangerous_content_is_reported_with_location(tmp_path,content,rule):
    findings=scan(tmp_path,{'docs/a.md':'ok\n'+content+'\n'})
    assert rule in rules(findings)
    assert any(f.path=='docs/a.md' and f.line==2 for f in findings)


@pytest.mark.parametrize('name',['data/app.db','x.sqlite3','.env','.harness/result.json',
                                 'test-results/e2e.xml','.Codex/kontext/ARBEITSSTAND.md'])
def test_forbidden_files_are_reported(tmp_path,name):
    assert 'forbidden-file' in rules(scan(tmp_path,{name:'x'}))


def test_denylisted_real_name_is_reported_case_insensitive(tmp_path):
    findings=scan(tmp_path,{'tests/t.py':"name='erika MUSTERFRAU'"},denylist=['Erika Musterfrau'])
    assert rules(findings)=={'real-name'}


@pytest.mark.parametrize('content',[
    "Co-Authored-By: Claude <noreply@anthropic.com>",
    'Fiktive Namen: Anna Müller, Ben Muster, Cora Demo',
    'KUMI_SECRET_KEY kann gesetzt werden',
    'password_hint = form.get("password")',
    "base_url='http://foreign.invalid'",
    'mail an jemand@example.com',
    '%TEMP%\\kumi-loop-guard und C:\\Temp\\abnahme.db',
    '.env.example',
])
def test_harmless_project_content_passes(tmp_path,content):
    assert scan(tmp_path,{'README.md':content},denylist=['Erika Musterfrau'])==[]


def test_env_example_file_is_allowed(tmp_path):
    assert scan(tmp_path,{'.env.example':'KUMI_PORT=5000'})==[]


def test_binary_files_are_skipped_not_crashing(tmp_path):
    path=tmp_path/'app/static/logo.png'
    path.parent.mkdir(parents=True)
    path.write_bytes(b'\x89PNG\x00\xff\xfe'+GITHUB_TOKEN.encode())
    assert scan_commit.scan(tmp_path,['app/static/logo.png'],[])==[]


def test_denylist_file_missing_is_reported_as_warning_not_silent(tmp_path):
    names,warning=scan_commit.load_denylist(tmp_path/'missing.txt')
    assert names==[] and 'Sperrliste' in warning


def test_denylist_file_ignores_comments_and_blank_lines(tmp_path):
    path=tmp_path/'names.txt'
    path.write_text('# echte Namen, nie ins Repo\n\nErika Musterfrau\n  Max Mustermann  \n',encoding='utf-8')
    assert scan_commit.load_denylist(path)==(['Erika Musterfrau','Max Mustermann'],None)


def test_cli_on_this_repository_is_clean():
    process=subprocess.run([sys.executable,str(ROOT/'scripts'/'scan_commit.py')],cwd=ROOT,
                           capture_output=True,text=True,encoding='utf-8',timeout=60)
    assert process.returncode==0, process.stdout+process.stderr


def test_cli_fails_on_finding_without_echoing_the_secret(tmp_path):
    subprocess.run(['git','init','-q'],cwd=tmp_path,check=True)
    (tmp_path/'leak.txt').write_text(f'token={GITHUB_TOKEN}\n',encoding='utf-8')
    process=subprocess.run([sys.executable,str(ROOT/'scripts'/'scan_commit.py'),'--root',str(tmp_path)],
                           capture_output=True,text=True,encoding='utf-8',timeout=60)
    assert process.returncode==1
    assert 'leak.txt:1' in process.stdout and 'secret' in process.stdout
    assert GITHUB_TOKEN not in process.stdout+process.stderr
