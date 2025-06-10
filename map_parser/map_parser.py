#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool to list bss symbols sorted descending by order of size.
"""

from enum import IntEnum
from typing import Tuple, List
import re
import sys
from argparse import ArgumentParser, Namespace, ArgumentDefaultsHelpFormatter


# ===============================================================================
#          Parse command line options
# ===============================================================================
def arg_parse() -> Namespace:
    """Parse the commandline options"""

    parser = ArgumentParser("Map parser tool to list BSS symbols by size", 
                           formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument("-i",
                        "--input",
                        required=True,
                        type=str,
                        help="Input map file.")

    parser.add_argument("-m",
                        "--min",
                        type=int,
                        default=0,
                        help="Do not print symbols with size below this value.")

    parser.add_argument("-x",
                        "--hexa",
                        action="store_true",
                        help="Add hex format for sizes.")

    parser.add_argument("-s",
                        "--sdk",
                        action="store_true",
                        help="List SDK symbols.")

    return parser.parse_args()


# ===============================================================================
#          Parse Map file from compilation and extract BSS section symbols
# ===============================================================================
def parse_map_file(map_file_path: str)-> Tuple[List, int]:
    """
    Parses an ARM GCC linker map file to extract information about the .bss section.

    Args:
        map_file_path (str): The path to the linker map file.
    Returns:
        Tuple[List, int]: A tuple containing a list of dictionaries with symbol information and the total size of the .bss section.
    """

    total_bss_size = 0
    bss_symbols = []
    in_bss_section = False
    current_object_file_context = "unknown" # Default context, updated when an object file is identified

    # Use a set to track (symbol_name, object_file) pairs that have already been added
    added_symbols_set = set()

    # Regex to find the .bss section header and its total size.
    # Matches lines like: "da7a0000 da7a0000 7480 8 .bss"
    # Group 3 captures the hex size (e.g., '7480')
    bss_header_pattern = re.compile(r"^\s*[0-9a-fA-F]+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]+)\s+\S+\s+\.bss\s*$")

    # Regex to parse general lines within sections that contain VMA, LMA, Size, Alignment, and the rest.
    # Matches lines like: "c0de0000 c0de0000 a 2 build/flex/obj/app/src/main.o:(.boot)"
    # Or: "da7a0000 da7a0000 1 1 G_swap_mode"
    # Group 3: Size (hex)
    # Group 5: The "remainder" of the line (the string after alignment, which could be an object file path or a symbol name)
    line_parser_pattern = re.compile(r"^\s*([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s*(.*)$")

    # Regex for lines that specify an object file and potentially a section/symbol within it.
    # Example: "build/flex/obj/app/src/handle_swap_sign_transaction.o:(.bss.G_swap_mode)"
    # Group 1: The full path to the object file (e.g., 'build/flex/obj/app/src/handle_swap_sign_transaction.o')
    # Group 2: The content inside the parentheses, including the section and potentially the symbol
    obj_file_and_section_content_pattern = re.compile(r"^(.*?)\s*:\s*\((.*?)\)$")

    # Regex to extract the symbol name from within a section definition like "(.bss.G_swap_mode)"
    # Group 1: The symbol name (e.g., 'G_swap_mode')
    symbol_in_section_pattern = re.compile(r"\.bss\.?([a-zA-Z_][a-zA-Z0-9_$.@*]*)$")

    # Regex to detect lines that are purely symbol names, not object files or section headers.
    # Example: "G_swap_mode"
    # Group 1: The symbol name
    plain_symbol_pattern = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_$.@*]*)\s*$")

    # Regex to detect the start of other common linker sections to stop parsing .bss.
    # Matches lines like: "d0000000 d0000000 10 4 DEBUG" or "c0de0000 c0de0000 2c346 8 .text"
    other_section_header_pattern = re.compile(r"^\s*[0-9a-fA-F]+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]+)\s+\S+\s+\.(text|data|rodata|stack|heap|common|DEBUG|ARM.exidx)\s*$", re.IGNORECASE)

    # Add a flexible _ebss detection pattern that handles various formats
    ebss_pattern = re.compile(r"^\s*[0-9a-fA-F]+\s+[0-9a-fA-F]+\s+\S+\s+\S+\s+(_ebss|_end|__bss_end__|COMMON)\b", re.IGNORECASE)

    try:
        with open(map_file_path, 'r') as f:
            for line in f:
                stripped_line = line.strip()

                if not stripped_line: # Skip empty lines
                    continue

                if not in_bss_section:
                    # Look for the .bss header to indicate the start of the relevant section
                    match = bss_header_pattern.match(stripped_line)
                    if match:
                        try:
                            # The total BSS size is the third hexadecimal number on the line
                            total_bss_size = int(match.group(1), 16)
                            in_bss_section = True
                        except ValueError:
                            # If parsing the BSS size fails, continue searching for a valid header
                            pass
                        continue
                else:
                    # Multiple checks for when we've left the BSS section
                    
                    # 1. Standard section header check
                    if other_section_header_pattern.match(stripped_line):
                        in_bss_section = False
                        break  # Exit the loop as we've left the .bss section

                    # 2. Check for the _ebss marker
                    if ebss_pattern.search(stripped_line) or "_ebss" in stripped_line:
                        in_bss_section = False
                        break

                    # 3. Additional check for sections by name
                    if re.search(r'\.\w+\s+', stripped_line) and not re.search(r'\.bss', stripped_line):
                        # Found another section that's not .bss
                        in_bss_section = False
                        break

                    # Now, parse lines within the .bss section
                    line_match = line_parser_pattern.match(stripped_line)
                    if line_match:
                        size_hex_str = line_match.group(3) # The size of the symbol/entry
                        remainder_str = line_match.group(5).strip() # The rest of the line after alignment

                        try:
                            symbol_size_dec = int(size_hex_str, 16)
                        except ValueError:
                            # If size conversion fails, this line is likely not a symbol definition we care about
                            continue

                        symbol_name = None
                        object_file_for_current_symbol = None

                        # 1. Prioritize matching lines that explicitly state the object file and symbol in parentheses
                        obj_sec_content_match = obj_file_and_section_content_pattern.match(remainder_str)
                        if obj_sec_content_match:
                            obj_file_path_from_line = obj_sec_content_match.group(1).strip()
                            section_content = obj_sec_content_match.group(2).strip()

                            # Update the current_object_file_context *only if* a valid object file path is found
                            if any(obj_file_path_from_line.endswith(ext) for ext in ['.o', '.obj', '.a', '.lib', '.elf', '.s']):
                                current_object_file_context = obj_file_path_from_line
                            
                            object_file_for_current_symbol = current_object_file_context

                            # Try to extract the symbol name from the section content (e.g., .bss.G_swap_mode)
                            sym_in_sec_match = symbol_in_section_pattern.search(section_content)
                            if sym_in_sec_match:
                                symbol_name = sym_in_sec_match.group(1)

                        else:
                            # 2. If it's not an object file line, try to match a plain symbol name.
                            # This path is primarily for symbols that might not have an explicit object file
                            # on their definition line, or for the "duplicate" plain symbol lines.
                            plain_sym_match = plain_symbol_pattern.match(remainder_str)
                            if plain_sym_match:
                                symbol_name = plain_sym_match.group(1)
                                object_file_for_current_symbol = current_object_file_context # Use the last known context

                        # Check for linker artifacts and ensure symbol_name was found
                        is_linker_artifact = (symbol_size_dec == 0 and (symbol_name == '_bss' or symbol_name == '_ebss'))

                        if symbol_name and not is_linker_artifact:
                            # Get address information from the line
                            vma_addr = int(line_match.group(1), 16)  # Virtual memory address

                            # Normalize object_file to "unknown" if it's still None/empty
                            final_object_file = object_file_for_current_symbol if object_file_for_current_symbol else "unknown"
                            
                            # Create a unique key for the symbol to check for duplicates
                            symbol_key = (symbol_name, final_object_file, symbol_size_dec) # Include size for more robust unique key
                            
                            if symbol_key not in added_symbols_set:
                                bss_symbols.append({
                                    "name": symbol_name,
                                    "size_hex": size_hex_str,
                                    "size_dec": symbol_size_dec,
                                    "vma": vma_addr,  # Store the VMA address
                                    "object_file": final_object_file
                                })
                                added_symbols_set.add(symbol_key)

        # After collecting all symbols, sort them by address
        bss_symbols.sort(key=lambda x: x["vma"])
        
        # Calculate padding between symbols
        total_padding = 0
        previous_end = None
        
        for symbol in bss_symbols:
            current_start = symbol["vma"]
            current_size = symbol["size_dec"]
            
            # If this isn't the first symbol, check for padding
            if previous_end is not None:
                # The padding is the difference between this symbol's start and the previous symbol's end
                padding = current_start - previous_end
                if padding > 0:
                    symbol["padding_before"] = padding
                    total_padding += padding
                else:
                    symbol["padding_before"] = 0
            else:
                symbol["padding_before"] = 0
                
            # Update previous_end for the next iteration
            previous_end = current_start + current_size

    except FileNotFoundError:
        print(f"Error: Map file '{map_file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while parsing the map file: {e}", file=sys.stderr)
        sys.exit(1)

    return bss_symbols, total_bss_size, total_padding


# ===============================================================================
#          Print the BSS summary
# ===============================================================================
def print_summary(total_bss_size: int, with_hex: bool = False)-> None:
    """
    Print the BSS summary.

    Args:
        total_bss_size (int): The total size of the BSS section in bytes.
        with_hex (bool): If True, display sizes in hexadecimal format.
    """

    # --- Output Section ---
    print(f"--- BSS Section Summary ---")
    size_str = f"{total_bss_size}"
    if with_hex:
        size_str += f" (0x{total_bss_size:X})"
    print(f"Total BSS Size: {size_str} Bytes")


# ===============================================================================
#          Print the symbol map
# ===============================================================================
def print_symbols(bss_symbols: list,
                  total_bss_size: int,
                  total_padding: int,
                  with_sdk: bool = True,
                  min_size: int = 0,
                  with_hex: bool = False)-> None:
    """
    Print the found symbols.

    Args:
        bss_symbols (list): List of dictionaries containing information about BSS symbols.
        total_bss_size (int): The total size of the BSS section in bytes.
        with_hex (bool): If True, display sizes in hexadecimal format.
    """

    # Sort symbols by size in descending order to easily identify largest contributors.
    bss_symbols.sort(key=lambda x: x["size_dec"], reverse=True)

    print("--- BSS Symbols ---")
    # Define column headers
    headers = ["Symbol Name", "Size (B)", "% of BSS", "Object File"]
    
    # Determine maximum column widths for formatting
    # Initialize with header lengths
    col_widths = {
        "Symbol Name": len(headers[0]),
        "Size (B)": len(headers[1]),
        "% of BSS": len(headers[2]),
        "Object File": len(headers[3])
    }

    # Update widths based on actual data
    for s in bss_symbols:
        col_widths["Symbol Name"] = max(col_widths["Symbol Name"], len(s["name"]))
        col_widths["Size (B)"] = max(col_widths["Size (B)"], len(f"{s['size_dec']}" + (f" (0x{s['size_dec']:X})" if with_hex else '')))
        col_widths["Object File"] = max(col_widths["Object File"], len(s["object_file"]))
        # Add this line to properly calculate percentage column width:
        col_widths["% of BSS"] = max(col_widths["% of BSS"], len(f"{(s['size_dec'] / total_bss_size) * 100:.2f}%"))

    # Print table header
    header_line = (
        f"{headers[0]:<{col_widths['Symbol Name']}} | "
        f"{headers[1]:>{col_widths['Size (B)']}} | "
        f"{headers[2]:>{col_widths['% of BSS']}} | "
        f"{headers[3]:<{col_widths['Object File']}}"
    )
    print(header_line)
    print("-" * len(header_line))

    # Print each symbol as a table row
    nb_symbols = 0
    symbol_size = 0
    computed_size = 0
    for symbol in bss_symbols:
        symbol_size += symbol["size_dec"]
        if symbol["size_dec"] < min_size:
            # Skip symbols smaller than the minimum size threshold
            continue

        if not with_sdk and "/obj/sdk/" in symbol["object_file"]:
            # Skip SDK symbols if the --sdk flag is not set
            continue

        # Calculate the percentage of the total BSS size
        percentage = (symbol["size_dec"] / total_bss_size) * 100 if total_bss_size > 0 else 0
        # Format the size string, optionally including hexadecimal representation
        size_str = f"{symbol['size_dec']}"
        if with_hex:
            size_str += f" (0x{symbol['size_dec']:X})"
        # Create the row string with proper formatting
        row = (
            f"{symbol['name']:<{col_widths['Symbol Name']}} | "
            f"{size_str:>{col_widths['Size (B)']}} | "
            f"{f'{percentage:.2f}%':>{col_widths['% of BSS']}} | "
            f"{symbol['object_file']:<{col_widths['Object File']}}"
        )
        computed_size += symbol["size_dec"]
        nb_symbols += 1
        # Print the row
        print(row)

    print("-" * len(header_line))
    if min_size != 0 or not with_sdk:
        print(f"Total BSS Symbols found: {nb_symbols} / {len(bss_symbols)}")
        print(f"Total accumulated size: {computed_size} / {symbol_size} Bytes")
    else:
        print(f"Total BSS Symbols found: {nb_symbols}")
        print(f"Total accumulated size: {symbol_size} Bytes")

    print(f"Total explicit padding: {total_padding} Bytes")
    remaining_diff = total_bss_size - (symbol_size + total_padding)
    if remaining_diff > 0:
        print(f"Additional unaccounted space: {remaining_diff} Bytes")

    padding_size = total_bss_size - symbol_size
    padding_percentage = (padding_size / total_bss_size) * 100 if total_bss_size > 0 else 0
    padding_str = f"{padding_size}"
    if with_hex:
        padding_str += f" (0x{padding_size:X})"
    print(f"Alignment padding: {padding_str} Bytes ({padding_percentage:.2f}%)")
    print(f"Total BSS size: {total_bss_size} Bytes")


def main():
    """
    Main function to handle command-line arguments and initiate parsing.
    """
    args = arg_parse()

    bss_symbols, total_bss_size, total_padding = parse_map_file(args.input)
    if not bss_symbols:
        if total_bss_size == 0:
            print("No BSS symbols found and BSS section is empty or not properly parsed.")
            return
        if total_bss_size > 0:
            print(f"BSS section has a total size of {total_bss_size} bytes, but no individual symbols were extracted.")
            print("This might indicate that the symbol parsing patterns need further refinement for your specific map file format.")
            return

    print_summary(total_bss_size, args.hexa)
    print_symbols(bss_symbols, total_bss_size, total_padding, args.sdk, args.min, args.hexa)

if __name__ == "__main__":
    main()
