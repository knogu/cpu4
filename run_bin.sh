sed -i '' -e $'1s/^/01000000000000000000000100010011\\\n/' ~/cpu4/asm.bin # set sp
sed -i -e 's/00000000000000001000000001100111/00000101000000000111100010011/' ~/cpu4/asm.bin # insert halt
iverilog -g 2012 -o ~/cpu4/a.out ~/cpu4/cpu.sv ~/cpu4/mem_sim.sv && vvp ~/cpu4/a.out
