# ADR-001: Lokaler Flask-Monolith mit SQLite
**Status:** für diese Planung entschieden, Umsetzung offen · 22.10.2026

## Kontext
Lokale Browser-App, Einzelarbeit, enger Hackathon-Zeitrahmen; M8 verlangt Neustartpersistenz.

## Entscheidung
Python mit Flask/Jinja und CSS, SQLite-Datei, serverseitige Fachregeln und ein lokaler Prozess. tzdata für Europe/Berlin unter Windows explizit installieren.

## Alternativen
React/Next plus separate API verworfen: zusätzliche Build-/Integrationsschicht. Nur LocalStorage verworfen: browsergebundener Zustand und keine zentrale serverseitige Regelprüfung. PostgreSQL verworfen: zusätzlicher Dienst für die lokale Demo.

## Konsequenzen
Weniger Setup, persistenter gemeinsamer lokaler Stand. Formulare laden Seiten neu; kein zugesagter Firmenbetrieb. Konkrete Paketversionen und Drei-Befehle-Start sind beim Bau zu verifizieren.
