# ADR-004: Namensvetter verwenden einen sichtbaren Zusatz
**Status:** für diese Planung entschieden, Umsetzung offen · 22.10.2026

## Kontext
Kein Login verlangt; M5 verbietet denselben normalisierten Namen am selben Mittwoch. Zwei reale Personen können gleich heißen.

## Entscheidung
Name wird trim+casefold normalisiert. Bei Namenskonflikt verlangt die UI einen unterscheidbaren Anzeigenamen wie Thomas A und Thomas B. Kein interner Identitätsbeweis.

## Alternativen
Gleiche Namen einfach zulassen verworfen: verletzt M5. E-Mail/Personalnummer erzwingen verworfen: zusätzliche personenbezogene Pflichtfelder. Login verworfen: ausdrücklich nicht verlangt.

## Konsequenzen
Einfache Lösung passend zur Demo; Nutzer verantworten unterscheidbare Eingabe. Schreibvarianten können Identität nicht sicher erkennen; keine Authentifizierung suggerieren.
