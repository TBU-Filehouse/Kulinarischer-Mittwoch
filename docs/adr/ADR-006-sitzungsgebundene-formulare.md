# ADR-006: Sitzungstoken schützen lokale Schreibformulare
**Status:** umgesetzt und technisch geprüft · 22.10.2026

## Kontext
AP4 führt erstmals gemeinsame Daten ändernde Formulare ein. Kein Login ist verlangt. Fremde Webseiten sollen den lokalen Browser nicht zu ungewollten Änderungen veranlassen können; Formularschutz und Loginumfang bleiben getrennt.

## Entscheidung
Jeder POST prüft einen zufälligen, an die signierte Flask-Session gebundenen CSRF-Token mittels konstantzeitlichem Vergleich. Vorhandener Origin muss passen. SECRET_KEY zufällig pro App oder aus KUMI_SECRET_KEY, niemals fest im Code. HttpOnly/SameSite Lax für lokales HTTP, TrustedHosts für Loopback. Bodylimit 16 KiB; gültige Maximalfelder inklusive Unicode bleiben möglich.

## Alternativen
Nur ausgeblendete Schaltflächen verworfen: direkte POSTs umgehen die UI. Alleinige Originprüfung verworfen: Der Header fehlt bei manchen zulässigen Anfragen. Login verworfen: nicht verlangt. Keine zusätzliche Formularbibliothek für drei begrenzte Routen; Schutz zentral in csrf.py.

## Konsequenzen
Alte Formulare können nach einem Neustart ohne festen Umgebungsschlüssel ungültig sein und müssen neu geladen werden. Daten bleiben erhalten. Lokale Nutzer können weiterhin gemeinsame Einträge bearbeiten; CSRF ist kein Identitätsnachweis. AP5 muss denselben Schutz verwenden. Tests deaktivieren ihn nicht.

Primärquelle: [Flask-Sicherheitsaspekte](https://flask.palletsprojects.com/en/stable/web-security/).
