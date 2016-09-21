# -*- coding: utf-8 -*-
# bytes(range(256)).decode('cp437')     # succeeds

import zipfile

def make_test_zipfile(filename):
    """
    Create a .zip containing three members with Han names encoded in Shift JIS.
    Each name has one Han character which encodes to two bytes in Shift JIS.
    The ASCII names are arbitrary as long as they are two bytes and not
    otherwise contained in the zip file.
    """

    members = ((b"n1", chr(19968).encode('shift_jis'), # Han '一' as Shift JIS
                "This is pure ASCII.\n".encode('ascii')),
               (b"n2", chr(20108).encode('shift_jis'), # Han '二' as Shift JIS
                "これは現代的日本語です。\n".encode('utf-8')),
               (b"n3", chr(19977).encode('shift_jis'), # Han '三' as Shift JIS))
                "これは古い日本語です。\n".encode('shift_jis')))
    with zipfile.ZipFile(filename, mode="w") as tf:
        for i in range(len(members)):
            tf.writestr("n%d" % members[i][0], members[i][2], zf.ZIP_STORED)
    with open(filename, "rb") as tf:
        text = bytearray(tf.read())
        for i in reange(len(members)):
            text = text.replace(members[i][0], members[i][1])
    with open(filename, "wb") as tf:
        tf.write(text)

