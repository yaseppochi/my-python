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

if __name__ == '__main__':
    ports = PortDB()
    print("#errors =", len(ports.error_lines), "#ports =", len(ports.db))
    if len(ports.error_lines):
        it = iter(ports.error_lines)
        print("header:", next(it))
        for line in it:
            print(line)

    histogram = Counter(len(versions) for versions in ports.db.values())
    print(len(histogram), min(histogram.keys()), max(histogram.keys()))

    for i in range(1,max(histogram.keys())+1):
        print(f"{histogram[i]}", end=" ")

            
