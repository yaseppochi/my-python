from analyze_mail import Student
import csv

OUTPUT = 'homework_db.csv'
MEIBO = 'RSMeibo_2016_01CN101.csv'

output_field_names = [
    "registered",
    "student id",
    "name",
    "reading",
    "display name",
    "address",
    "hw1",
    "hw2",
    "hw3",
    "hw4",
    "hw5",
    "hw6",
    "hw7",
    "hw8",
    ]

meibo_field_names = [
    "No.",                              # 1
    "学生所属",                         # 2
    "年次",                             # 3
    "学籍番号",                         # 4
    "氏名",                             # 5
    "氏名カナ",                         # 6
    # ... skip 15 empty columns (not even headers)
    "履修科目番号",                     # 22
    "備考",                             # 23
    ]

meibomap = {}
with open(MEIBO, 'r', encoding='utf-8') as f:
    for i in range(4):
        f.readline()
    rdr = csv.reader(f)
    for row in rdr:
        sid = row[3]
        name = row[4]
        yomi = row[5]
        meibomap[sid] = (name, yomi)

Student.attach_db()

with open(OUTPUT, 'w', encoding='utf-8') as f:
    print(','.join('"{}"'.format(field) for field in output_field_names),
          file=f)
    for s in Student.student_list:
        sid = s.student_id
        if sid is None:
            print("Can't join, no ID:", s)
            continue
        if sid in meibomap:
            name, yomi = meibomap[sid]
            registered = 1
        else:
            name = yomi = ''
            registered = 0

        print(registered, end=',"', file=f)
        print(sid, name, yomi, s.name, s.primary_address,
              sep='","', end='"', file=f)
        for i in range(1,9):
            print(',', 1 if str(i) in s.homework else 0, sep='', end='',file=f)
        print(file=f)
