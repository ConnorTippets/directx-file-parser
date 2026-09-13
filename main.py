import sys

import src as dtx

if __name__ == "__main__":
    with open(sys.argv[1], "rb") as f:
        contents = f.read()

    print(dtx.parse_x_file(contents))
