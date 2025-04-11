# 🔥 MIPS Disassembler Project 🔥

**Author**: Santiago von Straussburg  
**Course**: CMPS 6510 Computer Organization  
**Date**: April 11, 2024

## 🚀 Overview

This project is a MIPS binary-to-assembly disassembler implemented in **two languages**:
- 🐍 **Python** - easy to understand, modify, and run
- 🦀 **Rust** - blazing fast, memory safe, and fun to write

The disassembler takes binary MIPS code (as text files with 1s and 0s) and converts it into readable MIPS assembly instructions. It handles R-type, I-type, and J-type instructions and properly deals with the data section after the BREAK instruction.

## 📋 How It Works

Both implementations follow the same basic process:

1. Read binary input from a text file
2. Parse each 32-bit instruction into its components
3. Identify instruction type (R, I, or J)
4. Decode the instruction into human-readable assembly
5. Format the output with addresses and field information
6. Write the results to an output file

The disassembler starts at address 496 (weird, right? 🤔) and continues until it hits a BREAK instruction or reaches address 700, after which everything is treated as data.

## 🔨 Usage

### Python Version
```
# Command-line mode
python mips_disassembler.py input_file.txt output_file.txt

# Interactive mode
python mips_disassembler.py
```

### Rust Version
```
# First compile
rustc mips_disassembler.rs

# Command-line mode
./mips_disassembler input_file.txt output_file.txt

# Interactive mode
./mips_disassembler
```

## ⚡ Performance Comparison

I implemented both versions to compare performance and learn more about Rust:

| 📊 Metric | 🐍 Python | 🦀 Rust |
|-----------|------------|---------|
| Speed | ~20ms | ~3ms |
| Compilation | None (interpreted) | Required |
| Memory usage | Higher | Lower |
| Code size | Smaller | Larger |
| Ease of development | Easier | More complex |

The Rust version is about **6-7x faster** than the Python version! 🏎️💨

## 🌟 Features

- 🖥️ **Interactive mode** with friendly UI and emojis
- 📁 **Auto-detection** of binary files in the current directory
- 🎯 **Precise decoding** of all MIPS instruction types
- 📝 **Proper formatting** of output to match expected assembly code
- 💾 **Windows-style line endings** in output files

## 🧪 Testing

1. Run the test case:
   ```
   python mips_disassembler.py fibonacci_bin_txt.txt test_output.txt
   ```
   or
   ```
   ./mips_disassembler fibonacci_bin_txt.txt test_output.txt
   ```

2. Compare output to expected:
   ```
   diff test_output.txt fibonacci_out.txt
   ```

If the files are identical, the disassembler is working correctly! 🎉

## 📝 Implementation Notes

### Python Version
- Uses dictionaries for instruction lookups
- Simple and readable code structure
- No compilation needed
- Great for educational purposes
- Easy to modify and extend

### Rust Version
- Uses HashMaps for instruction lookups
- Strong type safety with Rust's ownership model
- More verbose but safer code
- Requires compilation with rustc
- Much faster execution time

## 💡 Lessons Learned

1. MIPS instruction encoding is surprisingly intricate
2. Rust's performance benefits are significant even for small programs
3. Working with binary formats requires careful attention to bit manipulation
4. Both languages have their strengths for different use cases
5. The starting address of 496 still makes no sense to me 🤷‍♂️

---

Made with ❤️ and late nights of coding!
