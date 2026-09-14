import os, sys, json, ctypes, subprocess, threading, re, time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
try:
    import psutil
except ImportError:
    psutil = None

APP = 'LAG|ZERØ'
VERSION = '0.3.0 BETA'
DATA_DIR = Path(os.environ.get('PROGRAMDATA', Path.home())) / 'LAGZERO'
BACKUP_FILE = DATA_DIR / 'backup.json'
TOOLS_DIR = DATA_DIR / 'Tools'
NVPI_EXE = TOOLS_DIR / 'NVIDIA Profile Inspector' / 'nvidiaProfileInspector.exe'
DLSS_NIP = TOOLS_DIR / 'lagzero_dlss.nip'
HIDUSBF_DIR = TOOLS_DIR / 'HidUSBF'
HIDUSBF_EXE = HIDUSBF_DIR / 'Setup.exe'

BG='#070a0c'; SIDEBAR='#090e11'; PANEL='#0d1317'; PANEL2='#11191e'; BORDER='#1b2a30'
TEXT='#edf3f5'; MUTED='#7f9098'; GREEN='#35f477'; GREEN2='#1ac95a'; RED='#ff5968'; YELLOW='#f4c95d'

TWEAKS = {
 'game_mode': ('Windows','Game Mode aktivieren', 'Aktiviert den Windows Game Mode.'),
 'gamedvr': ('Windows','Game DVR deaktivieren', 'Deaktiviert Game DVR/Captures im Hintergrund.'),
 'hags': ('Windows','Hardware GPU Scheduling', 'Aktiviert HAGS; ein Neustart kann erforderlich sein.'),
 'ultimate': ('Power','Ultimative Leistung', 'Aktiviert das Windows-Energieschema Ultimative Leistung.'),
 'nvidia_max': ('GPU','NVIDIA: Maximum Performance', 'Setzt den globalen NVIDIA Power-Management-Modus, sofern NVAPI/Registry-Profile verfügbar sind.'),
}

CATEGORY_DEFS = [
 ('windows','🪟','WINDOWS OPTIMIZATION','System für Gaming optimieren','Windows'),
 ('gpu','◈','GPU OPTIMIZATION','NVIDIA Einstellungen optimieren','GPU'),
 ('cpu','▣','CPU & POWER','Leistung und Energie optimieren','Power'),
 ('network','🌐','NETWORK OPTIMIZATION','Niedrigere Latenz. Stabile Verbindung.',None),
 ('services','⚙','SERVICES & BACKGROUND','Unnötige Dienste reduzieren',None),
 ('games','🎮','GAME SETTINGS','Spiele-spezifische Optimierungen',None),
]
# Diese drei Bereiche sind im Backend noch nicht real angebunden (siehe
# page_coming). Wir zeigen sie im Grid trotzdem an (gleiches Layout wie im
# Referenzdesign), aber mit DEAKTIVIERTEN Schaltern -- Toggles, die nichts
# bewirken würden, wären für Nutzer irreführend.
PLACEHOLDER_ROWS = {
 'network': ['Netzwerk-Adapter optimieren','TCP Auto-Tuning anpassen','DNS-Cache optimieren','QoS für Gaming','Netzwerkdrosselung deaktivieren'],
 'services': ['Unnötige Windows-Dienste deaktivieren','Druckdienste (wenn nicht benötigt)','Suchindexierung anpassen','Telemetrie und Diagnosedienste','Automatische Updates (Gaming-Mode)'],
 'games': ['Spiel-spezifische Profile aktivieren','Kompatibilitätseinstellungen setzen','Input-Lag Optimierungen','Hintergrundaufnahmen deaktivieren','Priorität auf Hoch setzen'],
}

# ---------- Windows helpers ----------
def is_admin():
    try: return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception: return False

def cmd(args, timeout=None):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                               creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode('utf-8','ignore') if isinstance(e.stdout,(bytes,bytearray)) else (e.stdout or '')
        err = (e.stderr.decode('utf-8','ignore') if isinstance(e.stderr,(bytes,bytearray)) else (e.stderr or '')) or 'Zeitlimit überschritten.'
        return subprocess.CompletedProcess(args, 1, out, err)
    except Exception as e:
        return subprocess.CompletedProcess(args, 1, '', str(e))

def reg_query(path, name):
    r=cmd(['reg','query',path,'/v',name])
    if r.returncode: return None
    for line in r.stdout.splitlines():
        if re.search(r'\s'+re.escape(name)+r'\s', line):
            p=line.split()
            return p[-1] if p else None
    return None

def reg_set(path,name,typ,value):
    return cmd(['reg','add',path,'/v',name,'/t',typ,'/d',str(value),'/f'])

def reg_delete(path,name):
    return cmd(['reg','delete',path,'/v',name,'/f'])

def active_power_guid():
    r=cmd(['powercfg','/getactivescheme'])
    m=re.search(r'([0-9a-fA-F-]{36})',r.stdout)
    return m.group(1) if m else None

def ultimate_guid():
    r=cmd(['powercfg','/list'])
    # Prefer English/German display name; otherwise detect duplicate by known base GUID is unreliable.
    for line in r.stdout.splitlines():
        if re.search(r'Ultimate Performance|Ultimative Leistung', line, re.I):
            m=re.search(r'([0-9a-fA-F-]{36})',line)
            if m:return m.group(1)
    return None

def ensure_data(): DATA_DIR.mkdir(parents=True,exist_ok=True)

def create_restore_point():
    # Best-effort Windows System Restore checkpoint as an extra safety net
    # in addition to our own backup.json. Silently ignored if System Restore
    # is disabled, throttled (Windows allows ~1 per 24h by default), or the
    # edition/policy does not support it.
    try:
        cmd(['powershell','-NoProfile','-Command',
             'Checkpoint-Computer -Description "LAGZERO Tweaker" -RestorePointType "MODIFY_SETTINGS"'])
    except Exception:
        pass

def backup(force=False):
    ensure_data()
    # Only capture a fresh snapshot if we don't already have one, so repeated
    # "Optimize" runs never overwrite the *original* pre-tweak state with an
    # already-tweaked state. Pass force=True to explicitly create a new
    # restore point (e.g. from a dedicated "New backup" action).
    if BACKUP_FILE.exists() and not force:
        try:
            return json.loads(BACKUP_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass  # corrupt/unreadable backup: fall through and recreate it
    data={'created':time.strftime('%Y-%m-%d %H:%M:%S'),'values':{
      'game_mode':reg_query(r'HKCU\\Software\\Microsoft\\GameBar','AllowAutoGameMode'),
      'gamedvr_enabled':reg_query(r'HKCU\\System\\GameConfigStore','GameDVR_Enabled'),
      'app_capture':reg_query(r'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR','AppCaptureEnabled'),
      'hags':reg_query(r'HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers','HwSchMode'),
      'power_scheme':active_power_guid(),
    }}
    BACKUP_FILE.write_text(json.dumps(data,indent=2),encoding='utf-8')
    return data

def apply_tweaks(selected):
    if not is_admin(): raise PermissionError('Administratorrechte erforderlich.')
    backup()  # captures the pristine state only on the very first run
    create_restore_point()
    results=[]
    if selected.get('game_mode'):
        r=reg_set(r'HKCU\\Software\\Microsoft\\GameBar','AllowAutoGameMode','REG_DWORD',1)
        if r.returncode: raise RuntimeError('Game Mode konnte nicht gesetzt werden.')
        results.append('Game Mode ON')
    if selected.get('gamedvr'):
        for p,n in [(r'HKCU\\System\\GameConfigStore','GameDVR_Enabled'),(r'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR','AppCaptureEnabled')]:
            r=reg_set(p,n,'REG_DWORD',0)
            if r.returncode: raise RuntimeError('Game DVR konnte nicht gesetzt werden.')
        results.append('Game DVR OFF')
    if selected.get('hags'):
        r=reg_set(r'HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers','HwSchMode','REG_DWORD',2)
        if r.returncode: raise RuntimeError('HAGS konnte nicht gesetzt werden.')
        results.append('HAGS ON (Neustart)')
    if selected.get('ultimate'):
        g=ultimate_guid()
        if not g:
            r=cmd(['powercfg','/duplicatescheme','e9a42b02-d5df-448d-aa00-03f14749eb61'])
            g=ultimate_guid()
        if g and cmd(['powercfg','/setactive',g]).returncode==0: results.append('Ultimate Performance ON')
        else: results.append('Ultimate Performance nicht verfügbar')
    # NVIDIA profile manipulation is intentionally not done through undocumented registry keys in v0.2.
    # We expose detection/status now; profile control will use a supported backend in a later build.
    if selected.get('nvidia_max'): results.append('NVIDIA Maximum Performance: vorbereitet')
    return results

def restore():
    if not is_admin(): raise PermissionError('Administratorrechte erforderlich.')
    if not BACKUP_FILE.exists(): raise FileNotFoundError('Kein LAG|ZERØ-Backup vorhanden.')
    d=json.loads(BACKUP_FILE.read_text(encoding='utf-8')).get('values',{})
    def rr(p,n,v):
        if v is None: reg_delete(p,n)
        else: reg_set(p,n,'REG_DWORD',int(v,0) if str(v).lower().startswith('0x') else int(v))
    rr(r'HKCU\\Software\\Microsoft\\GameBar','AllowAutoGameMode',d.get('game_mode'))
    rr(r'HKCU\\System\\GameConfigStore','GameDVR_Enabled',d.get('gamedvr_enabled'))
    rr(r'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR','AppCaptureEnabled',d.get('app_capture'))
    rr(r'HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers','HwSchMode',d.get('hags'))
    if d.get('power_scheme'): cmd(['powercfg','/setactive',d['power_scheme']])
    return 'Backup wiederhergestellt.'

# ---------- NVIDIA Profile Inspector / DLSS ----------
def find_nvpi():
    candidates = [NVPI_EXE,
        Path(os.environ.get('LOCALAPPDATA','')) / 'NVIDIAProfileInspector' / 'nvidiaProfileInspector.exe',
        Path(os.environ.get('ProgramFiles','')) / 'NVIDIA Profile Inspector' / 'nvidiaProfileInspector.exe',
        Path(os.environ.get('ProgramFiles(x86)','')) / 'NVIDIA Profile Inspector' / 'nvidiaProfileInspector.exe']
    for c in candidates:
        try:
            if c.exists(): return c
        except Exception: pass
    return None

def ensure_dlss_nip():
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    nip = '''<?xml version="1.0" encoding="utf-16"?>
<ArrayOfProfile>
  <Profile>
    <ProfileName>Base Profile</ProfileName>
    <Executeables />
    <Settings>
      <ProfileSetting>
        <SettingNameInfo>DLSS - Enable DLL Override</SettingNameInfo>
        <SettingID>283385345</SettingID>
        <SettingValue>1</SettingValue>
        <ValueType>Dword</ValueType>
      </ProfileSetting>
      <ProfileSetting>
        <SettingNameInfo>DLSS - Forced Model Preset Profile</SettingNameInfo>
        <SettingID>6505105</SettingID>
        <SettingValue>1</SettingValue>
        <ValueType>Dword</ValueType>
      </ProfileSetting>
      <ProfileSetting>
        <SettingNameInfo>DLSS - Forced Preset Letter</SettingNameInfo>
        <SettingID>283385331</SettingID>
        <SettingValue>16777215</SettingValue>
        <ValueType>Dword</ValueType>
      </ProfileSetting>
    </Settings>
  </Profile>
</ArrayOfProfile>
'''
    DLSS_NIP.write_text(nip, encoding='utf-16')
    return DLSS_NIP

def install_nvpi_runtime():
    existing = find_nvpi()
    if existing: return existing
    script = r'''$ErrorActionPreference = "Stop"
$base = Join-Path $env:LOCALAPPDATA "LAGZERO\Tools\NVIDIA Profile Inspector"
New-Item -ItemType Directory -Force -Path $base | Out-Null
$api = Invoke-RestMethod -Uri "https://api.github.com/repos/Orbmu2k/nvidiaProfileInspector/releases/latest" -Headers @{"User-Agent"="LAGZERO-Tweaker"}
$asset = $api.assets | Where-Object { $_.name -match '^nvidiaProfileInspector.*\.zip$' } | Select-Object -First 1
if (-not $asset) { throw "Kein NVIDIA Profile Inspector ZIP-Asset gefunden." }
$zip = Join-Path $env:TEMP "lagzero_nvpi.zip"
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip -UseBasicParsing
Expand-Archive -Path $zip -DestinationPath $base -Force
Remove-Item $zip -Force -ErrorAction SilentlyContinue
$exe = Get-ChildItem -Path $base -Filter "nvidiaProfileInspector.exe" -Recurse | Select-Object -First 1
if (-not $exe) { throw "nvidiaProfileInspector.exe wurde nicht gefunden." }
# Integrity/provenance visibility: log the release tag, publish date and
# SHA256 of the downloaded binary to a local audit file so a user (or
# support) can compare it against the GitHub release page if in doubt.
# This does not block execution -- it only makes tampering detectable.
try {
    $hash = (Get-FileHash -Path $exe.FullName -Algorithm SHA256).Hash
    $log = @"
LAG|ZERØ NVIDIA Profile Inspector install log
Release tag: $($api.tag_name)
Published:   $($api.published_at)
Asset URL:   $($asset.browser_download_url)
SHA256:      $hash
"@
    Set-Content -Path (Join-Path $base "install_log.txt") -Value $log -Encoding UTF8
} catch { }
Write-Output $exe.FullName
'''
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    ps = TOOLS_DIR / 'install_nvpi.ps1'
    ps.write_text(script, encoding='utf-8')
    r = cmd(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ps)])
    if r.returncode:
        raise RuntimeError('NVIDIA Profile Inspector konnte nicht installiert werden. ' + (r.stderr.strip() or r.stdout.strip()))
    path = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''
    return Path(path) if path and Path(path).exists() else find_nvpi()

def apply_dlss_latest():
    if not is_admin(): raise PermissionError('Administratorrechte erforderlich.')
    nvpi = find_nvpi() or install_nvpi_runtime()
    if not nvpi or not nvpi.exists(): raise FileNotFoundError('NVIDIA Profile Inspector nicht gefunden.')
    nip = ensure_dlss_nip()
    DATA_DIR.joinpath('NVIDIA Profiles').mkdir(parents=True, exist_ok=True)
    cmd([str(nvpi), '-exportCustomized'])
    r = cmd([str(nvpi), '-silentImport', str(nip)])
    if r.returncode:
        raise RuntimeError('DLSS-Profil konnte nicht importiert werden: ' + (r.stderr.strip() or r.stdout.strip()))
    return 'DLSS Latest Override aktiviert (globales NVIDIA-Profil).'

# ---------- HidUSBF (USB/HID Polling-Rate „Übertaktung") ----------
# HidUSBF (https://github.com/LordOfMice/hidusbf) ist ein Kernel-Filtertreiber.
# Wichtig für Nutzer:
#  - Seit 2024/07 sind die Treiber signiert -> i.d.R. KEIN Secure-Boot-Eingriff
#    mehr nötig (siehe Projekt-README, Abschnitt "History").
#  - Für die PATCHING-Varianten (nötig für Overclocking von Low-Speed-Geräten
#    über den Standard hinaus) verlangt der Hersteller ausdrücklich, dass
#    Windows Memory Integrity (Core Isolation) deaktiviert ist. Das ist ein
#    echter Sicherheits-Trade-off, den wir NICHT automatisch für den Nutzer
#    umschalten, sondern nur erklären.
#  - Es gibt keine dokumentierte/stabile Kommandozeile oder Registry-API, um
#    "welches Gerät bekommt welche Rate" automatisiert zu setzen. Wir bilden
#    daher bewusst nur Download/Update + Start der offiziellen Setup.exe ab,
#    statt das Gerät selbst zu raten (Fehlgriff könnte z.B. die Tastatur statt
#    des Controllers filtern).
HIDUSBF_ZIP_URL = 'https://raw.githubusercontent.com/LordOfMice/hidusbf/master/hidusbf.zip'

def find_hidusbf_setup():
    if HIDUSBF_EXE.exists(): return HIDUSBF_EXE
    if HIDUSBF_DIR.exists():
        for p in HIDUSBF_DIR.rglob('Setup.exe'):
            return p
    return None

def install_hidusbf_runtime():
    existing = find_hidusbf_setup()
    if existing: return existing
    script = r'''$ErrorActionPreference = "Stop"
$base = Join-Path $env:LOCALAPPDATA "LAGZERO\Tools\HidUSBF"
New-Item -ItemType Directory -Force -Path $base | Out-Null
$url = "''' + HIDUSBF_ZIP_URL + r'''"
$zip = Join-Path $env:TEMP "lagzero_hidusbf.zip"
Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
$zipHash = (Get-FileHash -Path $zip -Algorithm SHA256).Hash
Expand-Archive -Path $zip -DestinationPath $base -Force
Remove-Item $zip -Force -ErrorAction SilentlyContinue
$exe = Get-ChildItem -Path $base -Filter "Setup.exe" -Recurse | Select-Object -First 1
if (-not $exe) { throw "Setup.exe wurde im HidUSBF-Paket nicht gefunden." }
try {
    $log = @"
LAG|ZERO HidUSBF install log
Quelle:     $url
Zip SHA256: $zipHash
Setup:      $($exe.FullName)
"@
    Set-Content -Path (Join-Path $base "install_log.txt") -Value $log -Encoding UTF8
} catch { }
Write-Output $exe.FullName
'''
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    ps = TOOLS_DIR / 'install_hidusbf.ps1'
    ps.write_text(script, encoding='utf-8')
    r = cmd(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ps)])
    if r.returncode:
        raise RuntimeError('HidUSBF konnte nicht heruntergeladen werden. ' + (r.stderr.strip() or r.stdout.strip()))
    path = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''
    return Path(path) if path and Path(path).exists() else find_hidusbf_setup()

def open_hidusbf_config():
    if not is_admin(): raise PermissionError('Administratorrechte erforderlich.')
    setup = find_hidusbf_setup() or install_hidusbf_runtime()
    if not setup or not setup.exists(): raise FileNotFoundError('HidUSBF Setup.exe nicht gefunden.')
    # "/all" zeigt auch Controller/Gamepads (nicht nur erkannte Mäuse) in der Liste.
    subprocess.Popen([str(setup), '/all'])
    return 'HidUSBF-Gerätekonfiguration geöffnet — Gerät auswählen, Rate setzen, [Restart].'

# ---------- GamepadLA (Controller-Latenz-/Polling-Test) ----------
# Nutzt das quelloffene CLI-Tool "gamepadla-plus" (PyPI), das wir bei Bedarf
# per pip installieren und dessen Textausgabe wir in unser eigenes,
# LAG|ZERØ-gestyltes Ergebnis-Panel parsen (kein externes Fenster nötig).
_GLA_FIELDS = [
    ('mode',      'Gamepad mode'),
    ('os',        'Operating System'),
    ('rate_max',  'Polling Rate Max.'),
    ('rate_avg',  'Polling Rate Avg.'),
    ('stability', 'Stability'),
    ('lat_min',   'Minimal latency'),
    ('lat_avg',   'Average latency'),
    ('lat_max',   'Maximum latency'),
    ('jitter',    'Jitter'),
]

def gamepadla_exe():
    # Console-Script liegt im selben Environment wie der aktuell laufende
    # Python-Interpreter -> per Vollpfad ansprechen statt uns auf PATH zu verlassen.
    scripts_dir = Path(sys.executable).parent / 'Scripts'
    for name in ('gamepadla.exe','gamepadla'):
        p = scripts_dir / name
        if p.exists(): return str(p)
    return 'gamepadla'  # Fallback: PATH

def ensure_gamepadla():
    if cmd([gamepadla_exe(), '--help']).returncode == 0:
        return True
    r = cmd([sys.executable, '-m', 'pip', 'install', '--quiet', 'gamepadla-plus'], timeout=120)
    if r.returncode:
        raise RuntimeError('gamepadla-plus konnte nicht installiert werden. ' + (r.stderr.strip() or r.stdout.strip()))
    if cmd([gamepadla_exe(), '--help']).returncode:
        raise RuntimeError('gamepadla wurde installiert, ist aber nicht startbar (PATH/Environment prüfen).')
    return True

def parse_gamepadla_output(text):
    out={}
    for key,label in _GLA_FIELDS:
        m = re.search(re.escape(label)+r'\s*[:|│]?\s*([^\n\r|│]+)', text)
        if m:
            out[key]=m.group(1).strip(' \t|│─━')
    return out

def run_gamepad_latency_test(stick='right', timeout_s=30):
    ensure_gamepadla()
    r = cmd([gamepadla_exe(),'test','--stick',stick], timeout=timeout_s)
    combined = (r.stdout or '') + '\n' + (r.stderr or '')
    parsed = parse_gamepadla_output(combined)
    if not parsed:
        tail = combined.strip()[-400:]
        raise RuntimeError('Testergebnis konnte nicht gelesen werden. Controller angeschlossen/bewegt?\n' + tail)
    return parsed

# ---------- monitoring ----------
def nvidia():
    r=cmd(['nvidia-smi','--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,clocks.gr','--format=csv,noheader,nounits'])
    if r.returncode or not r.stdout.strip(): return None
    p=[x.strip() for x in r.stdout.splitlines()[0].split(',')]
    if len(p)<7:return None
    return dict(name=p[0],temp=p[1],util=p[2],vram=p[3],vram_total=p[4],power=p[5],clock=p[6])

def cpu_temp():
    # Best-effort ACPI temperature. Many modern boards expose no usable WMI value.
    r=cmd(['powershell','-NoProfile','-Command','(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object -First 1 CurrentTemperature).CurrentTemperature'])
    if r.returncode==0:
        try:
            v=float(r.stdout.strip())
            if v>2732:return f'{v/10-273.15:.0f}'
        except: pass
    return '—'

def os_name():
    r=cmd(['powershell','-NoProfile','-Command','(Get-CimInstance Win32_OperatingSystem).Caption'])
    return r.stdout.strip() or 'Windows'

class App:
    def __init__(self,root):
        self.root=root; root.title(f'{APP} Performance Tweaker'); root.geometry('1450x900'); root.minsize(1120,720); root.configure(bg=BG)
        self.vars={}; self.pages={}; self.current='Optimize'; self.status_text='Ready'
        self._tick_count=0; self._cpu_temp_cache='—'; self._os_name_cache=None
        self.build(); self.show('Optimize'); self.tick()
        if not is_admin(): self.set_status('Administratorrechte fehlen – starte die Anwendung als Administrator.',RED)

    def frame(self,p,bg=None,**kw): return tk.Frame(p,bg=bg or PANEL,**kw)
    def text(self,p,t,size=10,color=TEXT,bold=False,**kw): return tk.Label(p,text=t,bg=p.cget('bg'),fg=color,font=('Segoe UI',size,'bold' if bold else 'normal'),**kw)
    def card(self,p,**kw): return tk.Frame(p,bg=PANEL,highlightbackground=BORDER,highlightthickness=1,**kw)
    def button(self,p,t,command,bg=PANEL2,fg=TEXT,**kw): return tk.Button(p,text=t,command=command,bg=bg,fg=fg,activebackground=BORDER,activeforeground=TEXT,relief='flat',bd=0,cursor='hand2',font=('Segoe UI',10,'bold'),**kw)

    def build(self):
        side=self.frame(self.root,SIDEBAR,width=235); side.pack(side='left',fill='y'); side.pack_propagate(False)
        self.text(side,'LAG|ZERØ',25,GREEN,True).pack(anchor='w',padx=26,pady=(27,0)); self.text(side,'PERFORMANCE TWEAKER',8,TEXT,True).pack(anchor='w',padx=29,pady=(0,28))
        nav=['Dashboard','Optimize','Windows','GPU','CPU & Power','Network','Services','Games','Tools']
        for name in nav:
            b=self.button(side,name,lambda n=name:self.show(n),bg=SIDEBAR,fg=TEXT); b.pack(fill='x',padx=10,pady=2,ipady=10); setattr(self,'nav_'+name.replace(' ','_').replace('&','and'),b)
        self.text(side,'',1).pack(expand=True)
        self.text(side,'PLAY HIGHER. LAG LOWER.',8,MUTED,True).pack(anchor='w',padx=28,pady=(0,5)); self.text(side,VERSION,8,MUTED).pack(anchor='w',padx=28,pady=(0,22))
        main=self.frame(self.root,BG); main.pack(side='left',fill='both',expand=True,padx=18,pady=15)
        head=self.frame(main,BG); head.pack(fill='x')
        self.text(head,'LAG|ZERØ',18,TEXT,True).pack(side='left'); self.status_badge=self.text(head,'● READY',9,GREEN,True); self.status_badge.pack(side='right',pady=5)
        metrics=self.frame(main,BG); metrics.pack(fill='x',pady=(14,14)); self.metrics={}
        for title,key in [('CPU','cpu'),('GPU','gpu'),('RAM','ram'),('FPS','fps')]:
            c=self.card(metrics); c.pack(side='left',fill='x',expand=True,padx=4,ipady=9)
            self.text(c,title,8,MUTED,True).pack(anchor='w',padx=16); val=self.text(c,'—',20,TEXT,True); val.pack(anchor='w',padx=16); sub=self.text(c,'',8,MUTED); sub.pack(anchor='w',padx=16); self.metrics[key]=(val,sub)
        self.content=self.frame(main,BG); self.content.pack(fill='both',expand=True)

    def clear(self):
        for w in self.content.winfo_children(): w.destroy()
    def show(self,name):
        self.current=name; self.clear(); self.update_nav();
        if name=='Optimize': self.page_optimize()
        elif name=='Dashboard': self.page_dashboard()
        elif name=='Windows': self.page_tweaks('Windows')
        elif name=='GPU': self.page_tweaks('GPU')
        elif name=='CPU & Power': self.page_tweaks('Power')
        elif name=='Tools': self.page_tools()
        elif name in ('Network','Services','Games'): self.page_coming(name)
    def update_nav(self):
        for n in ['Dashboard','Optimize','Windows','GPU','CPU & Power','Network','Services','Games','Tools']:
            b=getattr(self,'nav_'+n.replace(' ','_').replace('&','and')); b.config(bg=GREEN2 if n==self.current else SIDEBAR,fg='#021108' if n==self.current else TEXT)

    def hero(self,p,title,sub):
        c=self.card(p); c.pack(fill='x',pady=(0,12),ipady=12); self.text(c,title,22,TEXT,True).pack(anchor='w',padx=20,pady=(4,0)); self.text(c,sub,9,MUTED).pack(anchor='w',padx=20,pady=(2,3)); return c
    def toggle_card(self,p,key):
        group,label,desc=TWEAKS[key]; c=self.card(p); c.pack(fill='x',pady=5,padx=2,ipady=7)
        self.text(c,label,10,TEXT,True).pack(side='left',padx=16); self.text(c,desc,8,MUTED).pack(side='left',padx=8)
        v=tk.BooleanVar(value=True); self.vars[key]=v
        tk.Checkbutton(c,variable=v,bg=PANEL,activebackground=PANEL,selectcolor=GREEN2,bd=0,highlightthickness=0).pack(side='right',padx=14)
    def page_optimize(self):
        self.hero(self.content,'OPTIMIZE YOUR PC','Ausgewählte, reversible Windows-Gaming-Optimierungen mit Backup.')
        body=self.frame(self.content,BG); body.pack(fill='both',expand=True)
        left=self.frame(body,BG); left.pack(side='left',fill='both',expand=True)
        right=self.card(body,width=300); right.pack(side='right',fill='y',padx=(12,0)); right.pack_propagate(False)
        for k in ['game_mode','gamedvr','hags','ultimate','nvidia_max']: self.toggle_card(left,k)
        self.button(left,'ϟ  OPTIMIZE PC',self.optimize,bg=GREEN,fg='#031008',font=('Segoe UI',14,'bold'),pady=15).pack(fill='x',pady=(15,5))
        self.button(left,'↶  RESTORE LAST BACKUP',self.restore,bg=PANEL2,fg=TEXT,font=('Segoe UI',11,'bold'),pady=13).pack(fill='x',pady=5)
        self.text(right,'SYSTEM STATUS',9,MUTED,True).pack(anchor='w',padx=18,pady=(20,2)); self.right_status=self.text(right,'READY',18,GREEN,True); self.right_status.pack(anchor='w',padx=18)
        self.right_detail=self.text(right,'Bereit für den ersten Test.',9,MUTED,wraplength=255,justify='left'); self.right_detail.pack(anchor='w',padx=18,pady=(3,18))
        self.text(right,'DESIGN GOAL',9,MUTED,True).pack(anchor='w',padx=18,pady=(8,5)); self.text(right,'Hypertune-inspirierte Oberfläche, aber mit eigener LAG|ZERØ-Optimierungslogik.',9,TEXT,wraplength=255,justify='left').pack(anchor='w',padx=18)
        self.text(right,'FUTURE TOOLS',9,MUTED,True).pack(anchor='w',padx=18,pady=(25,5)); self.text(right,'HidUSBF\nGamepadLA LatencyMon\n\nDiese Integrationen sind als eigener Tools-Bereich vorbereitet.',9,TEXT,justify='left').pack(anchor='w',padx=18)

    def page_dashboard(self):
        self.hero(self.content,'DASHBOARD','Live-Werte während der Nutzung – bewusst kein vollwertiger Hardware-Monitor.')
        c=self.card(self.content); c.pack(fill='both',expand=True)
        self.text(c,'LIVE MONITORING',10,MUTED,True).pack(anchor='w',padx=22,pady=(20,12))
        self.dashboard_info=self.text(c,'Erkennung läuft …',12,TEXT,justify='left'); self.dashboard_info.pack(anchor='w',padx=22)
    def page_tweaks(self,group):
        title={'Windows':'WINDOWS OPTIMIZATION','GPU':'GPU OPTIMIZATION','Power':'CPU & POWER'}[group]
        self.hero(self.content,title,'Einzelne Funktionen getrennt testen. Änderungen werden vor Anwendung gesichert.')
        for k,(g,_,_) in TWEAKS.items():
            if g==group:self.toggle_card(self.content,k)
        if group=='GPU': self.text(self.content,'NVIDIA-Profile werden in dieser Beta nur erkannt/angezeigt. Keine undokumentierten Treiber-Registry-Hacks.',8,YELLOW,wraplength=700,justify='left').pack(anchor='w',pady=12)
        self.button(self.content,'APPLY SELECTED',self.optimize,bg=GREEN,fg='#031008',pady=12).pack(fill='x',pady=8)
    def page_tools(self):
        self.hero(self.content,'TOOLS','Gaming-Tools und Treiberfunktionen direkt aus LAG|ZERØ.')
        c=self.card(self.content); c.pack(fill='x',pady=6,ipady=12)
        self.text(c,'NVIDIA DLSS',12,TEXT,True).pack(side='left',padx=18)
        self.text(c,'Global: neueste installierte DLSS-SR-Version + Recommended Preset',9,MUTED).pack(side='left',padx=10)
        self.button(c,'APPLY LATEST DLSS',self.apply_dlss,bg=GREEN,fg='#031008',pady=10).pack(side='right',padx=14)
        c2=self.card(self.content); c2.pack(fill='x',pady=6,ipady=12)
        self.text(c2,'NVIDIA PROFILE INSPECTOR',12,TEXT,True).pack(side='left',padx=18)
        self.text(c2,'Offizielles Upstream-Release wird bei Bedarf automatisch bezogen.',9,MUTED).pack(side='left',padx=10)
        self.button(c2,'INSTALL / UPDATE',self.install_nvpi,bg=PANEL2,fg=TEXT,pady=10).pack(side='right',padx=14)

        c3=self.card(self.content); c3.pack(fill='x',pady=6,ipady=12)
        self.text(c3,'HIDUSBF — CONTROLLER POLLING RATE',12,TEXT,True).pack(side='left',padx=18)
        self.text(c3,'Öffnet die offizielle HidUSBF-Gerätekonfiguration (Treiber wird bei Bedarf geladen).',9,MUTED,wraplength=430,justify='left').pack(side='left',padx=10)
        self.button(c3,'GERÄTE-KONFIGURATION ÖFFNEN',self.open_hidusbf,bg=PANEL2,fg=TEXT,pady=10).pack(side='right',padx=14)
        self.text(self.content,'HidUSBF ist ein Kernel-Filtertreiber. Aktuelle Treiber sind signiert (i.d.R. kein Secure-Boot-Eingriff nötig). '
                                'Für Overclocking über den Standard hinaus verlangt der Hersteller ausdrücklich deaktivierte Windows Memory Integrity (Core Isolation) — '
                                'diese Einstellung ändert LAG|ZERØ NICHT automatisch. Gerät auswählen und Rate setzen erfolgt bewusst im offiziellen HidUSBF-Fenster, '
                                'damit nicht versehentlich das falsche USB-Gerät (z. B. die Tastatur) gefiltert wird.',8,YELLOW,wraplength=850,justify='left').pack(anchor='w',pady=(4,12))

        c4=self.card(self.content); c4.pack(fill='x',pady=6,ipady=12)
        self.text(c4,'GAMEPADLA — CONTROLLER-LATENZTEST',12,TEXT,True).pack(side='left',padx=18)
        self.text(c4,'Misst Polling-Rate, Stabilität und synthetische Stick-Latenz direkt in LAG|ZERØ.',9,MUTED,wraplength=430,justify='left').pack(side='left',padx=10)
        self.button(c4,'TEST STARTEN (RECHTER STICK)',self.run_gamepadla,bg=GREEN,fg='#031008',pady=10).pack(side='right',padx=14)
        self.text(self.content,'Während des ~5-Sekunden-Tests den rechten Analogstick langsam bis zum Anschlag drehen. Miss die Stick-Bewegung, nicht die Tastendruck-Latenz.',
                  8,MUTED,wraplength=850,justify='left').pack(anchor='w',pady=(4,8))
        self.gla_result=self.card(self.content); self.gla_result.pack(fill='x',pady=(0,12),ipady=10)
        self.text(self.gla_result,'Noch kein Testergebnis.',10,MUTED).pack(anchor='w',padx=18,pady=8)

        self.text(self.content,'DLSS Override verändert das globale NVIDIA-Treiberprofil; es ersetzt keine DLL im Spielordner. Vor dem Import wird ein NVIDIA-Profil-Export angestoßen.',9,YELLOW,wraplength=850,justify='left').pack(anchor='w',pady=(2,4))
    def page_coming(self,name):
        self.hero(self.content,name.upper(),'Bereich ist im UI vorbereitet und wird in kommenden Test-Builds mit messbaren Tweaks gefüllt.')
        self.text(self.content,'Noch keine Änderungen aktiv.',12,MUTED).pack(anchor='w',padx=20,pady=20)

    def install_nvpi(self):
        self.set_status('NVIDIA Profile Inspector wird installiert/aktualisiert …',GREEN)
        def work():
            try:
                p=install_nvpi_runtime(); msg=f'NVIDIA Profile Inspector bereit: {p}' if p else 'Installation fehlgeschlagen.'
                self.root.after(0,lambda:self.set_status(msg,GREEN if p else RED))
            except Exception as e:self.root.after(0,lambda:self.set_status(str(e),RED))
        threading.Thread(target=work,daemon=True).start()
    def apply_dlss(self):
        self.set_status('DLSS Latest Override wird angewendet …',GREEN)
        def work():
            try:
                msg=apply_dlss_latest(); self.root.after(0,lambda:self.set_status(msg,GREEN))
            except Exception as e:self.root.after(0,lambda:self.set_status(str(e),RED))
        threading.Thread(target=work,daemon=True).start()
    def open_hidusbf(self):
        if not messagebox.askyesno(APP,'HidUSBF ist ein Kernel-Treiber zur USB/HID-Polling-Rate. Für Overclocking über den '
                                        'Standard hinaus muss ggf. Windows Memory Integrity (Core Isolation) deaktiviert sein — '
                                        'das ändert LAG|ZERØ nicht automatisch. Die eigentliche Geräteauswahl erfolgt im offiziellen '
                                        'HidUSBF-Fenster.\n\nHidUSBF jetzt laden/öffnen?'):
            return
        self.set_status('HidUSBF wird vorbereitet …',GREEN)
        def work():
            try:
                msg=open_hidusbf_config(); self.root.after(0,lambda:self.set_status(msg,GREEN))
            except Exception as e:self.root.after(0,lambda:self.set_status(str(e),RED))
        threading.Thread(target=work,daemon=True).start()
    def run_gamepadla(self):
        self.set_status('Controller-Latenztest läuft — jetzt rechten Stick langsam bis zum Anschlag drehen …',GREEN)
        def work():
            try:
                res=run_gamepad_latency_test('right',30)
                self.root.after(0,lambda:(self.render_gla_result(res), self.set_status('Latenztest abgeschlossen.',GREEN)))
            except Exception as e:self.root.after(0,lambda:self.set_status(str(e),RED))
        threading.Thread(target=work,daemon=True).start()
    def render_gla_result(self,res):
        for w in self.gla_result.winfo_children(): w.destroy()
        rows=[('Controller',res.get('mode','—')),('Polling Rate (max/avg)',f"{res.get('rate_max','—')} / {res.get('rate_avg','—')}"),
              ('Stabilität',res.get('stability','—')),('Latenz (min/avg/max)',f"{res.get('lat_min','—')} / {res.get('lat_avg','—')} / {res.get('lat_max','—')}"),
              ('Jitter',res.get('jitter','—'))]
        for label,val in rows:
            r=self.frame(self.gla_result,PANEL); r.pack(fill='x',padx=18,pady=2)
            self.text(r,label,9,MUTED).pack(side='left'); self.text(r,val,11,GREEN,True).pack(side='right')

    def set_status(self,msg,color=GREEN):
        self.status_badge.config(text=('● ERROR' if color==RED else '● READY'),fg=color)
        if hasattr(self,'right_status'):
            self.right_status.config(text='ERROR' if color==RED else 'READY',fg=color); self.right_detail.config(text=msg)
        if hasattr(self,'dashboard_info'): self.dashboard_info.config(text=msg)
    def optimize(self):
        selected={k:v.get() for k,v in self.vars.items()}
        if not any(selected.values()):
            self.set_status('Keine Änderungen ausgewählt.',YELLOW); return
        if not messagebox.askyesno(APP,'Ausgewählte Systemeinstellungen (Registry/Energieschema) werden geändert.\n'
                                        'Ein Backup und – falls möglich – ein Windows-Wiederherstellungspunkt werden zuvor angelegt.\n\nFortfahren?'):
            return
        self.set_status('Optimierung läuft …',GREEN)
        def work():
            try:
                res=apply_tweaks(selected); msg='  •  '.join(res) if res else 'Keine Änderungen ausgewählt.'
                self.root.after(0,lambda:self.set_status(msg,GREEN))
            except Exception as e:self.root.after(0,lambda:self.set_status(str(e),RED))
        threading.Thread(target=work,daemon=True).start()
    def restore(self):
        if not BACKUP_FILE.exists():
            self.set_status('Kein LAG|ZERØ-Backup vorhanden.',RED); return
        if not messagebox.askyesno(APP,'Der letzte LAG|ZERØ-Backup-Stand wird wiederhergestellt.\n\nFortfahren?'):
            return
        try:self.set_status(restore(),GREEN)
        except Exception as e:self.set_status(str(e),RED)

    def tick(self):
        try:
            self._tick_count+=1
            # os_name() and cpu_temp() each spawn a PowerShell/WMI process.
            # os_name never changes at runtime -> fetch it once and cache it.
            if self._os_name_cache is None:
                self._os_name_cache=os_name()
            # cpu_temp() is comparatively expensive and low-value at high
            # frequency -> refresh only every 5th tick (~9s) instead of
            # spawning a new PowerShell process every 1.8s.
            if self._tick_count % 5==1:
                self._cpu_temp_cache=cpu_temp()
            if psutil:
                ram=psutil.virtual_memory(); cpu=psutil.cpu_percent(interval=None)
                self.metrics['cpu'][0].config(text=(self._cpu_temp_cache+' °C') if self._cpu_temp_cache!='—' else '—')
                self.metrics['cpu'][1].config(text=f'{cpu:.0f}% load')
                self.metrics['ram'][0].config(text=f'{ram.used/1024**3:.1f} GB'); self.metrics['ram'][1].config(text=f'{ram.percent:.0f}% used')
            g=nvidia()
            if g:
                self.metrics['gpu'][0].config(text=f"{g['temp']} °C"); self.metrics['gpu'][1].config(text=f"{g['util']}%  •  {g['clock']} MHz")
                if hasattr(self,'dashboard_info'): self.dashboard_info.config(text=f"OS: {self._os_name_cache}\nGPU: {g['name']}\nGPU Power: {g['power']} W\nVRAM: {g['vram']} / {g['vram_total']} MB\nAdministrator: {'Yes' if is_admin() else 'No'}")
            else:
                self.metrics['gpu'][0].config(text='—'); self.metrics['gpu'][1].config(text='NVIDIA SMI nicht verfügbar')
                if hasattr(self,'dashboard_info'): self.dashboard_info.config(text=f"OS: {self._os_name_cache}\nGPU: nicht über nvidia-smi erkannt\nAdministrator: {'Yes' if is_admin() else 'No'}")
            self.metrics['fps'][0].config(text='—'); self.metrics['fps'][1].config(text='Game-Overlay später')
        except Exception: pass
        self.root.after(1800,self.tick)

if __name__=='__main__':
    if sys.platform!='win32': print('LAG|ZERØ ist für Windows 10/11 vorgesehen.')
    root=tk.Tk(); App(root); root.mainloop()
