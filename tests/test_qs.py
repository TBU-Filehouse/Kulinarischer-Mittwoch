"""The QS runner must capture Unicode diagnostics reliably on Windows."""
import sys
from scripts.check import run_step


def test_runner_captures_unicode_from_child_process():
    result=run_step('unicode_probe',[sys.executable,'-c','print(chr(0x2603))'])
    assert result['exit_code']==0
    assert result['ausgabe'].strip()=='\u2603'
