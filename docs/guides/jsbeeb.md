# Printing from jsbeeb

jsbeeb cannot print to Papyrium. It shows what its BBC Micro prints as
text in a window (Alt-B), and that text has lost the bytes the BBC sent:
line endings are changed and control codes are gone. A browser page also
cannot open a TCP connection or write a file of its choosing.

`docs/emulators/jsbeeb.md` describes jsbeeb's printer, as read from its
source, and the changes to jsbeeb that would let it reach Papyrium.
