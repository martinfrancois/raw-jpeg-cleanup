import os

# Checks if all files exist. After running main.py, to be safe, create a copy of `jpg_log.txt` and replace `.JPG` with `.ARW`. It shouldn't log anything. If it logs anything, remove it from `jpg_log.txt` manually.

def check_file_paths(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            file_path = line.strip()  # Remove leading/trailing whitespace and newline characters
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")

if __name__ == "__main__":
    input_file_path = "jpg_log2.txt"  # Replace with the path of your input file
    check_file_paths(input_file_path)
