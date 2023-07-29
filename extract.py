import os
import re
import shutil
from os.path import join
from pathlib import Path

_ = join

def en_filter(src, dst):
	if re.search(r"l_english.yml$", src):
		shutil.copy2(src, dst)


def main():
	extract_path = Path("./extract")
	shutil.rmtree(extract_path, ignore_errors=True)
	os.makedirs(extract_path, exist_ok=True)

	base_path = Path("./tmp/game")

	shutil.copytree(base_path.joinpath(Path("localisation")), extract_path.joinpath(Path("localisation")), copy_function=en_filter)


if __name__ == "__main__":
	# execute only if run as a script
	main()
