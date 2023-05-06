
CONFIG ?= configs/ICE40HX8K-EVB.json

all: build

build:
	python3 buildtool.py ${CONFIG}

clean:
	rm -rf Output/
