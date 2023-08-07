import os

def find_matching_files(folder_path, log_file):
    for root, _, files in os.walk(folder_path):
        file_dict = {}
        for file in files:
            filename, file_extension = os.path.splitext(file)
            if filename in file_dict:
                if file_extension.lower() in ['.jpg', '.jpeg']:
                    with open(log_file, 'a') as f:
                        f.write(os.path.join(root, file) + '\n')
                elif os.path.splitext(file_dict[filename])[1].lower() in ['.jpg', '.jpeg']:
                    with open(log_file, 'a') as f:
                        f.write(file_dict[filename] + '\n')
            else:
                file_dict[filename] = os.path.join(root, file)

if __name__ == "__main__":
    folder_path = input("Enter the folder path: ")
    log_file = "jpg_log.txt"

    with open(log_file, 'w'):  # Clear the log file if it already exists
        pass

    find_matching_files(folder_path, log_file)
    print("Process completed. The full paths to matching JPG files have been written to 'jpg_log.txt'.")
