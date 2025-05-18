with open("tmp.bin", "rb") as f:
    byte_data = f.read()

with open("program.mem", "w") as f:
    for i in range(0, len(byte_data), 4):  # RISC-V命令は32ビット（4バイト）
        word = byte_data[i:i+4]
        if len(word) < 4:
            word = word + b'\x00' * (4 - len(word))  # パディング
        bin_str = ''.join(f'{b:08b}' for b in word[::-1])  # little-endianに並び替え
        f.write(bin_str + '\n')
