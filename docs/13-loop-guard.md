# Loop-Guard für Agentensitzungen
Stand 22.10.2026 · **Als PreToolUse-Hook aktiv** in `.claude/settings.json` (Nutzerfreigabe als ausdrückliche G9-Ausnahme am 22.10.2026).

## Zweck
Auf Nutzerwunsch: Schleifen ohne Fortschritt und Befehle mit Hänger-Potenzial mechanisch stoppen, statt sich auf Vorsätze des Modells zu verlassen.

## Verhalten (scripts/hooks/loop_guard.py, PreToolUse)
- **Wiederholung:** derselbe Werkzeugaufruf dreimal direkt hintereinander, oder Pingpong A-B-A-B-A-B → Aufruf wird blockiert (Exit 2) mit Hinweis, Ursache zu prüfen oder die Person zu fragen. Die Beschreibung eines Befehls zählt nicht mit, damit Umformulieren keine Wiederholung versteckt. Danach beginnt die Zählung neu.
- **Hänger:** Vordergrund-Befehle, die nie enden (App-Server `-m app`, `flask run`, `http.server`, `tail -f`, `Get-Content -Wait`, `ping -t`, `while true`) werden blockiert, außer mit `run_in_background`. Text in Anführungszeichen wird ignoriert (`grep "tail -f"` bleibt erlaubt). Mit `timeout N` begrenzte Einzelbefehle bleiben erlaubt; hängt dahinter ein weiterer Befehl (`;`, `&`, `|`), greift die Ausnahme nicht.
- **Stopp:** Umgebungsvariable `KUMI_LOOP_GUARD=off` schaltet den Guard ab. Interne Fehler lassen den Aufruf durch (fail-open), damit ein defekter Guard die Arbeit nicht blockiert.
- Zustand je Sitzung im Temp-Verzeichnis (`%TEMP%\kumi-loop-guard`), nie im Repository. Meldungen als UTF-8 (Windows-Befund, mit Test abgesichert).

## Bestehender Hängerschutz im Projekt
scripts/check.py begrenzt jede Prüfstufe auf 120 s (Exit 124). E2E-Server haben 15 s Startfrist, Thread-Tests Barrieren mit Timeout.

## Nachweis
28 Fälle in tests/test_loop_guard.py, zuerst rot (Modul fehlte), dann grün; ein Fall fand die ANSI-Kodierung der Fehlermeldung unter Windows.

## Aktivierung
Eintrag in `.claude/settings.json` des Projekts (Shell bash, Zeitlimit 10 s):

    {"hooks": {"PreToolUse": [{"matcher": "*", "hooks": [{"type": "command",
      "command": "\"$CLAUDE_PROJECT_DIR/.venv/Scripts/python.exe\" \"$CLAUDE_PROJECT_DIR/scripts/hooks/loop_guard.py\"",
      "timeout": 10}]}]}}

## Live-Nachweis 22.10.2026
Befehl vor dem Eintrag mit nachgebauter Hook-Eingabe geprüft (harmlos Exit 0, Hänger Exit 2). Nach dem Eintrag in dieser Sitzung: `timeout 3 tail -f /dev/null` wurde zunächst blockiert. Das war ein Fehlalarm, denn der Befehl endet von selbst; mit rotem Test zuerst korrigiert. Danach lief `timeout 2 tail -f /dev/null` durch und endete mit Exit 124, während ungebremste Varianten weiter blockiert werden.
Abschalten: Umgebungsvariable `KUMI_LOOP_GUARD=off` oder den Eintrag aus `.claude/settings.json` entfernen.
Zweiter Live-Befund (AP7): Ein Heredoc mit gequotetem Begrenzer, dessen Text `python -m app` erwähnte, wurde blockiert. Solche Heredocs werden nie ausgeführt und sind seither ausgenommen; ungequotete Heredocs bleiben geprüft. Roter Test zuerst, danach lief derselbe Befehl live durch.
