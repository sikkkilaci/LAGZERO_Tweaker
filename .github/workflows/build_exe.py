#!/usr/bin/env python3
import subprocess
import sys

print("\n" + "="*50)
print("LAG|ZERØ TWEAKER - EXE Builder")
print("="*50 + "\n")

print("1. Installing psutil...")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "psutil"], check=False)

print("2. Installing pyinstaller...")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyinstaller"], check=False)

print("3. Building EXE (wait 1-2 minutes)...\n")
result = subprocess.run([
    sys.executable, "-m", "pyinstaller",
    "--onefile", "--windowed",
    "--name", "LAGZERO_Tweaker",
    "lagzero_tweaker.py"
])

if result.returncode == 0:
    print("\n" + "="*50)
    print("BUILD SUCCESS!")
    print("="*50)
    print("\nFile: LAGZERO_Tweaker.exe")
    print("Location: ./dist/LAGZERO_Tweaker.exe\n")
else:
    print("\nBuild failed!")

input("Press Enter to exit...")
