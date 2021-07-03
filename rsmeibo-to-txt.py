import csv
import datetime
from glob import glob
from os import stat

today = datetime.date.today()
ay = today.year - (1 if today.month < 4 else 0)
meibo = [(stat(f).st_ctime, f) for f in glob('RSMeibo_' + str(ay) + '*')]
meibo.sort(reverse=True)
print(*meibo, sep='\n')
meibo = meibo[0][1]

with open(meibo) as f:
    reader = csv.reader(f)
    for i in range(3):
        next(reader)
    meibo = []
    for row in reader:
        meibo.append(row[2:6])
    with open("maillist.txt", "w") as f:
        for row in meibo[1:]:
            print('"{0:s}" <s{1:s}@u.tsukuba.ac.jp>'.format(row[2], row[1][2:9]),
                  file=f)
    with open("meibo.txt", "w") as f:
        for row in meibo:
            print("{:9} {:1} {}\t{}\t".format(row[1], row[0], row[2], row[3]),
                  file=f)
    with open("meibo.csv", "w") as f:
        for row in meibo:
            print("{},{},{},{}".format(row[1], row[0], row[2], row[3]),
                  file=f)

