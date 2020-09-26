# splitmbox

# Copyright 2019 Stephen J. Turnbull
# Version 1.0
# October 23, 2019

# compatible with Python 3.7

# TODO
# 1.  Make .d dir if necessary and put splits there.
# 2.  Resplit.
# 3.  More flexible seasonality.
# 4.  Handle dates like 'Thu, 10 Oct 2019 00:36 +0200'.

from mailbox import mbox
import re

# Not sure about standard spacing of dates, but some implementations
# definitely produce only one column for single-digit days.  Just in
# case, treat hours the same, allowing '1', '01', or ' 1'.
# Weekday made optional.
# #### Possibly offset should be more flexible (optional, allow TZ, etc).
# #### What's "Fri, 16 Nov 29 16:14:17 +0900"?  From Received, it's Heisei 29.
RFC822_DATE_RE = re.compile(r'(?:(\w{3}), )?((?:\d| )?\d) (\w{3}) (\d{4})'
                            r' ((?:\d| )?\d):(\d\d):(\d\d) ([-+]\d{4})')
MONTHS = 'jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec'.split(',')

def m2n(s):
    s = s.lower()
    if s in MONTHS:
        return MONTHS.index(s) + 1
    else:
        return None

def tuple_from_RFC822_date(field):
    m = RFC822_DATE_RE.match(field)
    return (m.group(1),
            int(m.group(2)),
            m2n(m.group(3)),
            int(m.group(4)),
            int(m.group(5)),
            int(m.group(6)),
            int(m.group(7)),
            int(m.group(8))) if m else None

def split_by_date(path, frequency):
    """
    Split a mailbox by date, ignoring thread dates.
    path         filesystem path to the mailbox
    frequency    one of 'annual', 'quarterly', 'monthly'
    The mailbox will be split into parts named <path>.yyyyXnn, where
    yyyy is a 4-digit year, Xnn is not used for annual splits, and
    for quarterly splits is Q1..Q4, for monthly splits is M01..M12.
    """

    if frequency == 'annual':
        divisor = 0
        fmt = '{path}.{year}'
    elif frequency == 'quarterly':
        divisor = 3
        fmt = '{path}.{year}Q{quarter}'
    elif frequency == 'monthly':
        fmt = '{path}.{year}M{month}'
    else:
        raise RuntimeError(f'invalid frequency ({frequency})')

    box = mbox(path)
    boxes = {}
    for msg in box:
        d = tuple_from_RFC822_date(msg['date'])
        if d is None:
            print(f"Nonstandard date: {msg['date']}")
            # Add to current thisbox.
            thisbox.add(msg)
            continue
        # ignoring effect of offsets
        quarter = (d[2] - 1) // 3 + 1
        boxpath = fmt.format(path=path, year=d[3], month=d[2], quarter=quarter)

        # #### Can do this with .get() or defaultdict, I think.
        if boxpath not in boxes:
            thisbox = mbox(boxpath)
            thisbox.lock()
            boxes[boxpath] = thisbox
        else:
            thisbox = boxes[boxpath]
        thisbox.add(msg)

    for b in sorted(list(boxes.keys())):
        print(b)
        boxes[b].close()
