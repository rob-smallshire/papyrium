# Epson FX-80 behaviour notes

Facts about the FX-80 that Papyrium's `escp` language and `epson-fx80`
model rely on, restated in our own words from Epson's *FX Series Printer
User's Manual* (1984): Volume 1, Tutorial (T) and Volume 2, Reference (R).
Page numbers are the printed ones. The manuals themselves are copyrighted
and are kept, uncommitted, in `docs/local/`.

## Factory settings and DIP switches (R 295-299)

| Switch | Factory | Meaning |
|---|---|---|
| 1-1 | off | Power on in pica (on: condensed) |
| 1-2 | off | Plain zero (on: slashed zero; the font's U+0030 U+0338 glyph) |
| 1-3 | off | Paper-out sensor active |
| 1-4 | off | The 2K RAM holds user-defined characters (on: a text buffer) |
| 1-5 | off | Single strike (on: emphasized by default; beats 1-1) |
| 1-6..1-8 | on, on, on | International set: USA (Japan cannot be chosen by switch) |
| 2-1 | on | Printer always selected; DC1 and DC3 are ignored |
| 2-2 | on | Beeper sounds |
| 2-3 | off | No skip-over-perforation (on: skip one inch at the bottom of each form) |
| 2-4 | off | CR only (on: every CR also feeds a line) |

Power-on state: pica, margins 0 and 80, 1/6 inch line spacing, form
length 66 lines (11 inches), horizontal tabs every 8 pica columns,
vertical tabs every other line (12-dot spacing) in channel 0, USA set,
bidirectional printing.

## Top of form (T 32, T 104-105; R 296)

The top of form is wherever the paper is when the printer is switched on,
when `ESC @` arrives, or when either form of `ESC C` arrives. The user is
told to wind a perforation to the top of the ribbon before switching on,
so that the first line prints just below the perforation; the manual
gives no exact distance.

Papyrium models this with the FX-80's `top-offset` option, the distance
from the perforation to the top of the first line, 1/2 inch by default:
three lines, so that on listing paper the first line falls in the first
band and, on music-ruled paper, between its rules.

## Paper (T 23-24; R 327-328)

The built-in pin feed takes continuous paper 9.5 to 10 inches wide. The
standard 9.5-inch fanfold is 8.5-inch paper with a half-inch tear-off
strip of feed holes at each side. Cut sheets are 7.25 to 8.5 inches
wide, friction fed. Papyrium's default sheet is 9.5 by 11 inches (8.5 inches for the
`sheet` stationery, which has no strips), with
the 8-inch pica line centred across it (0.75 inch in from the edge); the
manual gives no exact head position.

## The print buffer

Text is collected in a one-line buffer that is printed by CR, LF, FF, VT,
`ESC J` or a full line. These also flush it first: BS, HT, SI, `ESC 4`,
`ESC R` and every graphics command (`ESC K/L/Y/Z/*/^`), which prints
everything before it and then its own data at once (R 271-280; T 144).

- CAN removes all text from the buffer; DEL removes the last character.
  Neither undoes control codes (T 46).
- `ESC @` clears the buffer without printing it, so text sent before the
  reset on the same line is lost; graphics already sent are not (T 144;
  R 275).
- `ESC Q` and `ESC l` clear the buffer as CAN does (T 118).
- `ESC -` does not flush the buffer (R 290).

## Reset (`ESC @`) (T 45, T 207; R 275)

Returns every mode to its power-on setting, sets the form length to 11
inches, makes the current line the top of form, cancels skip-over-
perforation, and erases all user-defined characters in RAM.

## Pitch and weight priorities (R 318-319)

Each mode has its own switch; when switches conflict the higher priority
wins and the lower is masked, not cancelled:
Elite > Proportional > Emphasized > Compressed > Pica.
Proportional characters always print emphasized. Super- and subscript
always print double-strike, and `ESC T` returns to whatever strike was
set before. Italic, underline and expanded combine with everything.

`ESC !` (Master Select) sets only pica/elite, compressed, emphasized,
double-strike and expanded: 16 combinations (bits 0, 2, 3, 4, 5). It
leaves italic, underline and script alone (T 73-76).

Expanded: `SO` lasts until the end of the line, DC4, or `ESC W 0`;
`ESC W 1` lasts until `ESC W 0` and is not cancelled by DC4 (R 272, 278).

## Underline (T 70)

The FX-80 underlines using the bottom pin one dot row below the lowest
row of any character (below the descenders), by feeding down, printing
the line and reversing. The FX-100 uses the ninth row itself.

## Margins (T 113-118; R 278, 280)

- `ESC l n`: left margin in columns of the current pitch, 0-78 pica, 0-93
  elite, 0-133 compressed. Invalid values are ignored.
- `ESC Q n`: right margin, 2-80 pica, 3-96 elite, 4-137 compressed; it
  must be at least 2 (pica), 3 (elite) or 4 (compressed) columns right
  of the left margin, else it is ignored.
- Both clear the text buffer and take effect from the next carriage
  return. Both restore the default horizontal tabs.
- Margins are absolute: changing pitch afterwards does not move them.
- In compressed mode the power-on line is 132 characters; setting the
  right margin to 137 gives a full 8 inches (T 117; R 327).

## Tabs (T 118-129)

- Horizontal: up to 32 stops, set in the current pitch, counted from the
  left margin, fixed thereafter. Defaults every 8 pica columns.
- Vertical: up to 16 stops per channel, in lines of the current spacing,
  fixed thereafter; line 0 is the top of form. Stops beyond the form
  length are ignored. Eight channels: `ESC b c stops... 0` stores channel
  c, `ESC /c` selects it, `ESC B` stores channel 0. Default stops every
  other line in 1/6 inch spacing.
- A stop list ends with 0 or any value not greater than the previous one.

## Forms (T 105-110; R 275, 277, 302)

- `ESC C n` sets the form in lines (1-127); `ESC C 0 n` in inches (1-22).
  Both make the current line the top of form and cancel skip-over-
  perforation.
- `ESC N n` skips n lines at the bottom of each form; ignored if n is not
  less than the form length. `ESC O` turns it off.
- `ESC A n` accepts 0-85.

## Graphics (T 145-154; R 276-280)

| Mode | Command | Dots per inch | Adjacent dots in a row |
|---|---|---|---|
| 0 | `ESC K` | 60 | printed |
| 1 | `ESC L` | 120 | printed |
| 2 | `ESC Y` | 120 | second suppressed |
| 3 | `ESC Z` | 240 | second suppressed |
| 4 | | 80 (Epson QX-10 screen) | printed |
| 5 | | 72 (one-to-one, plotter) | printed |
| 6 | | 90 (Corvus Concept, DEC screens) | printed |

`ESC ? s n` reassigns K, L, Y or Z to mode n. `ESC ^ d n1 n2` is nine-pin
graphics: d 0 is 60 dpi and d 1 is 120 dpi; each column takes two bytes,
the first for the top eight pins (bit 7 the top pin) and bit 7 of the
second for the ninth.

## Character ROM (R 253-255; T 208-211)

The ROM holds 256 locations: roman ASCII at 32-126, italic ASCII at
160-254, and 32 international characters at 0-31 (roman) and 128-159
(italic). The international sets do not hold their own characters: each
national code (35, 36, 64, 91-94, 96, 123-126) points at one of the
locations 0-31. The location table (T 210) agrees with our
`charsets.py`; location 7 is the inverted exclamation mark.

- `ESC I 1` prints locations 0-31 for codes that are not control codes;
  7-15, 17-20, 24 and 27 always act as controls. `ESC I 0` restores them.
- `ESC 6` prints 128-159 and 255 as the italic international characters;
  `ESC 7` restores them as controls.

## User-defined characters (T 199-213; R 273-274, 302)

- Needs switch 1-4 off (the factory setting).
- `ESC & 0 c1 c2` then, per character, an attribute byte and 11 column
  bytes (bit 7 the top dot). Attribute bit 7 set: the top eight pins;
  clear: the bottom eight. Bits 4-6 and 0-3 give the first and last
  columns printed in proportional mode (0-11, column 11 for the extra
  emphasized column).
- The RAM has its own 256 locations, independent of the ROM. With
  `ESC % 1 0` selected, a location never defined prints blank.
  `ESC : 0 0 0` copies the whole ROM into RAM first. `ESC % 0 0`
  returns to the ROM.
- With an international set selected, a national code prints the RAM
  location it points to, as in the ROM.
- Two dots side by side in a row are never printed in characters, even at
  half speed.

## Other commands

- `ESC j n` (FX-80 only): reverse feed n/216 inch without a CR.
- `ESC i n` (FX-80 only): immediate mode, printing each character as it
  arrives.
- `ESC s`, `ESC U`, `ESC <`, `ESC 8`, `ESC 9`: speed, direction and paper
  sensing; nothing visible on paper.
- High codes 128-155 and 255 mirror the controls 0-27 and 127 (R 281).
