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
import email.parser
import email.policy
import mailbox
import os
import os.path
import pickle

# TO DO
# 1.  Add a function to list all recipients in a database entry.
# 2.  Add a function to pretty-print a database entry.
# 4.  Add a function to hash the payload.  Add a field to the database.
# 5.  Add a function to merge database pickles.  Add a CLI argument.
# 7.  Add a function to identify list posts.
# 8.  Add a function to prioritize deletions.
# 9.  Need to expand file names in case not called from shell.
# 10. Add functionality to migrate database schema.

# Code

def summarize_database(db):
    print(len(db['missing-message-id@turnbull.sk.tsukuba.ac.jp']),
          'missing ID')
    duplicates = 0
    bodyless = 0
    for i, (key, values) in enumerate(db.items()):
        if len(values) > 1:
            duplicates += 1
        for v in values:
            bodyless += v['lacks-body']
    print(duplicates, 'duplicates out of', i, 'unique message IDs')
    print(bodyless, 'lacking body')

# #### db should be a class and process_mailbox a method
def process_mailbox(path, db, cls=mailbox.mbox):
    if os.path.isdir(path):
        raise IsADirectoryError(path)
    errors = [[], []]
    box = cls(path, create=False)       # #### Probably raises.
    parser = email.parser.BytesParser(policy=email.policy.default)
    for k in box.iterkeys():
        try:
            msgid = 'unparsed-message-id@turnbull.sk.tsukuba.ac.jp'
            m = parser.parse(box.get_file(k))
            msgid = m['message-id']
            if not msgid:         # could be None or '' #### or ' '?            
                msgid = 'missing-message-id@turnbull.sk.tsukuba.ac.jp'
            lacks_body = True if m.get_body() is None else False
        except UnicodeDecodeError:
            errors[0].append((k, msgid))
            continue
        except Exception:
            errors[1].append((k, msgid))
            continue

        d = { 'mailbox-path' : path,
              'unix-from' : m.get_unixfrom(),
              'lacks-body' : lacks_body }
        for h in ('bcc', 'cc', 'date', 'from', 'message-id', 'to'):
            d[h] = m.get_all(h)
        db[msgid] = value = db.get(msgid, [])
        value.append(d)

    print('skipped due to UnicodeDecodeError:')
    for msgid in errors[0]:
        print(' ', msgid)
    print('skipped due to other Exceptions:')
    for msgid in errors[1]:
        print(' ', msgid)
    print('end skips')

def dump_pickle(database_info):
    outfile = database_info[1] or database_info[2]
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
    if path is not None and os.path.exists(path):
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
    db = db_info[0]
    for box in args.mailboxes:
        print('processing', box)
        process_mailbox(box, db)
    dump_pickle(db_info)

    summarize_database(db)
