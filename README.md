# embedded-application-tools

Various public tools for embedded applications development.

## Icon resizing script

Used to generate the Stax/Flex dashboard & in-app icons of an app from a given image (of any format).

Works best if the source image :

* is as large as possible (helps with antialiasing applied when resizing)
* is black & white or no more than 16 colors (otherwise the script will auto-convert the colors and it won't look great)

Requires [ImageMagick](https://imagemagick.org/) installed with its `convert` command.

```bash
$> cd icons

$> ./resize_icon.sh
Usage: ./resize_icon.sh INPUT_FILE

$> ./resize_icon.sh ../ethereum.png # will create icons/stax_app_ethereum.gif, icons/flex_app_ethereum.gif & glyphs/ethereum_64px.gif

$> ./resize_icon.sh -k ../ethereum.png # same as above, but will keep the margins from the source image (not recommended, unless the icon needs to be purposely small / not centered)
```

## Map file parser

This tool allows to parse the App map file (usually found in the App dir, under `build/<device>/dbg/app.map`), and output the bss symbols list
in a table, sorted in descending order.
The goal is to provide the developer a way to diagnoze the RAM footprint and quickly analyze the possible optimizations.

```bash
$> cd map_parser

$> ./map_parser.py -h
usage: Map parser tool to list BSS symbols by size [-h] -i INPUT [-m MIN] [-x] [-s]

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input map file. (default: None)
  -m MIN, --min MIN     Do not print symbols with size below this value. (default: 0)
  -x, --hexa            Add hex format for sizes. (default: False)
  -s, --sdk             List SDK symbols. (default: False)

```

Quick usage example, on Ethereum, using the following filters: Min size=200B, and without SDK symbols:

```bash
$> map_parser.py -i <path to app>/debug/app.map -m 200
--- BSS Section Summary ---
Total BSS Size: 29824 Bytes
--- BSS Symbols ---
Symbol Name                         | Size (B) | % of BSS | Object File                                                                  
-----------------------------------------------------------------------------------------------------------------------------------------
mem_buffer                          |    12288 |   41.20% | build/flex/obj/app/src/mem.o                                                 
g_network_icon_bitmap               |     2048 |    6.87% | build/flex/obj/app/src_features/provide_network_info/cmd_network_info.o      
msg_buffer                          |      632 |    2.12% | build/flex/obj/app/src_nbgl/ui_approve_tx.o                                  
tmpCtx                              |      540 |    1.81% | build/flex/obj/app/src/main.o                                                
global_sha3                         |      424 |    1.42% | build/flex/obj/app/src/main.o                                                
hash_ctx                            |      424 |    1.42% | build/flex/obj/app/src_features/generic_tx_parser/gtp_tx_info.o              
strings                             |      420 |    1.41% | build/flex/obj/app/src/main.o                                                
dataContext                         |      392 |    1.31% | build/flex/obj/app/src/main.o                                                
g_stax_shared_buffer                |      380 |    1.27% | build/flex/obj/app/src_nbgl/ui_home.o                                        
title_buffer                        |      344 |    1.15% | build/flex/obj/app/src_nbgl/ui_approve_tx.o                                  
-----------------------------------------------------------------------------------------------------------------------------------------
Total BSS Symbols found: 10 / 152
Total accumulated size: 17892 / 29764 Bytes
Total explicit padding: 56 Bytes
Additional unaccounted space: 4 Bytes
Alignment padding: 60 Bytes (0.20%)
Total BSS size: 29824 Bytes
```
