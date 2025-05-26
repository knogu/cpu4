def bin_to_mif_compact(input_file, output_file, depth=65536):
    width = 32
    default_value = "00000000000000000000000000000000"

    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    with open(output_file, 'w') as f:
        f.write(f"WIDTH={width};\n")
        f.write(f"DEPTH={depth};\n\n")
        f.write("ADDRESS_RADIX=UNS;\n")
        f.write("DATA_RADIX=BIN;\n\n")
        f.write("CONTENT BEGIN\n")

        for addr, line in enumerate(lines):
            f.write(f"    {addr} : {line};\n")

        if len(lines) < depth:
            f.write(f"    [{len(lines)}..{depth - 1}] : {default_value};\n")

        f.write("END;\n")

bin_to_mif_compact('insts.bin', 'insts.mif')
