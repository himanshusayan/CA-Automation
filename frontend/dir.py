import os

def print_tree(dir_path, prefix="", file=None):
    items = os.listdir(dir_path)
    items.sort()
    for index, item in enumerate(items):
        path = os.path.join(dir_path, item)
        is_last = index == len(items) - 1
        connector = "└── " if is_last else "├── "
        line = prefix + connector + item + "\n"
        file.write(line)
        if os.path.isdir(path):
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(path, new_prefix, file)

if __name__ == "__main__":
    output_file = "tree.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        print_tree(".", file=f)
    print(f"Tree written to {output_file}")
