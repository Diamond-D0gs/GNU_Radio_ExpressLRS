import os

# Define the number of lines to generate and the output filename
num_lines = 500
filename = "random_hex_lines.txt"

print(f"Generating {num_lines} random hex strings and saving to '{filename}'...")

try:
    with open(filename, "w", encoding="utf-8") as f:
        for _ in range(num_lines):
            # 1. Generate 8 cryptographically secure random bytes
            random_bytes = os.urandom(8)
            
            # 2. Convert the bytes to a hex string (e.g., '1bec68453fab9405')
            hex_string = random_bytes.hex()
            
            # 3. Write the string to the file, followed by a newline
            f.write(hex_string + "\n")
            
    print(f"Successfully created '{filename}' with {num_lines} lines.")

except IOError as e:
    print(f"Error writing to file: {e}")