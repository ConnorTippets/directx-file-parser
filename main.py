import src as dtx

import sys

if __name__ == "__main__":
    with open(sys.argv[1], "r") as f:
        contents = f.read()

    print(dtx.parse_x_file(contents, dtx.XFileMode.TEXT_MODE))
