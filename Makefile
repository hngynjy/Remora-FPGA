
CONFIG ?= configs/ICE40HX8K-EVB.json

all: build

build:
	python3 buildtool.py ${CONFIG}

clean:
	rm -rf Output/

format:
	black buildtool.py plugins/*/*.py

isort:
	isort buildtool.py plugins/*/*.py

flake8:
	flake8 --max-line-length 200 buildtool.py plugins/*/*.py

mypy:
	mypy buildtool.py plugins/*/*.py

check: isort flake8 mypy
