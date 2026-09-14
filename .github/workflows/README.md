# LAG|ZERØ Tweaker v0.3.0 BETA

Windows Gaming-Performance-Optimizer. Optimiert Registry, Energiesparpläne und Treiber für maximale FPS und minimale Latenz — mit lokalem Backup und Restore.

**Neu in 0.3.0:**
- ✅ NVIDIA Profile Inspector Integration + APPLY LATEST DLSS
- ✅ HidUSBF Controller-Polling-Überclocking
- ✅ GamepadLA Latenz-/Polling-Rate-Test (direkt in der UI)
- ✅ Windows Wiederherstellungspunkt vor Optimierungen
- ✅ Bestätigungsdialoge vor Systemänderungen
- ✅ Optimierte Performance (gecachte OS-Info, reduzierte PowerShell-Calls)
- ✅ Vollständig als standalone `.exe` verteilbar

## Schnellstart

### Für Endnutzer
Laden Sie die fertige `LAGZERO_Tweaker.exe` herunter:
1. Entpacken Sie das ZIP
2. Doppelklick auf `LAGZERO_Tweaker.exe` (Admin-Rechte werden angefordert)
3. Fertig!

**Siehe:** `INSTALLATION_GUIDE.md` für Details.

### Für Entwickler (EXE selbst bauen)

**Systemanforderungen:**
- Python 3.8+
- Windows 10/11
- Internet-Verbindung (für pip-Abhängigkeiten)

**Schritte:**
1. Klonen Sie das Projekt oder laden Sie den Source herunter.
2. Öffnen Sie `BUILD_EXE.bat` (Doppelklick).
3. Das Skript installiert Abhängigkeiten und kompiliert die EXE (~1 Minute).
4. `LAGZERO_Tweaker.exe` liegt danach im gleichen Verzeichnis.

**Optionale:** `RELEASE_PACKAGE.bat` erstellt ein verteilbares ZIP mit README und Shortcuts.

Die Funktion lädt bei Bedarf das aktuelle Upstream-Release von NVIDIA Profile Inspector, exportiert die angepassten NVIDIA-Profile und importiert anschließend ein globales DLSS-Profil mit:
- DLSS DLL Override: neueste installierte Version
- Forced Model Preset Profile: Recommended
- Forced Preset Letter: Recommended/latest mapping

Das ändert das NVIDIA-Treiberprofil und ersetzt keine DLL im Spielordner. DLSS muss vom Spiel bereits unterstützt werden. Bei Treiber- oder Spieländerungen kann eine erneute Anwendung erforderlich sein.

HidUSBF und GamepadLA/LatencyMon sind weiterhin als zukünftige Tool-Integrationen vorbereitet.

Start: `START_AS_ADMIN.bat`

## Fixes in diesem Build (Robustheit/Sicherheit)
- **Kritisch:** `TOOLS_DIR`, `NVPI_EXE`, `DLSS_NIP` waren nirgends definiert → jeder Klick auf „APPLY LATEST DLSS" oder „INSTALL / UPDATE" ist mit `NameError` fehlgeschlagen. Jetzt behoben.
- Versionsstring im Code stand noch auf 0.2.0, jetzt konsistent 0.3.0.
- `backup()` überschrieb bei jedem „Optimize"-Lauf den vorhandenen Backup-Stand — bei zwei Durchläufen ging der wirklich ursprüngliche Zustand verloren. Backup wird jetzt nur einmalig (pristine) angelegt, außer explizit erzwungen.
- Vor Registry-/Energieschema-Änderungen wird zusätzlich (best effort) ein Windows-Wiederherstellungspunkt angelegt.
- Bestätigungsdialog vor „OPTIMIZE PC" und „RESTORE", da beides Systemeinstellungen ändert.
- Live-Monitoring spawnte bei jedem Tick (1,8s) 2–3 PowerShell-Prozesse (`os_name()`, doppelter `cpu_temp()`-Aufruf) — für ein Performance-Tool kontraproduktiv. OS-Name wird jetzt einmalig gecacht, CPU-Temperatur nur noch alle ~9s neu abgefragt.
- Der automatische NVIDIA-Profile-Inspector-Download protokolliert jetzt Release-Tag, Datum und SHA256-Hash lokal, damit die Herkunft der Binary im Zweifel nachvollziehbar/verifizierbar ist.

## Bekannte, noch offene Punkte
- Registry-Zugriffe laufen über `reg.exe`-Subprozesse statt über das `winreg`-Modul; funktioniert, ist aber langsamer und von der Textausgabe des Reg-Tools abhängig (Locale-Risiko). Migration auf `winreg` wäre robuster.
- Es existiert nur ein einziger Backup-Slot (`backup.json`); kein Verlauf/Versionierung mehrerer Snapshots.
- Der NVIDIA-Profile-Inspector-Download wird nicht kryptografisch signaturgeprüft (nur Hash-Logging), da das Upstream-Release nicht durchgängig codesigniert ist.

## Neu: HidUSBF (Controller-Polling-Rate) + GamepadLA (Latenztest)
- **HidUSBF** (github.com/LordOfMice/hidusbf) wird bei Bedarf direkt aus dem `master`-Branch geladen (das Projekt veröffentlicht keine GitHub Releases, sondern committet `hidusbf.zip` im Repo). Download-Hash + Quelle werden lokal protokolliert (`Tools/HidUSBF/install_log.txt`).
  - Seit 2024/07 sind die Treiber signiert → in der Regel kein Secure-Boot-Eingriff mehr nötig.
  - Für Overclocking über den Standard hinaus (patchende Varianten) verlangt der Hersteller **Windows Memory Integrity (Core Isolation) deaktiviert**. LAG|ZERØ ändert diese Einstellung bewusst nicht automatisch — das bleibt eine informierte Nutzerentscheidung.
  - Es gibt keine dokumentierte, stabile Kommandozeile/Registry-API, um "Gerät X bekommt Rate Y" automatisiert zu setzen. LAG|ZERØ lädt daher die offizielle `Setup.exe` (mit `/all`, damit auch Controller statt nur Mäuse gelistet werden) und öffnet sie — die eigentliche Geräteauswahl passiert bewusst im Originaltool, um nicht versehentlich das falsche USB-Gerät zu filtern.
- **GamepadLA** wird über das quelloffene CLI-Tool `gamepadla-plus` (PyPI) realisiert, bei Bedarf per `pip install` nachgerüstet. Die Textausgabe (`Polling Rate`, `Stability`, `Latency`, `Jitter`) wird geparst und in einem eigenen, LAG|ZERØ-gestylten Ergebnis-Panel angezeigt — kein externes Fenster.
- Beide Integrationen liegen im **Tools**-Tab neben NVIDIA Profile Inspector / DLSS.
