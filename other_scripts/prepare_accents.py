#!/usr/bin/python3
"""Prepare accents.json dictionary.

"""

import sys
import codecs
import json
from pathlib import Path


def main():
    if sys.argv.__len__() > 1:
        file_name = Path(sys.argv[1])
        assert file_name.exists(), 'File `{0}` does not exist!'.format(file_name)
        with codecs.open(file_name, mode='r', encoding='utf-8', errors='ignore') as fp:
            data = json.load(fp)
        accented_wordforms = sorted(list(set(data[1])))
        data[1] = accented_wordforms
        with codecs.open(file_name, mode='w', encoding='utf-8', errors='ignore') as fp:
            json.dump(data, fp, indent=4, ensure_ascii=False, sort_keys=True)
    else:
        print("Usage: accents.json")


if __name__ == '__main__':
    main()
