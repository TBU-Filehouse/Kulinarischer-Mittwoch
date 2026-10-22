"""Loop guard for agent sessions: blocks non-progress repetition and foreground hangs."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'/'hooks'))
import loop_guard  # noqa: E402


def call(state,tool='Bash',session='s1',**tool_input):
    event={'session_id':session,'tool_name':tool,'tool_input':tool_input or {'command':'ls'}}
    return loop_guard.evaluate(event,state)


def test_identical_call_blocked_on_third_consecutive_repeat(tmp_path):
    assert call(tmp_path,command='pytest -q')[0]==0
    assert call(tmp_path,command='pytest -q')[0]==0
    code,message=call(tmp_path,command='pytest -q')
    assert code==2 and 'Schleife' in message


def test_repeats_with_progress_in_between_are_allowed(tmp_path):
    for round_number in range(5):
        assert call(tmp_path,tool='Edit',file_path='a.py',old_string=str(round_number),new_string=str(round_number+1))[0]==0
        assert call(tmp_path,command='pytest -q')[0]==0


def test_ping_pong_without_progress_is_blocked(tmp_path):
    outcomes=[call(tmp_path,command=command)[0] for command in ['a','b','a','b','a','b']]
    assert outcomes[:5]==[0,0,0,0,0] and outcomes[5]==2


def test_description_change_does_not_hide_a_repeat(tmp_path):
    call(tmp_path,command='pytest',description='eins')
    call(tmp_path,command='pytest',description='zwei')
    assert call(tmp_path,command='pytest',description='drei')[0]==2


def test_sessions_are_counted_separately(tmp_path):
    call(tmp_path,session='a',command='x')
    call(tmp_path,session='a',command='x')
    assert call(tmp_path,session='b',command='x')[0]==0


def test_block_resets_so_a_changed_approach_continues(tmp_path):
    for _ in range(3):
        call(tmp_path,command='x')
    assert call(tmp_path,command='anderer Ansatz')[0]==0
    assert call(tmp_path,command='x')[0]==0


@pytest.mark.parametrize('command',[
    '.venv/Scripts/python.exe -m app',
    'python -m flask run',
    'tail -f server.log',
    'Get-Content server.log -Wait',
    'ping -t 127.0.0.1',
    'python -m http.server 8000',
    'while true; do echo x; done',
    'while ($true) { Start-Sleep 1 }',
    'cat <<EOF\n`python -m app`\nEOF',  # Unquoted heredoc: the shell would run the backticks.
    "cat > doc.md <<'EOF'\ntext\nEOF\npython -m app",
])
def test_foreground_commands_that_never_end_are_blocked(tmp_path,command):
    code,message=call(tmp_path,command=command)
    assert code==2 and 'Hintergrund' in message


@pytest.mark.parametrize('command',[
    '.venv/Scripts/python.exe -m pytest -q tests',
    '.venv/Scripts/python.exe scripts/check.py',
    'git log --oneline -3',
    'grep -n "tail -f" README.md',
    'timeout 3 tail -f server.log',
    'timeout 10 python -m app',
    "cat > doc.md <<'EOF'\nStart mit `python -m app` und tail -f log\nEOF\necho ok",
    'cat > doc.md <<"END"\nwhile true wird beschrieben\nEND',
])
def test_normal_commands_pass(tmp_path,command):
    assert call(tmp_path,command=command)[0]==0


def test_long_running_command_in_background_is_allowed(tmp_path):
    assert call(tmp_path,command='python -m app',run_in_background=True)[0]==0


def test_kill_switch_disables_guard(tmp_path,monkeypatch):
    monkeypatch.setenv('KUMI_LOOP_GUARD','off')
    for _ in range(4):
        assert call(tmp_path,command='python -m app')[0]==0


def test_corrupt_state_or_input_fails_open(tmp_path):
    (tmp_path/'s1.json').write_text('{kaputt',encoding='utf-8')
    assert call(tmp_path,command='ls')[0]==0
    assert loop_guard.evaluate({'tool_name':None},tmp_path)[0]==0


def test_cli_exit_code_and_stderr(tmp_path):
    env={'KUMI_LOOP_GUARD_DIR':str(tmp_path),'SYSTEMROOT':os.environ.get('SYSTEMROOT','')}
    event=json.dumps({'session_id':'cli','tool_name':'Bash','tool_input':{'command':'tail -f x.log'}})
    process=subprocess.run([sys.executable,str(ROOT/'scripts'/'hooks'/'loop_guard.py')],input=event,
                           capture_output=True,text=True,encoding='utf-8',env=env,timeout=30)
    assert process.returncode==2 and 'Hintergrund' in process.stderr
    assert not any(ROOT.glob('*.json'))  # State never lands in the repository root.
