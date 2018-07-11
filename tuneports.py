#! /opt/local/bin/python3.6

# Intended for use with most recent version of MacPorts Python.
# Currently 3.6.1.
# This means that new features may be used.

"""
Manage information about installed ports.
Clean up inactive ports, by rule or interactively.
"""

from collections import Counter
import re
import subprocess

class PortDB:
    """
    In-memory database of installed MacPorts ports from ``port installed``.
    """

    # port installed output looks like
    # The following ports are currently installed:
    #   aalib @1.4rc5_5 (active)
    #   adns @1.5.0_0

    def __init__(self):
        proc = subprocess.run(["port", "installed"],
                              stdout=subprocess.PIPE,
                              encoding='utf-8')
        pname = "[-_.a-zA-Z0-9]+"
        vno = "\d*(?:[-.]\d+)*(?:[-.]?[a-zA-Z]+\d*)?"
        prev = "\d+"
        port_info_re = re.compile(
            fr"^  ({pname}) @({vno})_({prev})((?:\+{pname})*)\s*(\(active\))?$"
            )

        self.db = {}
        self.error_lines = []
        for line in proc.stdout.splitlines():
            m = port_info_re.match(line)
            if not m:
                self.error_lines.append(line)
                continue
            versions = self.db.get(m[1],[])
            versions.append((m[2], m[3], m[4], bool(m[5]))),
            self.db[m[1]] = versions

def test(ports, tests='all'):
    if tests == 'all':
        tests = ['stats', 'histogram', 'portlist']
    if 'stats' in tests:
        print("#errors =", len(ports.error_lines), "#ports =", len(ports.db))
        if len(ports.error_lines):
            it = iter(ports.error_lines)
            print("header:", next(it))
            for line in it:
                print(line)
    if 'histogram' in tests:
        histogram = Counter(len(versions) for versions in ports.db.values())
        print(len(histogram), min(histogram.keys()), max(histogram.keys()))

        for i in range(1,max(histogram.keys())+1):
            print(f"{histogram[i]}", end=" ")
        print()

    if 'portlist' in tests:
        for i, (port, versions) in enumerate(ports.db.items()):
            if i >= 10: break
            print("==", port)
            for version in versions:
                print(version)
    
if __name__ == '__main__':
    ports = PortDB()
    # test(ports)                # add argparse parser

    tasks = []
    cmd = ["sudo", "port", "uninstall", None, None]
    for i, (port, versions) in enumerate(ports.db.items()):
        prompt = []
        for version in versions:
            if version[3]:
                print(f"Skipping active version {version[:2]} of {port}")
            else:
                prompt.append(f"@{version[0]}_{version[1]}{version[2]}")
        if prompt:
            print(f"Delete these versions of {port}?\n{' '.join(prompt)}")
            confirm = input("y/n/q? ")[0].lower()
            if confirm == 'q':
                break
            elif confirm == 'y':
                for version in prompt:
                    cmd[-2:] = port, version
                    tasks.append(cmd[:])

    for cmd in tasks:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, encoding='utf-8')
        print(proc.stdout, end='')

    plural = "s" if i > 1 else ""
    print(f"{i} port{plural} processed.")

