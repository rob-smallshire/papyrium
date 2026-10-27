# Character generation

How Papyrium turns a character into dots, what the Star LC-10 asks of
that which the earlier printers did not, and the refactoring that makes
the LC-10 an easy change. Written 2026-10-27, before the LC-10 model.

## Where it stands

A printer's characters pass through three things:

- **Fonts** (`papyrium.core.dotfont`) are bitmaps on the `papyrium.font`
  axis: a font has a fixed matrix, rows by columns, and each glyph is a
  set of dots in it. A glyph carries nothing else: no width, no spacing.
- **The mechanism** (`EscpMechanism`) is a printer model's description of
  its hardware: one draft font, a tuple of NLQ fonts in `ESC k` order,
  and a growing number of booleans for its quirks
  (`prints_adjacent_dots_once`, `nlq_emphasized`, `justify_nlq_only`,
  ...).
- **The interpreter** (`EscpInterpreter`) holds the algorithms: italic as
  a slant of half a column per row about row 6 (`BASELINE_ROW`),
  emphasis, double-strike 1/216 inch lower, double width, NLQ as two
  passes 1/216 inch apart on a 24-column pica cell, proportional widths
  measured from where a glyph's dots fall.

That suited the FX-80, M-1109 and LX-800, whose firmware stores most of
what they print and varies little in how it prints it.

## What the LC-10 shows

The LC-10's firmware (`docs/star-lc10-firmware.md`) generates much of
what it prints from a few tables, and does so its own way:

1. **Characters carry their spacing.** Every NLQ entry gives a left
   space, a width and a right space; proportional spacing is the width
   plus four columns, with the spaces dropped. Draft's table carries
   first and last columns. Papyrium's fonts cannot hold these, so the
   interpreter guesses from the dots.
2. **Some typefaces are made from others.** Pica, condensed and
   proportional draft are Sanserif's second NLQ pass at half width,
   pairs of columns ORed and no pin fired twice running. Condensed NLQ
   halves each pass the same way. The block graphics are extended from
   8 dots to 12 by repeating their two lowest rows.
3. **The styles are its own.** Italic shears each column byte, the
   lowest pins fixed and the top moved three 1/120 inch columns (draft)
   or seven 1/240 inch columns (NLQ), about the byte rather than a
   common baseline. Superscript and subscript keep every other row.
   NLQ's passes are 1/144 inch apart, not 1/216.
4. **Pitch chooses the glyphs.** Elite NLQ has its own tables (a 20
   column cell, with narrower forms of the widest letters); elite draft
   has the ROM's draft table while the other pitches have derived draft.
5. **Colour.** The LC-10 Colour prints each dot from one or two ribbon
   bands.

The interpreter can express none of 1 to 4 without another round of
booleans, and the page model cannot express 5.

## Two kinds of generator

The printer's generators fall into two kinds, and they belong in
different places.

**Fixed derivations are fonts.** Pica draft is always Sanserif's second
pass at half width, whatever the printer is doing. Such a typeface is a
font defined by another font and a transform: a *derived font* on the
font axis, registered and selected like any other. Defining it so,
rather than baking its dots into a file, keeps the hardware's
dependency: replace the Sanserif font and pica draft follows, as it would
on the printer, where a baked file would silently disagree. The block
graphics' 12-dot extension is the same kind.

**Mode-dependent transforms are not fonts.** Italic, scripts, enlarged
sizes, emphasis, double-strike and condensed depend on the print mode
and on how the line's passes are arranged, and each printer has its own
(the LX-800 stores italic glyphs; the LC-10 shears each column). Made
into fonts they would multiply into a variant for every combination of
modes. They are the printer's *character generator*: strategies the
printer model supplies to the interpreter, in place of booleans that
switch behaviour inside it.

## The plan

Refactor first: make each change easy, then make the easy change. Every
step keeps the FX-80, M-1109 and LX-800 golden pages byte-identical,
which is the test that a refactoring has not changed behaviour.

1. **Glyph metrics.** A glyph gains its cell: where its advance begins
   and ends, as left space, width and right space, optional in the dot
   font format so existing fonts need no change and their metrics
   default to what the interpreter measures today. Proportional spacing
   then reads the glyph's metrics rather than measuring its dots.
2. **A character generator.** The interpreter's styling (italic,
   emphasis, double-strike, double width, scripts) and NLQ geometry
   (pass offset, columns to the cell) move behind an object the
   mechanism supplies, with today's behaviour as the FX-80's generator
   and the existing booleans folded into it where they belong.
3. **Typefaces by pitch.** The mechanism names a font for each quality,
   typeface and pitch it distinguishes, falling back as today where it
   does not.
4. **Derived fonts.** A font defined by a source font and a transform:
   first the transforms the LC-10 needs (one pass's rows, half width
   with no pin fired twice running, rows repeated below). `lc10-draft`
   becomes a derived font of `lc10-nlq-sanserif`, checked against the
   dots the extractor makes today.
5. **The LC-10 model**, on the LX-800 per the emulation rule: its
   generator (the column-byte italic shear, 1/144 inch NLQ passes, the
   12-dot block graphics), its fonts by pitch, its spacing from glyph
   metrics, then the Star commands.
6. **Colour** in the page model, a set of ribbon bands for each dot, and
   the LC-10 Colour's `ESC r` and band passes.

Steps 1 to 3 the LC-10 needs whether or not fonts can be derived; once
they are done, derived fonts cost little.

## Progress

Steps 1 to 4 are done:

1. A glyph may carry its `span` (`U+0021 span 2 5`), and proportional
   spacing reads its `extent`.
2. `papyrium.language.escp.generator`: a `CharacterGenerator` turns a
   glyph in a `CharacterStyle` into dots, its `proportional_cell` gives
   a character's proportional width, and its parameters hold the rules
   that were mechanism booleans (`prints_adjacent_dots_once`,
   `nlq_emphasized`) and NLQ's pass offset. An NLQ font's columns span
   its cell.
3. The mechanism's `elite_font`, `nlq_elite` and `nlq_elite_fonts` choose
   fonts by pitch.
4. `DerivedDotFont`, with the `pass_rows` and `half_width` transforms;
   `lc10-draft` is derived from `lc10-nlq-sanserif`.

The block graphics stay a file, `lc10-block-graphics`, with their 12-dot
extension written out as rows 8-11: the ROM keeps no 8-dot block font
that another could be derived from, only the table the extractor reads.

Step 5 is under way. Two further refactorings came first: a draft
cell's columns at each pitch became a generator rule (`cell_columns`),
and a glyph says whether it prints a pin lower (`lowered`), which the
LC-10's italic needs because it slants about the column byte. The
generator gained `italic_offset`, `nlq_italic_offset` and
`double_strike_offset`, the interpreter's 1/216 inch feed unit was
renamed `FEED_STEP`, and a mechanism may keep block graphics in a font
of their own. `papyrium.model.star_lc10` prints Standard mode with the
LC-10's fonts by pitch, its generator (`LC10CharacterGenerator`) and its
12-dot block graphics. Still to come: NLQ proportional spacing, the
Star commands, character sizes, IBM mode, and colour (step 6).

Since then the LC-10 has gained, each as a mechanism or generator rule
the other printers leave at their defaults: proportional NLQ
(`nlq_proportional_cell`), Star's ESC/P additions (`ESC $`, `ESC \`,
`ESC X`, `ESC SP`, `ESC ~`, `ESC LF`, `ESC FF`, `ESC +`, `ESC f 0` as a
column move), character sizes (`ESC h`, `ESC w`, `ESC [ @`, with the
generator's `enlarged_dots`), overline and the top margin, switch 1-2
(`line_feed_returns`), its national-set departures
(`national_differences`), proportional elite without forced emphasis,
and download characters by quality.

Step 6 is done. A page holds dots struck through coloured ribbon bands
(`Page.ink_dots`, by `Ink`), which the PNG and PDF outputs multiply onto
the paper so that overprinted inks mix; `ESC r` and the embedded
commands (`embedded_commands`) choose colours on a mechanism with a
`colour_ribbon`; and `star-lc10-colour` is the LC-10 Colour.

IBM mode remains. Per the emulation rule it comes after the printer it
emulates: the IBM Proprinter's language, `papyrium.language.proprinter`,
shares the ESC/P interpreter's machinery and makes NLQ from the draft
characters as the Proprinter does (`nlq_from_draft`), a mode-dependent
transform, since it applies to download characters too.
