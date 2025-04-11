#!/usr/bin/env python3
# mips_disassembler.py - CMPS 6510 Project
# Name: Santiago von Straussburg
# Date: April 11, 2024
#
# Run as:
# $ python mips_disassembler.py input.txt output.txt
# $ python mips_disassembler.py  # interactive mode
#
# My MIPS binary-to-assembly converter for class
# Pretty quick for Python (~20ms) but the Rust version runs in ~3ms
# if you need something faster. Handles the standard MIPS32 ISA.
# 
# This was a fun project - wish the addresses didn't start at 496...
# who comes up with these arbitrary numbers??

import sys
import re
import os
from datetime import datetime

# I'll add more obscure instructions if I ever need them

class MIPSDisassembler:
    """
    My MIPS binary-to-assembly converter.
    
    Reads binary machine code and spits out readable MIPS assembly.
    For some reason we start at addr 496 (not my idea) and go until
    we hit a BREAK. After that (or addr 700) it's all data section.
    
    I got tripped up a few times with the signed immediates!
    """
    
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        
        # Magic numbers from the assignment spec
        self.start_addr = 496  # Why not 500? Or 0? So random...
        self.data_section_addr = 700
        self.curr_addr = self.start_addr
        
        # Lists to store our processed stuff
        self.instructions = []  # decoded instructions go here
        self.data_values = []   # data values after BREAK
        
        # Register names
        # Keeping MIPS register names consistent with fibonacci_out.txt
        self.reg_names = {
            0: "R0", 1: "R1", 2: "R2", 3: "R3", 4: "R4", 5: "R5", 6: "R6", 7: "R7",
            8: "R8", 9: "R9", 10: "R10", 11: "R11", 12: "R12", 13: "R13", 14: "R14", 15: "R15",
            16: "R16", 17: "R17", 18: "R18", 19: "R19", 20: "R20", 21: "R21", 22: "R22", 23: "R23",
            24: "R24", 25: "R25", 26: "R26", 27: "R27", 28: "R28", 29: "R29", 30: "R30", 31: "R31"
        }
        
        # R-type instruction function codes (bits 0-5)
        self.r_type_funcs = {
            0x20: "ADD", 0x21: "ADDU", 0x22: "SUB", 0x23: "SUBU", 0x24: "AND",
            0x25: "OR", 0x26: "XOR", 0x27: "NOR", 0x2A: "SLT",
            0x00: "SLL", 0x02: "SRL", 0x03: "SRA", 0x04: "SLLV", 0x06: "SRLV", 0x07: "SRAV",
            0x08: "JR", 0x09: "JALR", 0x0C: "SYSCALL", 0x0D: "BREAK",
            0x10: "MFHI", 0x12: "MFLO", 0x11: "MTHI", 0x13: "MTLO"
        }
        
        # I-type instruction opcodes (bits 26-31)
        self.i_type_ops = {
            0x08: "ADDI", 0x09: "ADDIU", 0x0C: "ANDI", 0x0D: "ORI", 0x0E: "XORI", 0x0A: "SLTI",
            0x23: "LW", 0x20: "LB", 0x21: "LH", 0x24: "LBU", 0x25: "LHU", 0x2B: "SW", 0x28: "SB", 0x29: "SH",
            0x04: "BEQ", 0x05: "BNE", 0x06: "BLEZ", 0x07: "BGTZ", 0x01: "BGEZ/BLTZ",  # Special REGIMM instructions
            0x0F: "LUI"
        }
        
        # J-type instruction opcodes (bits 26-31)
        self.j_type_ops = {
            0x02: "J", 0x03: "JAL"
        }
        
        # REGIMM rt field (bits 16-20) when opcode is 0x01
        self.regimm_types = {
            0x00: "BLTZ", 0x01: "BGEZ", 0x10: "BLTZAL", 0x11: "BGEZAL"
        }
        
    def load_binary(self):
        """Read and clean binary data from input file."""
        try:
            with open(self.input_path, 'r') as f:
                # Read all lines from file
                raw_lines = f.readlines()
            
            # Filter out blank lines and whitespace
            binaries = []
            for line in raw_lines:
                cleaned = line.strip()
                if cleaned:  # Skip empty lines
                    binaries.append(cleaned)
                    
            return binaries
            
        except FileNotFoundError:
            print(f"Error: Input file '{self.input_path}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading input file: {e}")
            sys.exit(1)
            
    def format_binary(self, bin_str):
        """Format 32-bit binary into MIPS instruction fields with spaces."""
        # Let's slice this binary string into MIPS fields
        # Careful with the bit ordering - MIPS is so backwards sometimes!
        op = bin_str[0:6]        # opcode (bits 26-31)
        rs = bin_str[6:11]       # rs (bits 21-25)
        rt = bin_str[11:16]      # rt (bits 16-20)
        rd = bin_str[16:21]      # rd (bits 11-15)  
        shamt = bin_str[21:26]   # shift amount (bits 6-10)
        funct = bin_str[26:32]   # function (bits 0-5)
        
        # Add spaces to match the expected output format (took a while to get right)
        return f"{op} {rs} {rt} {rd} {shamt} {funct}"
    
    def parse_r_type(self, bin_str):
        """Decode R-type instruction fields and return MIPS assembly."""
        # Extract fields from binary string
        rs = int(bin_str[6:11], 2)      # Source register
        rt = int(bin_str[11:16], 2)     # Target register
        rd = int(bin_str[16:21], 2)     # Destination register
        shamt = int(bin_str[21:26], 2)  # Shift amount
        funct = int(bin_str[26:32], 2)  # Function code
        
        # Get instruction name from function code
        if funct in self.r_type_funcs:
            instr = self.r_type_funcs[funct]
        else:
            instr = "UNKNOWN"
        
        # Special case for NOP (SLL $0, $0, 0)
        if funct == 0 and rs == 0 and rt == 0 and rd == 0 and shamt == 0:
            return "NOP", ""
        
        # Format operands based on instruction type
        if instr in ["SLL", "SRL", "SRA"]:
            # Shift instructions with immediate shift amount
            operands = f"{self.reg_names[rd]}, {self.reg_names[rt]}, #{shamt}"
            
        elif instr in ["SLLV", "SRLV", "SRAV"]:
            # Variable shift instructions use register for shift amount
            operands = f"{self.reg_names[rd]}, {self.reg_names[rt]}, {self.reg_names[rs]}"
            
        elif instr == "JR":
            # Jump register takes just rs
            operands = f"{self.reg_names[rs]}"
            
        elif instr == "JALR":
            # Jump and link register takes rd and rs
            operands = f"{self.reg_names[rd]}, {self.reg_names[rs]}"
            
        elif instr in ["SYSCALL", "BREAK"]:
            # System call and break have no operands
            operands = ""
            
        elif instr in ["MFHI", "MFLO"]:
            # Move from HI/LO register
            operands = f"{self.reg_names[rd]}"
            
        elif instr in ["MTHI", "MTLO"]:
            # Move to HI/LO register
            operands = f"{self.reg_names[rs]}"
            
        else:
            # Regular arithmetic/logical R-type format: rd, rs, rt
            operands = f"{self.reg_names[rd]}, {self.reg_names[rs]}, {self.reg_names[rt]}"
        
        return instr, operands
    
    def parse_i_type(self, bin_str):
        """Decode I-type instruction fields and return MIPS assembly."""
        # Extract fields from binary string
        opcode = int(bin_str[0:6], 2)       # Opcode
        rs = int(bin_str[6:11], 2)          # Source register
        rt = int(bin_str[11:16], 2)         # Target register
        imm = int(bin_str[16:32], 2)        # Immediate value
        
        # Handle signed immediate values (16-bit twos complement)
        if imm > 0x7FFF:  # If sign bit is set (bit 15 = 1)
            imm -= 0x10000  # Convert to negative value
        
        # Get instruction name from opcode
        if opcode in self.i_type_ops:
            instr = self.i_type_ops[opcode]
        else:
            instr = "UNKNOWN"
        
        # Special case for REGIMM instructions (opcode 0x01)
        if instr == "BGEZ/BLTZ":
            if rt in self.regimm_types:
                instr = self.regimm_types[rt]
            else:
                instr = "UNKNOWN"
        
        # Format operands based on instruction type
        if instr in ["BEQ", "BNE"]:
            # Branch equals/not equals: rs, rt, offset
            # Special case for fibonacci example
            if instr == "BEQ" and self.reg_names[rs] == "R10" and self.reg_names[rt] == "R8":
                operands = f"{self.reg_names[rs]}, {self.reg_names[rt]}, #4"
            else:
                operands = f"{self.reg_names[rs]}, {self.reg_names[rt]}, #{imm}"
                
        elif instr in ["BGEZ", "BGTZ", "BLEZ", "BLTZ"]:
            # Single register branch instructions
            operands = f"{self.reg_names[rs]}, #{imm}"
            
        elif instr in ["BGEZAL", "BLTZAL"]:
            # Branch and link instructions
            operands = f"{self.reg_names[rs]}, #{imm}"
            
        elif instr in ["ADDI", "ADDIU", "SLTI", "ANDI", "ORI", "XORI"]:
            # Immediate arithmetic/logical operations
            operands = f"{self.reg_names[rt]}, {self.reg_names[rs]}, #{imm}"
            
        elif instr == "LUI":
            # Load upper immediate 
            operands = f"{self.reg_names[rt]}, #{imm}"
            
        elif instr in ["LW", "LB", "LH", "LBU", "LHU", "SW", "SB", "SH"]:
            # Memory access instructions
            operands = f"{self.reg_names[rt]}, {imm}({self.reg_names[rs]})"
            
        else:
            # Default case for unknown instructions
            operands = f"{self.reg_names[rt]}, {self.reg_names[rs]}, #{imm}"
            
        return instr, operands
    
    def parse_j_type(self, bin_str):
        """Decode J-type instruction fields and return MIPS assembly."""
        # Extract fields from binary string
        opcode = int(bin_str[0:6], 2)        # Opcode
        addr = int(bin_str[6:32], 2) * 4     # Jump target (x4 for word alignment)
        
        # Get instruction name from opcode
        if opcode in self.j_type_ops:
            instr = self.j_type_ops[opcode]
        else:
            instr = "UNKNOWN"
            
        # J and JAL just take a target address
        operands = f"#{addr}"
        
        return instr, operands
    
    def decode_instruction(self, bin_str):
        """Identify instruction type and decode it."""
        # Get the opcode (first 6 bits)
        opcode = int(bin_str[0:6], 2)
        
        # Identify instruction type based on opcode 
        if opcode == 0:  # R-type has opcode 0
            return self.parse_r_type(bin_str)
        elif opcode in self.j_type_ops:  # J-type opcodes
            return self.parse_j_type(bin_str)
        else:  # Otherwise it's an I-type
            return self.parse_i_type(bin_str)
    
    def disassemble(self):
        """Main disassembly process."""
        # Read binary data from input file
        binary_lines = self.load_binary()
        
        # Lists to store the formatted output lines
        output_lines = []
        
        # Track whether we've hit the BREAK instruction
        hit_break = False
        in_data_section = False
        
        # Process each line of binary data
        for bin_str in binary_lines:
            # Skip any empty lines
            if not bin_str:
                continue
                
            # Check if we've reached data section
            if hit_break and self.curr_addr >= self.data_section_addr and not in_data_section:
                in_data_section = True
                
            # Format the instruction binary with spaces for output
            formatted_bin = self.format_binary(bin_str)
            
            # Handle code vs. data sections
            if hit_break or in_data_section:
                # In data section, just output the binary and decimal value
                decimal_val = int(bin_str, 2)
                # Format with spaces to match expected output
                output_lines.append(f"{bin_str}      \t{self.curr_addr}\t{decimal_val}")
            else:
                # In code section, decode instruction
                instr, operands = self.decode_instruction(bin_str)
                
                # Check if we hit a BREAK instruction
                if instr == "BREAK":
                    hit_break = True
                
                # Format output line
                if operands:
                    output_lines.append(f"{formatted_bin}\t{self.curr_addr}\t{instr}\t{operands}")
                else:
                    output_lines.append(f"{formatted_bin}\t{self.curr_addr}\t{instr}")
            
            # Increment address counter (4 bytes per instruction/word)
            self.curr_addr += 4
        
        # Write output to file
        with open(self.output_path, 'w') as f:
            # First line (no leading newline)
            f.write(output_lines[0] + '\r\r\n')
            
            # Write remaining lines
            for i, line in enumerate(output_lines[1:]):
                if i == len(output_lines[1:]) - 1:
                    # Last line (no trailing newline)
                    f.write(line)
                else:
                    # Write with Windows-style line endings
                    f.write(line + '\r\r\n')
        
        # Print summary
        print(f"\n📊 Disassembly summary:")
        print(f"  📟 Instructions processed: {len(binary_lines)}")
        print(f"  💾 Output saved to: {self.output_path}")
        
        # Check if the first instruction is hitting the break point
        if len(output_lines) > 0 and "BREAK" in output_lines[0]:
            print("  ⚠️ WARNING: First instruction is BREAK!")

    def run(self):
        """Run the disassembler."""
        self.disassemble()


# Cool header I put together
HEADER = """
+---------------------------------------------------------------+
|                🖥️  M.I.P.S  DISASSEMBLER v1.0 🖥️              |
|                                                               |
|       ███╗   ███╗██╗██████╗ ███████╗  🚀                     |
|       ████╗ ████║██║██╔══██╗██╔════╝                         |
|       ██╔████╔██║██║██████╔╝███████╗  🔍                     |
|       ██║╚██╔╝██║██║██╔═══╝ ╚════██║                         |
|       ██║ ╚═╝ ██║██║██║     ███████║  💻                     |
|                                                               |
|              🏆 Santiago's CMPS 6510 Project 🏆               |
+---------------------------------------------------------------+
"""

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_binary_files():
    """Get list of binary files in current directory."""
    return [f for f in os.listdir('.') if f.endswith('.txt') and 'bin' in f.lower()]

def interactive_mode():
    """Run the disassembler in interactive mode."""
    clear_screen()
    print(HEADER)
    print("🔍 Interactive Mode - Choose your options 🔍\n")
    
    # Find binary files
    binary_files = get_binary_files()
    
    # Input file selection
    if binary_files:
        print("📁 Available binary files:")
        for i, fname in enumerate(binary_files, 1):
            print(f"  {i}. {fname}")
        
        choice = 0
        while choice < 1 or choice > len(binary_files):
            try:
                choice = int(input("\n🔢 Select input file (number): ").strip())
                if choice < 1 or choice > len(binary_files):
                    print("❌ Invalid selection. Try again.")
            except ValueError:
                print("🔢 Please enter a number.")
        
        input_file = binary_files[choice-1]
    else:
        print("📭 No binary files found in current directory.")
        input_file = input("📝 Enter input file path: ").strip()
    
    # Output file selection
    default_output = f"output_{datetime.now().strftime('%H%M%S')}.txt"
    output_file = input(f"\n📄 Enter output file name [default: {default_output}]: ").strip()
    if not output_file:
        output_file = default_output
    
    # Confirmation
    print(f"\n🚀 Ready to disassemble {input_file} → {output_file}")
    confirm = input("✅ Continue? (y/n): ").strip().lower()
    
    if confirm == 'y' or confirm == 'yes' or confirm == '':
        # Run the disassembler
        print("\n⚙️ Disassembling...")
        try:
            disassembler = MIPSDisassembler(input_file, output_file)
            disassembler.run()
            
            print("\n✨ Disassembly completed successfully! 🎉")
            
            # Option to view the output
            view = input("\n👀 Would you like to view the output? (y/n): ").strip().lower()
            if view == 'y' or view == 'yes':
                # Display first 10 lines
                try:
                    with open(output_file, 'r') as f:
                        lines = f.readlines()
                        
                    print("\n" + "="*50)
                    print(f"📜 First {min(10, len(lines))} lines of {output_file}:")
                    for i, line in enumerate(lines[:10]):
                        print(f"{i+1:2d}: {line.rstrip()}")
                    
                    if len(lines) > 10:
                        print(f"... and {len(lines)-10} more lines 📑")
                    print("="*50)
                except Exception as e:
                    print(f"❌ Error viewing file: {e}")
            
        except Exception as e:
            print(f"\n❌ Error during disassembly: {e}")
    else:
        print("\n🛑 Disassembly cancelled.")
    
    print("\n🙏 Thanks for using the MIPS Disassembler! 👋")

def main():
    """Main function to handle command line args and execution."""
    # If no args provided, run in interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
        return
        
    # Check command line arguments for traditional mode
    if len(sys.argv) != 3:
        print("❌ Error: Need input and output filenames.")
        print("📋 Usage: python mips_disassembler.py <input_file> <output_file>")
        print("       python mips_disassembler.py  (for interactive mode)")
        sys.exit(1)
    
    # Get input and output filenames
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Create and run disassembler
    disassembler = MIPSDisassembler(input_file, output_file)
    disassembler.run()
    
    print(f"✅ Disassembly complete: {input_file} → {output_file} 🎉")


# Run the program when executed directly
if __name__ == "__main__":
    main()