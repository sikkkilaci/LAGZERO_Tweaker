# LAG|ZERØ Tweaker – Installationsanleitung

## Für Endnutzer (EXE-Download)

### Was ist LAG|ZERØ?
LAG|ZERØ ist ein Gaming-Performance-Optimizer für Windows 10/11. Die Anwendung optimiert Registry-Einstellungen, Energiesparpläne und Treiberkonfigurationen für maximale Gaming-Performance bei minimaler Latenz.

### Systemanforderungen
- **OS:** Windows 10 (Build 19041+) oder Windows 11
- **RAM:** 512 MB (minimal)
- **Disk:** ~200 MB (für die EXE + temporäre Tools)
- **Admin-Rechte:** Ja, erforderlich (wird beim Start angefordert)
- **GPU:** NVIDIA (optional, für DLSS-Profile), Intel oder AMD (Basis-Optimierungen funktionieren überall)

### Installation

#### Option 1: Fertige EXE herunterladen
1. Laden Sie `LAGZERO_Tweaker.exe` herunter (z.B. von GitHub Releases).
2. Speichern Sie die Datei in einem beliebigen Verzeichnis (z.B. `C:\Programme\LAG|ZERØ\`).
3. Doppelklick auf `LAGZERO_Tweaker.exe`.
4. Bestätigen Sie die UAC-Abfrage (Administrator-Berechtigung erforderlich).
5. Die Anwendung startet. Beim ersten Start werden optionale Tools (HidUSBF, GamepadLA) bei Bedarf heruntergeladen.

#### Option 2: EXE selbst bauen (für Entwickler)
Wenn Sie das Projekt von GitHub klont haben:

1. Installieren Sie Python 3.8+:
   - https://www.python.org/downloads/
   - **WICHTIG:** Aktivieren Sie „Add Python to PATH" während der Installation!

2. Öffnen Sie die `BUILD_EXE.bat` im Projektverzeichnis (Doppelklick oder CMD).

3. Das Skript wird:
   - Abhängigkeiten installieren (psutil, gamepadla-plus, pyinstaller)
   - Die EXE kompilieren (~1 Minute)
   - `LAGZERO_Tweaker.exe` im aktuellen Verzeichnis ablegen

4. Starten Sie die EXE — Fertig!

### Erste Schritte

#### Dashboard
- Zeigt Live-Daten: CPU-Temperatur, GPU-Auslastung, RAM-Nutzung
- Wird alle ~9 Sekunden aktualisiert (bewusst niedrig, um Performance nicht zu belasten)

#### Optimize
- Wählen Sie gewünschte Optimierungen (Checkboxen):
  - **Game Mode aktivieren:** DirectX 12 Games bekommen Priorität
  - **Hardware-accelerated GPU Scheduling:** Bessere GPU-Auslastung
  - **Ultimate Performance Energieschema:** CPU-Vollleistung (höherer Stromverbrauch)
  - **Game DVR deaktivieren:** Weniger Background-Overhead
  - **NVIDIA max. Leistung:** Treiber bevorzugt Spielleistung über Energiesparen
  
- Klicken Sie **„OPTIMIZE PC"** → Bestätigungsdialog → Backup wird angelegt → System wird angepasst.

- **RESTORE:** Setzt alle Änderungen auf den Ausgangszustand zurück (nur der erste Backup-Punkt).

#### Windows / GPU / CPU & Power / Network / Services / Games
- **Einzelne Kategorien:** Feinere Kontrolle über spezifische Einstellungen.
- **Placeholder-Bereiche:** Network, Services, Games zeigen noch keine realen Schalter (kommende Versionen).

#### Tools
- **NVIDIA DLSS:** Wendet die neueste DLSS-Version als globales Profil an.
- **NVIDIA Profile Inspector:** Lädt das offizielle Tool herunter → Ermöglicht manuelle Profil-Bearbeitung.
- **HidUSBF:** Kernel-Filtertreiber für USB/HID-Geräte-Polling-Überclocking (Controller, Maus).
  - Lädt das offizielle HidUSBF-Projekt herunter.
  - Öffnet die Setup.exe → Nutzer wählt das Gerät und die Rate selbst.
- **GamepadLA:** Misst Controller-Polling-Rate und synthetische Latenz.
  - ~5 Sekunden Messdauer, während Sie den rechten Stick drehen.
  - Ergebnis wird direkt in LAG|ZERØ angezeigt.

### Häufig gestellte Fragen

**F: Kann ich mehrere Backups haben?**
Nein (noch nicht). Es gibt einen einzigen Backup-Slot. Beim nächsten Optimize wird der alte Stand verwendet (nicht überschrieben). Für Experimente: Notieren Sie die Einstellungen oder verwenden Sie Windows Systemwiederherstellung.

**F: Ist LAG|ZERØ sicher?**
Ja. Alle Registry-Änderungen sind dokumentierte Windows-Features (kein Registry-Hacking). Ein Backup wird automatisch angelegt. Zusätzlich wird versucht, einen Windows-Wiederherstellungspunkt zu erstellen. Sie können jederzeit mit „RESTORE" zurückgehen.

**F: Werde ich von Antivirus-Software blockiert?**
Möglich (falsch-positive Detektionen). LAG|ZERØ ist quelloffen — wenn Sie misstrauen, können Sie den Code selbst prüfen oder die EXE von Virenscannern whitelist'en (z.B. unter Windows Defender → Ausschlüsse).

**F: Funktioniert das auch ohne NVIDIA GPU?**
Ja. Windows-Optimierungen, CPU-Power, Network-Settings funktionieren überall. DLSS-Features sind NVIDIA-spezifisch und werden automatisch deaktiviert, wenn das Tool nicht verfügbar ist.

**F: Kann ich LAG|ZERØ auf mehreren PCs verwenden?**
Ja. Die EXE hat keine Lizenz-Keys, Aktivierungen oder Online-Checks — einfach kopieren und starten.

**F: Was passiert, wenn ich die Anwendung während einer Optimierung schließe?**
Registry-Änderungen sind bereits geschrieben (nicht rückgängig). Das Backup ist gespeichert → Sie können mit „RESTORE" alles zurücksetzen.

**F: Kann ich die EXE ohne Admin-Rechte starten?**
Die Anwendung funktioniert nur mit Admin-Rechten (Systemänderungen). Sie können die EXE starten, aber die Optimierungen schlagen fehl. Die UAC-Abfrage ist normal.

### Troubleshooting

**Problem: „Python not found" (beim selbst bauen)**
- Laden Sie Python von python.org herunter und installieren Sie es.
- **WICHTIG:** Aktivieren Sie „Add Python to PATH" während der Installation.
- Starten Sie den PC neu und versuchen Sie es erneut.

**Problem: EXE startet, aber Fehler beim Optimize**
- Admin-Rechte nötig (UAC bestätigt?).
- Windows 10/11 erforderlich.
- Versuchen Sie Windows Update.

**Problem: GamepadLA-Test wird nicht erkannt**
- Controller angeschlossen? (USB oder wireless Receiver).
- Während des Tests den rechten Stick langsam bis zum Anschlag drehen.
- Wenn weiterhin nicht erkannt: pip-Installation fehlgeschlagen → Manuell nachinstallieren:
  ```
  py -m pip install gamepadla-plus
  ```

**Problem: HidUSBF wird nicht geladen**
- Internet-Verbindung erforderlich (Download vom GitHub).
- Setup.exe-Fenster wurde möglicherweise im Hintergrund geöffnet (Alt+Tab).
- Falls 404-Fehler: HidUSBF-Projekt-URL hat sich ggf. geändert (Issue/PR gerne willkommen).

### Deinstallation
Löschen Sie einfach die `LAGZERO_Tweaker.exe` und optional die Datei:
```
C:\ProgramData\LAGZERO\
```
(Enthält Backups und heruntergeladene Tools.)

### Support & Feedback
- GitHub: https://github.com/.../ (Link erforderlich)
- Issues: Probleme, Fehler, Feature-Requests
- Discussions: Fragen, Best Practices

---

**Version:** 0.3.0 BETA
**Zuletzt aktualisiert:** 2026-09-14
