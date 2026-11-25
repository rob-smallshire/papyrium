# Printing through a CUPS driver

`print_through_cups.py` prints a test page (`test_page.py`: a one-inch
grid, a border half an inch in, diagonals, text from 6 to 48 points and
grey squares) through a CUPS queue's printer driver, and prints the bytes
the driver makes with Papyrium, so that what a computer's driver sends,
and how a Papyrium model takes it, can be seen together.

```sh
uv run python tools/cups-print/print_through_cups.py                      # through the FX80 queue's driver, printed as an FX-80
uv run python tools/cups-print/print_through_cups.py --model star-lc10
uv run python tools/cups-print/print_through_cups.py --resolution 240x72dpi
uv run python tools/cups-print/print_through_cups.py --queue              # with lp, to a running papyrium serve
```

Without `--queue` it needs no running printer: `cupsfilter` rasterises the
page as the queue would, and the driver's filter, named in the queue's
PPD, makes the bytes, which are the same every time. The PDF, the raster,
the capture and the pages go in `cups-print-output/`.

## CUPS's Epson 9-Pin Series driver

macOS and Linux include CUPS's sample driver for Epson 9-pin printers,
added with

```sh
sudo lpadmin -p FX80 -D "Epson FX-80" -E -v socket://localhost:9100 \
    -m drv:///sample.drv/epson9.ppd
```

It prints everything as bit images (`ESC *` mode 1 at 120 dots per inch,
or modes 0 and 3 at 60 and 240), in bands of eight rows 1/9 inch apart
(`ESC 3 24` and LF), each band twice, its even and odd columns apart, as
a 9-pin printer needs at 120 dots per inch. It places each image with
`ESC $`, an absolute move in 1/60 inch, and also sends `ESC P`, `ESC x`
and `ESC U`.

`ESC $` came after the FX-80: of Papyrium's models only the Star LC-10
(and LC-10 Colour) obeys it. The others, like the real printers, print
its argument as a character and run each band's second image on from
its first, so the page is garbled. Serve the LC-10 for this driver:

```sh
papyrium serve --model star-lc10 -M stationery=sheet
```
