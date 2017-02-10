PREFIX=/usr/local
BINDIR=$(PREFIX)/bin

all:
	@echo "Run \"sudo make install\" to install tailosd"
	@echo "   (equivalent to \"sudo python setup.py install\""

install:
	python setup.py install

clean:
	python setup.py clean
	rm -rf build dist tailosd.egg-info
	rm *.pyc
