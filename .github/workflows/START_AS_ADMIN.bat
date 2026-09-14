@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~dp0lagzero_tweaker.py' -Verb RunAs"
