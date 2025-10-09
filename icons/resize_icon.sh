#!/usr/bin/env bash

set -e

resize_icon() {
    local OPTIND input_file target_size target_margin target_colors background_color output_file

    while getopts "i:s:m:c:b:o:" OPT
    do
        case "$OPT" in
            i) # input file
                input_file="$OPTARG"
                ;;
            s) # target size (in px)
                target_size="$OPTARG"
                ;;
            m) # margin (in px)
                target_margin="$OPTARG"
                ;;
            c) # number of colors
                target_colors="$OPTARG"
                ;;
            b) # background color
                background_color="$OPTARG"
                ;;
            o) # output file
                output_file="$OPTARG"
                ;;
            *)
                return
                ;;
        esac
    done
    mkdir -p "$(dirname "$output_file")" # create output dir
    resize_target=$((target_size - (target_margin * 2)))
    args=()
    args+=(-background "$background_color")
    if [ "$target_colors" -eq 2 ]
    then
        # seems to produce better outputs
        args+=(-adaptive-resize "${resize_target}x${resize_target}")
    else
        args+=(-resize "${resize_target}x${resize_target}")
    fi
    args+=(-bordercolor "$background_color")
    args+=(-border "$target_margin")
    if [ "$target_colors" -eq 2 ]
    then
        args+=(-monochrome)
    else
        args+=(-type grayscale)
        args+=(-colors "$target_colors")
    fi
    convert "$input_file" "${args[@]}" "$output_file"
}

no_crop=false

while getopts "k" OPT
do
    case "$OPT" in
        k) # keep source image margins
            no_crop=true
            ;;
        *)
            exit 1
            ;;
    esac
done
shift $((OPTIND-1))

if [ "$#" -ne 1 ]
then
    echo "Usage: $0 INPUT_FILE"
    exit 1
fi

icon_name=$(echo -n "$1" | rev | cut -d/ -f1 | rev | cut -d. -f1)
ifile=/tmp/icon.png

if ! "$no_crop"
then
    # crop to content
    convert -background none "$1" -trim +repage "$ifile"
else
    cp "$1" "$ifile"
fi

width=$(identify -format "%w" "$ifile")
height=$(identify -format "%h" "$ifile")

# make square if not already
if [ "$width" -ne "$height" ]
then
    mv "$ifile" "$ifile.old"

    # max(width, height)
    if [ "$width" -gt "$height" ]
    then
        isize="$width"
    else
        isize="$height"
    fi
    # generate a temporary square icon
    convert "$ifile.old" \
        -background none \
        -gravity center \
        -extent "${isize}x${isize}" \
        "$ifile"
fi

bg_color="white"

# common to Stax & Flex
resize_icon -i "$ifile" \
            -s 64 \
            -m 3 \
            -c 16 \
            -b "$bg_color" \
            -o "glyphs/${icon_name}_64px.png"

resize_icon -i "$ifile" \
            -s 32 \
            -m 1 \
            -c 16 \
            -b "$bg_color" \
            -o "icons/stax_app_${icon_name}.png"

resize_icon -i "$ifile" \
            -s 40 \
            -m 1 \
            -c 16 \
            -b "$bg_color" \
            -o "icons/flex_app_${icon_name}.png"

resize_icon -i "$ifile" \
            -s 48 \
            -m 2 \
            -c 2 \
            -b "$bg_color" \
            -o "glyphs/${icon_name}_48px.png"

resize_icon -i "$ifile" \
            -s 32 \
            -m 1 \
            -c 2 \
            -b "$bg_color" \
            -o "icons/apex_app_${icon_name}.png"

# delete temporary icon(s)
rm -f "$ifile" "$ifile.old"
