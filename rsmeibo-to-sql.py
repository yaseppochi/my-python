# requires Python >= 3.6 for f-strings

# Not sure what's going on, maybe direct access to MySQL db doesn't work now?
# Need to use ImportUsers extension?  Does that work?  I don't remember....

import csv
import datetime
import glob

today = datetime.date.today()
ay = today.year - (1 if today.month < 4 else 0)

csv_files = glob.glob(f"RSMeibo_{ay}_*.csv")
# 2017: "RSMeibo_2017_FH11011.csv
# 2016: "RSMeibo_2016_FH11011.csv", "RSMeibo_2016_FH61041.csv"
print(csv_files)

meibo = []
ids = set()

for fn in csv_files:
    with open(fn) as f:
        reader = csv.reader(f)
        for i in range(3):
            next(reader)
        for row in reader:
            if row[3] in ids:
                print("Note: {} from {} already added to list.".format(row[3], fn))
            else:
                ids.add(row[3])
                meibo.append(row[2:6])
# Example student
meibo.append(["99","199954321","有座 例","ユーザ レイ"])

with open("maillist", "w") as f:
    for row in meibo[1:]:
        # was "u.tsukuba.ac.jp" in 2016 and earlier
        print(f'"{row[2]}" <s{row[1][2:9]}@u.tsukuba.ac.jp>', file=f)

with open("meibo", "w") as f:
    for row in meibo:
        print(row[1:] + row[:1], file=f)

password_map = {"199954321" : "199954321"}
fake_password = "This\tis\tnot\tthe\tpassword\tyou're\tlooking\tfor."
with open("社工専門英語・社会工学英語未登録者.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)                        # skip header
    for row in reader:
        if row[0]:
            if row[0] in password_map:
                print(f"{row[0]} already in group map.")
            password_map[row[0]] = fake_password
        if row[3]:
            if row[3] in password_map:
                print(f"{row[3]} already in group map.")
            password_map[row[3]] = row[3]

print(f"Password map ({len(password_map)} items)")
for row in password_map.items():
    print(row)
print("Password map done")

# NOTE: Idiot Mediawiki insists on user names being capitalized.
#   So if we insert user names that start with lower case, it bitches that
#   they don't exist in either capitalization.  Arrgh.
#   OTOH, capitalization doesn't matter when logging in.  *sigh*
# Old passwords (MD5) will be accepted on login, but new passwords will be
#   saved as PBKDF2.
# Don't know if user_password field needs to be populated.  I'm guessing it's
#   ignored.
# user_touched field must be populated, or the comparison fails and Mediawiki
#   throws an InternalError.
fmt = "".join(["INSERT `user` SET user_newpassword = ",
               "CONCAT(':B:35942d3d:', MD5(CONCAT('35942d3d-', MD5('{}')))), ",
               "user_password = ",
               "CONCAT(':B:35942d3d:', MD5(CONCAT('35942d3d-', MD5('{}')))), ",
               "user_name = 'S{}', user_real_name='{}', ",
               "user_email = 's{}@u.tsukuba.ac.jp',",
               "user_touched = '{}';",
               ])

# Temporary code due to in-development fails.
with open("wikiusers.sql", "w") as f:
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    for row in meibo[1:]:
        id9 = row[1]
        id7 = id9[2:]
        pwd = password_map[id9]
        print(fmt.format(pwd, pwd, id7, row[2], id7, stamp), file=f)
    print("UPDATE `user` SET user_email = 'turnbull.stephen.fw@tsukuba.ac.jp' "
          "WHERE user_name = 'S9954321';", file=f)

fmt = "".join(["UPDATE `user` SET user_email = 's{}@u.tsukuba.ac.jp' "
               "WHERE user_name = 'S{}';"
               ])
with open("updateusers.sql", "w") as f:
    for row in meibo[1:]:
        id7 = row[1][2:9]
        print(fmt.format(id7, id7), file=f)

with open("importusers.csv", "w") as f:
    for row in meibo[1:-1]:             # omit header and example user
        id9 = row[1]
        id7 = id9[2:]
        pwd = password_map[id9]
        if pwd != fake_password:
            print(f"S{id7},{pwd},s{id7}@u.tsukuba.ac.jp,{row[2]}", file=f)
    #print("S9954321,199954321,turnbull@sk.tsukuba.ac.jp,有座 例", file=f)
