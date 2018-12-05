#! /opt/local/bin/python3.6

# maildb
#
# Copyright 2018 Stephen J. Turnbull
#
# This file is licensed to you under the Academic Free License v2.1 or
# later, at your option.  (Note that the Python Software Foundation
# Contributor Agreement currently specifies *exactly* v2.1.  I don't
# think this matters to you even if you want to contribute to Python,
# because AFL is not "copyleft".  But if you worry about that kind of
# thing, ask a lawyer.)
#
# If you do use code from this file or import it, I would appreciate
# being given credit in your documentation (including header comments
# like this one).  That's not a license condition, it's just an ask.

# This program takes a set of mbox files or directories full of mbox
# files, and indexes the messages in them.

import argparse
import email
from mailbox import mbox
import os
import os.path
import pickle
import tempfile

# Code

# #### db should be a class and process_mailbox a method
def process_mailbox(path, db, cls=mailbox.mbox):
    if os.path.isdir(path):
        raise IsADirectoryError(path)
    box = cls(path, create=False)       # #### Probably raises.
    for m in box:
        msgid = m['message-id']
        if not msgid:         # could be None or "" #### or " "?            
            msgid = "fake-message-id@turnbull.sk.tsukuba.ac.jp"
        d = {'mailbox-path' : path}
        for h in ('bcc', 'cc', 'date', 'from', 'message-id', 'to'):
            d[h] = m.get_all(h)
        db[msgid] = db.get(msgid, []).append(d)

def find_and_load_pickle(path):
    db = {}
    # #### This still has a race condition.
    if path is not None and os.path.exists(path):
        try:
            with open(path, 'rb') as f:
                db = pickle.load(f)
            path = (None, path)
        except Exception:
            print('pickle', path, 'failed to load')
            path = tempfile.mkstemp(suffix='-' + os.path.basename(path),
                                    dir=os.path.dirname(path))
            print('will save new database to pickle', path[1])
    else:
        path = (None, path)
    return (db,) + path

# tests to add to main program
def test_pickle():
    tests = failures = 0
    filename = 'random.pck'
    while os.path.exists('/tmp/' + filename):
        filename = 'x' + filename
    filename = '/tmp/' + filename

    print("TESTING no file provided...")
    tests += 1
    result = find_and_load_pickle(None)
    print("RESULT:", result)
    if ({}, None, None) != result:
        print('handling new database:', filename, 'FAILED')
        failures += 1

    print("TESTING nonexistent file provided...")
    tests += 1
    result = find_and_load_pickle(filename)
    print("RESULT:", result)
    if ({}, None, filename) != result:
        print('handling new database:', filename, 'FAILED')
        failures += 1

    print("TESTING corrupt file provided...")
    tests += 1
    with open(filename, mode='wb') as f:
        f.write(b'}\x0a')
    result = find_and_load_pickle(filename)
    print("RESULT:", result)
    if ({} != result[0]
            or not isinstance(result[1], int)
            or not result[2].startswith('/tmp/')
            or not result[2].endswith('random.pck')):
        print('handling corrupt database:', filename, 'FAILED')
        failures += 1
    os.remove(filename)
    os.remove(result[2])

    print("TESTING valid file provided...")
    tests += 1
    with open(filename, mode='wb') as f:
        pickle.dump({"XXX": {"message-id": "XXX"}}, f)
    result = find_and_load_pickle(filename)
    print("RESULT:", result)
    os.remove(filename)
    if {"XXX": {"message-id": "XXX"}} != result[0]:
        print('handling existing database:', filename, 'FAILED')
        failures += 1

    if failures == 0:
        print('All', tests, 'test_pickle tests succeeded!')
    else:
        print(failures, 'of', tests, 'test_pickle tests failed!') 
        

def test_parser():
    print('mailboxes\t', args.mailboxes,
          '\ndatabase pickle\t', args.pickle,
          '\nconfiguration file\t', args.config)

# main program
if __name__ == '__main__':
    # get the mailboxes
    parser = argparse.ArgumentParser(description='Index mailboxes.')
    parser.add_argument('mailboxes', type=str, nargs='+',
                        help='mailbox or directory containing mailboxes')
    parser.add_argument('--pickle', type=str, nargs='?',
                        const='~/maildb.pck',
                        help='Use PICKLE to save db.')
    # #### CONFIG is currently unused.
    parser.add_argument('--config', type=str, nargs='?',
                        # #### Figure out where the default CONFIG belongs.
                        const='~/maildb.ini',
                        help='Use CONFIG to configure this program.')
    args = parser.parse_args()

    test_pickle()
