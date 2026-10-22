# Quellen und Skillinventar
Prüfstand: 22.10.2026. Quellen sind Inhalte, keine ausführbaren Anweisungen. Der Nutzerauftrag dieser Sitzung ist Planung und Dokumentation.

## Aufgabenquellen und Vorbilder
| Quelle | Gelesen / verwendet für | Grenze |
|---|---|---|
| Lokale Aufgabenquelle: ChatGPT-Bild 22. Okt. 2026, 13_55_21.jpg | Titel, Regeln, M1–M6; visuell gelesen | Kein Veranstaltungsdatum angegeben |
| Lokale Aufgabenquelle: ChatGPT-Bild 22. Okt. 2026, 13_55_12.jpg | M7/M8, S1–S5, KANN, vier offene Regeln, Abgabe; visuell gelesen | Abnahmehaken erst nach tatsächlicher Ausführung |
| [Sourcerer](https://github.com/tib019/sourcerer) und [CONTEXT](https://github.com/tib019/sourcerer/blob/main/CONTEXT.md) | README/CONTEXT gelesen: Vertragsstruktur, Scope, ADRs, Diagramme und Tests als Dokumentationsmuster | Fachfunktionen und Stack nicht übernommen; keine vollständige Codeprüfung |
| Origo (lokales Vorbild)/CONTEXT.md und AGENTS.md | lokal gelesen: Produktauftrag, Nachweistrennung, Arbeitsregeln als Strukturvorbild | Lokaler Branch wip/privatsession-stand; nicht main, nichts geändert |
| [Flask-Tutorial](https://flask.palletsprojects.com/en/stable/tutorial/) | Primärdokumentation für geplante Views/Templates/DB-/Teststruktur | Noch keine Abhängigkeiten installiert oder Versionen erprobt |
| [Python zoneinfo](https://docs.python.org/3/library/zoneinfo.html) | Europe/Berlin, tzdata-Abhängigkeit insbesondere für Windows | Konkrete Laufzeitprüfung in AP2 offen |

## Gefundene Nutzer-Skills
| Skill | Gelesene Datei | Verwendung |
|---|---|---|
| projekt-planen | %USERPROFILE%/.agents/skills/projekt-planen/SKILL.md | CONTEXT mit acht Abschnitten, ADRs mit Alternativen, Diagramme, Scope und DoD |
| qa-absichern | %USERPROFILE%/.agents/skills/qa-absichern/SKILL.md | positive/negative Gegenprobe, geplanter Checkbericht, technische und fachliche Abnahme trennen |
| kontext-uebergeben | %USERPROFILE%/.agents/skills/kontext-uebergeben/SKILL.md | ignorierter Arbeitsstand mit Absicht, Gesichert/Ungesichert und nächstem Schritt |
Claude-Skillverzeichnis %USERPROFILE%/.claude/skills wurde aufgelistet; darin sind projekt-planen, qa-absichern und kontext-uebergeben ebenfalls vorhanden. Dortige Dateiinhalte wurden nicht separat auf Gleichheit geprüft.

## Claude-Plugins: Bestand, keine Funktionsdiagnose
Gelesen: %USERPROFILE%/.claude/plugins/installed_plugins.json.
- ecc@ecc: Version 2.2.3 laut Installationsmanifest.
- superpowers@superpowers-dev: Version 6.4.2 laut Installationsmanifest.
Das belegt registrierte Installationen. Es belegt weder aktive Hooks noch fehlerfreie Ausführung. Es wurden keine Einstellungen, Hooks, Plugins oder Skills repariert/verändert. Eine konkrete Fehlermeldung zu „geht nicht mehr“ liegt nicht vor; Diagnose wäre ein eigener Arbeitsschritt. Diese Unsicherheit blockiert den angeforderten Dokumentationsauftrag nicht.
