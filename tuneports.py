#! /opt/local/bin/python3.6

# Intended for use with most recent version of MacPorts Python.
# Currently 3.6.1.
# This means that new features may be used.

"""
Manage information about installed ports.
Clean up inactive ports, by rule or interactively.
"""

import re

class PortDB:
    """
    In-memory database of installed MacPorts ports from ``port installed``.
    """

    # port installed output looks like
    # The following ports are currently installed:
    #   aalib @1.4rc5_5 (active)
    #   adns @1.5.0_0

    db = {}
    error_lines = []
    def __init__(self):
        proc = subprocess.run(["port", "installed"],
                              stdout=subprocess.PIPE,
                              encoding='utf-8')
        pname = "[-_.a-zA-Z0-9]+"
        vno = "\d+(?:.\d+)*"
        prev = "\d+"
        port_info_re = re.compile(
            fr"^  ({pname}) @({vno})_({prev})((?:\+{pname})*\s*(\(active\))$"
            )
        for line in proc.stdout.splitlines():
            m = port_info_re.match(line)
            if not m:
                error_lines.append(line)
                continue
            versions = db.get(m[1],[]).append((m[2], m[3], m[4], bool(m[5])))
            db[m[0]] = versions
