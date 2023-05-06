
CONFIG ?= configs/BugblatPIF_2.json

all: build

build:
	python3 buildtool.py ${CONFIG}

clean:
	rm -rf Output/
