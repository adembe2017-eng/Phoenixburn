#!/usr/bin/env python3
"""
PhoenixBurn
-----------
A safe, fully simulated "ISO to USB" burner tool, built in Python
as part of the ALphoenixa OS / dstc educational project.

IMPORTANT: This tool does NOT write to any real disk or device.
It simulates the experience of burning an OS image (like Rufus or
Ventoy) for learning purposes only -- fake drives, fake progress,
fake verification. Nothing on your actual computer is touched.

Run:
    python3 phoenixburn.py
"""

import os
import sys
import time
import random
import string

APP_NAME = "PhoenixBurn"
VERSION = "1.0"

# ---------------------------------------------------------------
# بيانات وهمية: محركات أقراص وأنظمة تشغيل للاختيار منها
# ---------------------------------------------------------------
FAKE_DRIVES = [
    {"id": 1, "label": "SanDisk Ultra 32GB",  "device": "/dev/sdb1", "size_gb": 32},
    {"id": 2, "label": "Kingston DataTraveler 64GB", "device": "/dev/sdc1", "size_gb": 64},
    {"id": 3, "label": "Generic USB 3.0 16GB", "device": "/dev/sdd1", "size_gb": 16},
]

FAKE_ISOS = [
    {"id": 1, "name": "ALphoenixa-OS-1.0.iso", "size_mb": 1850},
    {"id": 2, "name": "dstc-DOS-1.0.iso",       "size_mb": 620},
    {"id": 3, "name": "Ubuntu-24.04-desktop.iso", "size_mb": 5200},
    {"id": 4, "name": "Debian-12-netinst.iso",  "size_mb": 660},
    {"id": 5, "name": "custom-image.iso (browse...)", "size_mb": None},
]


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    print("=" * 52)
    print(f"  {APP_NAME} v{VERSION}  —  Simulated ISO/USB Burner")
    print("  Part of the ALphoenixa OS / dstc project")
    print("=" * 52)
    print()
    print("  NOTE: This is a 100% SIMULATED tool.")
    print("  No real disk, drive, or file is ever touched.")
    print()


def choose_from(prompt, items, label_key):
    print(prompt)
    for item in items:
        extra = f" ({item['size_mb']} MB)" if items is FAKE_ISOS and item.get("size_mb") else ""
        print(f"  [{item['id']}] {item[label_key]}{extra}")
    print()
    while True:
        choice = input("Enter number: ").strip()
        for item in items:
            if choice == str(item["id"]):
                return item
        print("Invalid choice, try again.")


def fake_checksum(length=64):
    chars = string.hexdigits.lower()[:16]
    return "".join(random.choice(chars) for _ in range(length))


def progress_bar(total_steps=40, label="Writing image"):
    print()
    for i in range(total_steps + 1):
        pct = int((i / total_steps) * 100)
        filled = int((i / total_steps) * 30)
        bar = "#" * filled + "-" * (30 - filled)
        sys.stdout.write(f"\r  {label}: [{bar}] {pct:3d}%")
        sys.stdout.flush()
        time.sleep(0.05 + random.uniform(0, 0.03))
    print()


def confirm(prompt):
    answer = input(f"{prompt} (y/n): ").strip().lower()
    return answer in ("y", "yes")


def main():
    clear_screen()
    banner()

    iso = choose_from("Select an OS image to burn:", FAKE_ISOS, "name")
    print(f"\nSelected image: {iso['name']}\n")

    drive = choose_from("Select a target USB drive:", FAKE_DRIVES, "label")
    print(f"\nSelected drive: {drive['label']} ({drive['device']}, {drive['size_gb']} GB)\n")

    print("!" * 52)
    print(f"  WARNING: In a real burner tool, this step would")
    print(f"  ERASE ALL DATA on '{drive['label']}'.")
    print(f"  This is a SIMULATION -- nothing will actually happen.")
    print("!" * 52)
    print()

    if not confirm(f"Proceed with simulated burn of '{iso['name']}' to '{drive['label']}'?"):
        print("\nOperation cancelled. No changes were made (simulation).")
        return

    print("\nStep 1/3: Preparing image...")
    progress_bar(20, "Preparing")

    print("\nStep 2/3: Writing to simulated device...")
    progress_bar(50, "Writing image")

    print("\nStep 3/3: Verifying write...")
    progress_bar(25, "Verifying")

    checksum = fake_checksum()
    print()
    print("=" * 52)
    print("  BURN COMPLETE (simulated)")
    print(f"  Image:     {iso['name']}")
    print(f"  Target:    {drive['label']} ({drive['device']})")
    print(f"  Checksum:  {checksum}  (simulated, not a real hash)")
    print("=" * 52)
    print()
    print("  Reminder: this tool never touched any real hardware.")
    print("  For a real USB burner, use tools like Rufus, Ventoy,")
    print("  or 'dd' on Linux (with real caution).")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user. No changes were made (simulation).")
