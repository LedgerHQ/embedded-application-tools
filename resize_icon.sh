#!/usr/bin/env bash

set -e

resize_icon() {
    local OPTIND input_file target_size target_margin background_color output_file

    while getopts "i:s:m:b:o:" OPT
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
    convert "$input_file" \
        -background "$background_color" \
        -flatten \
        -resize "${resize_target}x${resize_target}" \
        -colors 16 \
        -bordercolor "$background_color" \
        -border "$target_margin" \
        "$output_file"
}

if [ "$#" -ne 1 ]
then
    echo "Usage: $0 INPUT_FILE"
    exit 1
fi

ifile="$1"
icon_name=$(echo -n "$ifile" | rev | cut -d/ -f1 | rev | cut -d. -f1)

width=$(identify -format "%w" "$ifile")
height=$(identify -format "%h" "$ifile")

# check if square
if [ "$width" -ne "$height" ]
then
    ifile_bak="$ifile"
    ifile=/tmp/icon.png

    # max(width, height)
    if [ "$width" -gt "$height" ]
    then
        isize="$width"
    else
        isize="$height"
    fi
    # generate a temporary square icon
    convert "$ifile_bak" \
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
            -b "$bg_color" \
            -o "glyphs/${icon_name}_64px.gif"

resize_icon -i "$ifile" \
            -s 32 \
            -m 1 \
            -b "$bg_color" \
            -o "icons/stax_app_${icon_name}.gif"

resize_icon -i "$ifile" \
            -s 40 \
            -m 1 \
            -b "$bg_color" \
            -o "icons/flex_app_${icon_name}.gif"

# delete temporary icon
if [ -n "$ifile_bak" ]
then
    rm -f "$ifile"
fi
