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

# TO DO
# 1.  Add a function to list all recipients in a database entry.
# 2.  Add a function to pretty-print a database entry.  Use #16.
# 5.  Add a function to merge database pickles.  Add a CLI argument.
# 7.  Add a function to identify list posts.
# 8.  Add a function to prioritize deletions.
# 9.  Need to expand file names in case not called from shell.
# 10. Add functionality to migrate database schema.
# 11. Reorganize imports to separate library functionality from reporting,
#     testing, and debugging infrastructure.
# 12. It's hard to see how the database can be reliably updated with additions
#     to a mailbox because addition to mailbox isn't timestamped.  It makes
#     sense to use a database other than a dictionary only if it's
#     significantly faster.  For debug purposes it's worth saving to a pickle,
#     but maybe the contortions in find_and_load_pickle are unnecessary.
#     Refactor to emphasize the "one pass" use cases?
# 13. Need to check for the case of no pickle and no input files?
# 14. Refactor argument parser to distinguish the default "keep" mailbox, and
#     present the "k(eep), m(ove to duplicates), d(elete)" dialog efficiently.
# 15. Refactor database entries to use namedtuple?
# 16. Add functionality to pretty-print database entries field by field for
#     easy comparison.  Use these to implement #2.

# Code

import argparse
from collections import Counter
import email
import email.parser
from email.contentmanager import raw_data_manager
import email.policy
from hashlib import sha1
import mailbox
import os
import os.path
import pickle

def summarize_database(db):
    print(len(db.get('missing-message-id@turnbull.sk.tsukuba.ac.jp',())),
          'missing ID')
    duplicate = hash_mismatch = bodyless = 0
    ld = Counter((v['bodylength'] for vs in db.values() for v in vs))
    print(len(ld), 'unique body lengths; min', min(ld.keys()),
          'max', max(ld.keys()))
    for key, values in db.items():
        if len(values) > 1:
            duplicate += 1
        hashes = []
        for v in values:
            hashes.append(v['bodyhash'])
            bodyless += 1 if v['bodyhash'] is None else 0
        for h in hashes:
            if h != hashes[0]:
                hash_mismatch += 1
                #print('Message', key, 'body hashes vary')
                break
    print(hash_mismatch, 'hash mismatches and', end=' ')
    print(duplicate, 'duplicates out of', len(db), 'unique message IDs')
    print(bodyless, 'lacking body')


NoneDigest = sha1(b'').digest()
def get_hash(msg):
    body = msg.get_body(('related', 'plain', 'html'))
    # .get_body is idempotent when applied twice with same restriction.
    body = msg.get_body(('plain', 'html'))
    content = body.get_content()
    if isinstance(content, (bytes, str)):
        content = content.strip()
        length = len(content)
        if isinstance(content, str):
            content = content.encode('utf8', errors='surrogateescape')
        sha = sha1(content).digest()
    else:
        print('content type is', body.get_content_type(),
              'in', msg['message-id'] or 'message with no id')
        length = 0
        sha = NoneDigest
    return (sha, length)


# #### db should be a class and process_mailbox a method
def process_mailbox(path, db, get_mailbox=mailbox.mbox):
    if os.path.isdir(path):
        raise IsADirectoryError(path)
    myerrors = {}
    box = get_mailbox(path, create=False) # #### Probably raises on empty path.
    for key in box.iterkeys():
        try:
            msgid = 'unparsed-message-id@turnbull.sk.tsukuba.ac.jp'
            parser = email.parser.BytesParser(policy=email.policy.default)
            msg = parser.parse(box.get_file(key))
            msgid = msg['message-id']
            if not msgid:         # could be None or '' #### or ' '?            
                msgid = 'missing-message-id@turnbull.sk.tsukuba.ac.jp'
            bodyhash, bodylength = get_hash(msg)
        except Exception as e:
            name = e.__class__.__name__
            item = (key, e.args, msgid)
            if name not in myerrors:
                myerrors[name] = [item]
            else:
                myerrors[name].append(item)
            continue

        d = { 'mailbox-path' : path,
              'unix-from' : msg.get_unixfrom(),
              'bodyhash' : bodyhash,
              'bodylength' : bodylength }
        for h in ('bcc', 'cc', 'date', 'from', 'message-id', 'to'):
            d[h] = msg.get_all(h)
        db[msgid] = value = db.get(msgid, [])
        value.append(d)

    for key, errlist in myerrors.items():
        print('skipped due to ', key, ': ', sep='')
        for err in errlist:
            print(' ', err[0], err[1], err[2])
    print('end skips')

def dump_pickle(database_info):
    outfile = database_info[1] or os.path.expanduser(database_info[2])
    if outfile:
        print('Saving pickle to', database_info[2])
        with open(outfile, mode='wb') as f:
            try:
                pickle.dump(database_info[0], f)
            except Exception as e:
                print('pickling failed:', e)
    else:
        print('There is no file to dump a pickle to.')

def find_and_load_pickle(path):
    """
    Load a pickle from PATH, and return a triple (database, fd, path).
    If the pickle is corrupt, returns an open temporary file for fd.
    Note: open(fd, ...) wraps the fd with a Python file stream.
    """

    db = {}
    # #### This still has a race condition.
    path = os.path.expanduser(path)
    if path is None or not os.path.exists(path):
        path = (None, path)
    else:
        try:
            with open(path, 'rb') as f:
                db = pickle.load(f)
            path = (None, path)
        except Exception:
            print('pickle', path, 'failed to load')
            import tempfile
            path = tempfile.mkstemp(suffix='-' + os.path.basename(path),
                                    dir=os.path.dirname(path))
            print('will save new database to pickle', path[1])
    return (db,) + path

# tests to add to main program
def test_pickle():
    tests = failures = 0
    filename = 'random.pck'
    while os.path.exists('/tmp/' + filename):
        filename = 'x' + filename
    filename = '/tmp/' + filename

    print('TESTING no file provided...')
    tests += 1
    result = find_and_load_pickle(None)
    print('RESULT:', result)
    if ({}, None, None) != result:
        print('handling new database:', filename, 'FAILED')
        failures += 1

    print('TESTING nonexistent file provided...')
    tests += 1
    result = find_and_load_pickle(filename)
    print('RESULT:', result)
    if ({}, None, filename) != result:
        print('handling new database:', filename, 'FAILED')
        failures += 1

    print('TESTING corrupt file provided...')
    tests += 1
    with open(filename, mode='wb') as f:
        f.write(b'}\x0a')
    result = find_and_load_pickle(filename)
    print('RESULT:', result)
    if ({} != result[0]
            or not isinstance(result[1], int)
            or not result[2].startswith('/tmp/')
            or not result[2].endswith('random.pck')):
        print('handling corrupt database:', filename, 'FAILED')
        failures += 1
    os.remove(filename)
    os.remove(result[2])

    print('TESTING valid file provided...')
    tests += 1
    with open(filename, mode='wb') as f:
        pickle.dump({'XXX': {'message-id': 'XXX'}}, f)
    result = find_and_load_pickle(filename)
    print('RESULT:', result)
    os.remove(filename)
    if {'XXX': {'message-id': 'XXX'}} != result[0]:
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
    parser.add_argument('mailboxes', type=str, nargs='*',
                        help='mailbox or directory containing mailboxes')
    parser.add_argument('--pickle', type=str, nargs='?',
                        const=os.path.expanduser('~/maildb.pck'),
                        help='Use PICKLE to save db.')
    # #### CONFIG is currently unused.
    parser.add_argument('--config', type=str, nargs='?',
                        # #### Figure out where the default CONFIG belongs.
                        const=os.path.expanduser('~/maildb.ini'),
                        help='Use CONFIG to configure this program.')
    args = parser.parse_args()

    db_info = find_and_load_pickle(args.pickle)
    print('db of length ', len(db_info[0]),
          ', ', db_info[1],
          ', ', db_info[2],
          sep='')
    db = db_info[0]
    for box in args.mailboxes:
        print('processing', box)
        process_mailbox(box, db)
    if args.mailboxes:
        dump_pickle(db_info)

    summarize_database(db)
