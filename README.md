# embedded-application-tools
Various tools for embedded applications development

## Icon resizing script

Used to generate the Stax dashboard & in-app icons of an app from a given image (of any format).

Works best if the source image :
* is as large as possible (helps with antialiasing applied when resizing)
* has no border (proper borders will be added by the script automatically)
* is black & white or no more than 16 colors (otherwise the script will auto-convert the colors and it won't look great)

Requires [ImageMagick](https://imagemagick.org/) installed with its `convert` command.

```bash
$> ./resize_icon.sh
Usage: ./resize_icon.sh INPUT_FILE

$> ./resize_icon.sh ../ethereum.png # will create icons/stax_app_ethereum.gif & glyphs/stax_ethereum_64px.gif
```
