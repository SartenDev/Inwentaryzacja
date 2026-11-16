import platform
import socket
import subprocess
import os
import json
import sys
import csv
import plistlib
from pathlib import Path
from datetime import datetime, timezone

def run(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip().splitlines()
    except (OSError, subprocess.TimeoutExpired):
        return []


def windows():
    import winreg
    apps = []
    paths = [
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    ]

    for root, path in paths:
        try:
            key = winreg.OpenKey(root, path)
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey = winreg.OpenKey(
                        key, winreg.EnumKey(key, i)
                    )
                    name = winreg.QueryValueEx(
                        subkey, "DisplayName"
                    )[0]

                    try:
                        version = winreg.QueryValueEx(
                            subkey, "DisplayVersion"
                        )[0]
                    except OSError:
                        version = ""

                    if name:
                        apps.append({
                            "name": name,
                            "version": version
                        })
                except OSError:
                    continue
        except OSError:
            continue
    return apps


def macOS():
    import plistlib

    apps = []
    directories = [
        Path("/Applications"),
        Path("/Applications/Utilities"),
        Path("/System/Applications"),
        Path.home() / "Applications",
    ]

    for directory in directories:
        if not directory.is_dir():
            continue
        for app in directory.glob("*.app"):
            version = ""
            try:
                with open(app / "Contents" / "Info.plist", "rb") as f:
                    info = plistlib.load(f)
                version = str(
                    info.get("CFBundleShortVersionString")
                    or info.get("CFBundleVersion")
                    or ""
                )
            except Exception:
                pass
            apps.append({"name": app.stem, "version": version})
    return apps

def linux():
    apps = []

    if platform.system() == "Linux":
        if os.path.exists("/usr/bin/dpkg-query"):
            lines = run([
                "dpkg-query", "-W",
                "-f=${Package}\t${Version}\n"
            ])

            for line in lines:
                parts = line.split("\t")
                if len(parts) == 2:
                    apps.append({
                        "name": parts[0],
                        "version": parts[1]
                    })

        elif os.path.exists("/usr/bin/rpm"):
            lines = run([
                "rpm", "-qa", "--qf",
                "%{NAME}\t%{VERSION}-%{RELEASE}\n"
            ])

            for line in lines:
                parts = line.split("\t")
                if len(parts) == 2:
                    apps.append({
                        "name": parts[0],
                        "version": parts[1]
                    })
    return apps

def applications():
    system = platform.system()

    if system == "Windows":
        return windows()
    elif system == "Darwin":
        return macOS()
    elif system == "Linux":
        return linux()

    return []



if __name__ == "__main__":
    raport = {
        "device": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "applications": applications()
    }
    if getattr(sys, "frozen", False):
        output_dir = Path(sys.executable).parent
    else:
        output_dir = Path(__file__).parent

    output_file_json = output_dir / "data.json"
    output_file_csv = output_dir / "data.csv"
    with open(output_file_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=',')
        for item in raport:
            if item == "applications":
                w.writerow("")
                w.writerow(["NAME", "VERSION"])
                for app in raport[item]:
                    w.writerow([app["name"], app["version"]])
            else:
                w.writerow([item, raport[item]])


    with open(output_file_json, "w", encoding="utf-8") as f:
        json.dump(raport, f, indent=4, ensure_ascii=False)


