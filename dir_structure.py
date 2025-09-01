# dir_structure.py
import os

EXCLUDE_DIRS = {"myenv", "__pycache__"}

def print_directory_structure(root, indent=""):
    items = [i for i in sorted(os.listdir(root)) if i not in EXCLUDE_DIRS]
    for i, item in enumerate(items):
        path = os.path.join(root, item)
        is_last = i == len(items) - 1
        prefix = "`-- " if is_last else "|-- "
        print(indent + prefix + item)
        if os.path.isdir(path):
            new_indent = indent + ("    " if is_last else "|   ")
            print_directory_structure(path, new_indent)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(os.path.basename(base_dir))
    print_directory_structure(base_dir)
