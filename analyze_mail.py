TODO = "mpps.math.hw"
HELP = "mpps.math.help"
DONE = "mpps.math.hw.parsed"

from mailbox import mbox
from email.utils import getaddresses, parseaddr
from email.header import Header, decode_header
import os.path
import pickle
import re
from collections import defaultdict

stidre = re.compile(r'201\d{6}')
stidaddrre = re.compile(r's(1\d{6})@(u|sk)\.tsukuba\.ac\.jp')
hwre = re.compile(r'(?i)(?:homework|hw)\s*(?:no\.?|#)?\s*(\d|one|two|three|four|five|six|seven|eight)(?:\D|$)')

extension_type_map = {
    'xlsx' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'bin' : 'application/octet-stream',
    'png' : 'image/png',
    'jpg' : 'image/jpg',
    'gif' : 'image/gif',
    }

class Student:

    sidmap = {}
    addrmap = {}
    student_list = []
    initialized = False

    @classmethod
    def attach_db(cls):
        if not Student.initialized and os.path.exists('student_db.pck'):
            with open('student_db.pck', 'rb') as f:
                Student.student_list, Student.sidmap, Student.addrmap = pickle.load(f)
        Student.initialized = True

    @classmethod
    def commit_db(cls):
        if Student.initialized:
            with open('student_db.pck', 'wb') as f:
                db = (Student.student_list, Student.sidmap, Student.addrmap)
                pickle.dump(db, f)

    def __init__(self):
        self.student_id = None
        self.name = None
        self.aliases = set()
        self.primary_address = None
        self.other_addresses = set()
        self.homework = set()

    def __str__(self):
        hs = list(self.homework)
        hs.sort()
        return "{} <{}> {} {}".format(self.name, self.primary_address,
                                      self.student_id, hs)

    def add_name(self, name, primary=False):
        if self.name is None:
            self.name = name
        elif primary:
            self.aliases.add(self.name)
            self.name = name
        else:
            self.aliases.add(name)

    def add_address(self, addr, primary=False):
        if self.primary_address is None:
            self.primary_address = addr
        elif primary:
            self.other_addresses.add(self.primary_address)
            self.primary_address = addr
        else:
            self.other_addresses.add(addr)

    def add_student_id(self, idno):
        self.student_id = idno

    def add_homework(self, hw):
        self.homework.update(hw)

def update_student(name=None, addr=None, sid=None, hw=None):
    if sid and sid in Student.sidmap:
        student = Student.sidmap[sid]
    elif addr and addr in Student.addrmap:
        student = Student.addrmap[addr]
    else:
        student = Student()
        Student.student_list.append(student)
        if sid:
            Student.sidmap[sid] = student
        if addr:
            Student.addrmap[addr] = student

    if name:
        student.add_name(name)
    if addr:
        student.add_address(addr)
    if sid:
        student.add_student_id(sid)
    if hw:
        student.add_homework(hw)


def decode_value(s):
    ss = decode_header(s)
    s = []
    for b, cs in ss:
        if isinstance(b, str):
            s.append(b)
        elif cs is None:
            s.append(b.decode('latin-1', errors='replace'))
        else:
            s.append(b.decode(cs, errors='replace'))
    return ''.join(s)

# #### Use walker here.
def print_payload_text(msg, size=1000):
    if msg.get_content_type() == 'text/plain':
        cs = msg.get_content_charset() or 'ascii'
        p = msg.get_payload(decode=True).decode(cs, errors='backslashreplace')
        print(p[:size])
    elif msg.is_multipart():
        for m in msg.get_payload():
            print_payload_text(m, size)
    else:
        print(msg.get_content_type())

def regex_search(m, matches, nesting):
    """
    Walker for walk_message.
    matches[0] contains the regular expression (may be compiled).
    matches[1:] is the list of matches.
    """

    if m.get_content_maintype() == 'text':
        cs = m.get_content_charset() or 'ascii'
        p = m.get_payload(decode=True).decode(cs, errors='backslashreplace')
        matches.extend(re.findall(matches[0], p))

def print_content_type(m, external_only, nesting):
    ct = m.get_content_type()
    if not external_only or not ct.startswith('text') and not m.is_multipart():
        print(" " * nesting, ct, sep='')

# There may be some way to maintain state in the iteration, and so have
# the agent *return* (rather than "maintain") the state, but it would be
# complicated.  Therefore to have an "active" state (changing as the
# message is walked), state must be mutable.  "Passive" state (set from
# outside the walker and not changed during the walk) can be useful, and in
# that case state could be an immutable object other than None.
def walk_message(msg, agent, state=None, nesting=0):
    """
    Walk a message structure, performing an action on each part.

    msg         the message to walk
    agent       a callable taking a message, a state, and the nesting level;
                the return value, if any, is ignored
    state       an arbitrary object, maintained by the agent, or None
    nesting     the nesting level, maintained by the walker

    Typically state will be mutable.  The agent must set it before returning.
    """

    agent(msg, state, nesting)
    if msg.is_multipart():
        for m in msg.get_payload():
            walk_message(m, agent, state, nesting + 1)

def parse_message(msg, check_content=False):
    subject = decode_value(msg['subject']).strip()
    name, addr = parseaddr(msg['from'])
    name = decode_value(name)

    matches = re.findall(stidre, subject)
    matches.insert(0, stidre)       # see regex_search
    walk_message(msg, regex_search, matches)
    matches = matches[1:]
    sids = set(matches)
    if len(sids):
        sid = sids.pop()
    else:
        sid = None
    if len(sids) > 1:
        print(sids)
    if sid is None:
        print(addr)
        sid = stidaddrre.match(addr)
        if sid:
            sid = '20' + sid.group(1)

    hws = re.findall(hwre, subject)
    hws.insert(0, hwre)             # see regex_search
    walk_message(msg, regex_search, hws)
    hws = hws[1:]
    if not hws:
        walk_message(msg, print_content_type, True)
    if check_content and not hws:
        print_payload_text(msg, 1000)
        hws = []
        if sid is None:
            print('NO ID')
        elif sid in Student.sidmap:
            print(sid, Student.sidmap[sid].homework)
        else:
            print(sid)
        s = input('Enter hw number (empty to stop): ')
        while s:
            hws.append(s)
            s = input('Enter hw number (empty to stop): ')
    return name, addr, sid, hws


def auto_parse_all(mb):
    for key, msg in mb.iteritems():
        subject = decode_value(msg['subject']).strip()
        if subject.startswith('[Spam]'):
            continue
        update_student(*parse_message(msg))

def parse_and_move(todo, done):
    donekeys = []
    try:
        for key, msg in todo.iteritems():
            subject = decode_value(msg['subject']).strip()
            if subject.startswith('[Spam]'):
                continue
            name, addr, sid, hws = parse_message(msg, check_content=True)
            if not sid and addr in Student.addrmap:
                sid = Student.addrmap[addr].student_id

            update_student(name=name, addr=addr, sid=sid, hw=hws)
            if (hws and sid) or name == "Koki TAKAYAMA":
                # This message has been fully parsed.
                done.add(msg)
                donekeys.append(key) 

    finally:
        print("donekeys =", donekeys)
        for key in donekeys:
            todo.remove(key)

def main():
    Student.attach_db()
    todo = mbox(TODO)
    done = mbox(DONE)

    #auto_parse_all(done)
    parse_and_move(todo, done)

    Student.commit_db()
    todo.close()
    done.close()

    print([str(s) for s in Student.student_list if s.student_id is None])
    all = set(Student.sidmap.values())
    for s in Student.addrmap.values():
        all.add(s)
    print(len(Student.sidmap), len(Student.addrmap), len(all))

    for s in Student.student_list:
        print(s)

if __name__ == '__main__':
    main()
