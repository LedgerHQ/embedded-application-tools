# embedded-application-tools
Various tools for embedded applications development

## Icon resizing script

Used to generate the Stax/Flex dashboard & in-app icons of an app from a given image (of any format).

Works best if the source image :
* is as large as possible (helps with antialiasing applied when resizing)
* is black & white or no more than 16 colors (otherwise the script will auto-convert the colors and it won't look great)

Requires [ImageMagick](https://imagemagick.org/) installed with its `convert` command.

```bash
$> ./resize_icon.sh
Usage: ./resize_icon.sh INPUT_FILE

$> ./resize_icon.sh ../ethereum.png # will create icons/stax_app_ethereum.gif, icons/flex_app_ethereum.gif & glyphs/ethereum_64px.gif

$> ./resize_icon.sh -k ../ethereum.png # same as above, but will keep the margins from the source image (not recommended, unless the icon needs to be purposely small / not centered)
```
