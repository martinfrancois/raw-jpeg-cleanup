import os
import send2trash

def move_to_trash(file_path):
    try:
        send2trash.send2trash(file_path)
        print(f"Moved '{file_path}' to the trash folder.")
    except FileNotFoundError:
        print(f"File not found: '{file_path}'")
    except OSError as e:
        print(f"Error moving '{file_path}' to the trash folder: {e}")

def main():
    file_paths_file = "jpg_log.txt"  # Replace this with the path to your file containing one path per line

    try:
        with open(file_paths_file, "r") as file:
            file_paths = file.readlines()
    except FileNotFoundError:
        print(f"File not found: '{file_paths_file}'")
        return

    for file_path in file_paths:
        file_path = file_path.strip()  # Remove leading/trailing whitespaces and newlines
        if os.path.isfile(file_path):
            move_to_trash(file_path)
        else:
            print(f"Invalid file path or not a file: '{file_path}'")

if __name__ == "__main__":
    main()
