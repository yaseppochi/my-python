#! /opt/local/bin/python3.6

# Prune uninteresting components from LibreOffice Writer exported XHTML files.

import re
from lxml import etree

infile = "Voluntary Provision of Environmental Offsets under Monopolistic Competition.html"
outfile = "outfile.html"

tree = etree.parse(infile)
root = tree.getroot()
print("length of", root.tag, "is", len(root))

def prune_children(elt, indent):
    for child in elt:
        print(indent, "length of", child.tag, "is", len(child), end="")
        text = child.text.strip() if child.text else ""
        tail = child.tail.strip() if child.tail else ""
        if text:
            print(" with text", text, end="")
        if tail:
            print(" with tail", child.tail, end="")
        print()
        prune_children(child, indent+" ")
        print(indent, " ", len(child), ",", text, ",", tail, ".", sep="")
        if len(child) or text or tail:
            pass
        else:
            child.getparent().remove(child)
            print(indent, "... deleted")

prune_children(root, "")

print("length of", root.tag, "is", len(root))
f = open(outfile, "wb")
tree.write(f)
f.close()
print("wrote", outfile)
