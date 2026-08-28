# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/),
and versions follow [Semantic Versioning](https://semver.org/).

Each `## [x.y.z]` section is what the release workflow publishes as the
release notes for the matching `vx.y.z` tag, so keep the wording aimed at
whoever downloads the script.

## [2.0.0]

Rückkehr zur semantischen Versionierung und erster Release, der
automatisch entsteht.

Zwischen `v.1.2.0` (Juni 2023) und dieser Version liegen 29 Commits, die
zwischenzeitlich unter Datums-Versionen wie `01.02.2026-1130`
veröffentlicht wurden. Was in dieser Zeit dazugekommen ist:

- Konfiguration über `~/.config/tsr/config`, dazu Umgebungsvariablen und
  dokumentierte Kommandozeilenoptionen
- Korrigierte Qualitätserkennung, robustere Fehlerauswertung und
  aufgeräumtes Thread-Handling
- Nachbearbeitung: `ffmpeg -y`, echtes AAC-Remux statt bloßer
  Umbenennung, sauberes Aufräumen der Zwischendateien
- README dokumentiert Optionen, Konfiguration und die Nachbearbeitung

Der Sprung auf 2.0.0 markiert den Bruch im Versionsschema, nicht eine
inkompatible Änderung am Skript selbst — die letzten Tags waren Daten,
und `v1.x` ist auf dem GitHub-Spiegel bereits vergeben.

Ab hier entsteht zu jedem Tag `v*` automatisch ein Release mit `tsr.py`
als Anhang; der Workflow prüft dabei, dass Tag und Versionszeile in
`tsr.py` übereinstimmen.
