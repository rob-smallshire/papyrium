# papyrium-model-epson-fx80

The Epson FX-80, an 80-column 9-pin dot-matrix printer of the early 1980s,
for Papyrium. It speaks ESC/P through `papyrium-language-escp` and prints
with a Papyrium dot font (`draft-9` by default) in place of Epson's
character ROM, which is not copied.

Registered as `epson-fx80` on the `papyrium.model` axis. The options model
the printer's DIP switches and paper:

| Option | Default | Meaning |
|---|---|---|
| `auto-line-feed` | `no` | Each carriage return also feeds a line (a BBC Micro left at `*FX6,10` sends CR alone and needs this) |
| `character-set` | `usa` | Power-on international set: usa, france, germany, uk, denmark, sweden, italy, spain, japan |
| `form-length` | `11` | Form length in inches |
| `skip-perforation` | `no` | Skip one inch over the perforation |
| `high-codes-printable` | `no` | Print codes 128-159 rather than obey them as controls |
| `condensed` | `no` | Power on in condensed mode |
| `slashed-zero` | `no` | Print zero with a slash |
| `emphasized` | `no` | Power on printing emphasized |
| `software-select` | `no` | Obey DC1 and DC3; otherwise the printer is always selected |
| `user-defined-characters` | `yes` | The RAM holds user-defined characters; `no` makes it a buffer and `ESC %` is ignored |
| `paper-width` | `9.5` | Paper width in inches, tear-off strips included; the line is centred on it |
| `top-offset` | `0` | Inches from the perforation to the top of the first line, where the paper was wound before switching on |
| `stationery` | `fanfold` | The paper: `fanfold` (plain, with tear-off strips), `sheet` (no strips), `green-bar`, `blue-bar`, `music-ruled` |
| `font` | `draft-9` | The dot font standing in for the character ROM |
