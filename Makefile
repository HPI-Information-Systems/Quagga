# makefile for testing, will be deleted once we have proper tests
all: clean
	python -m Quagga.Examples.simpleExample
clean:
	rm -r -f Quagga/Examples/testData/output/*.quagga.*
