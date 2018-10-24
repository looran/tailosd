PREFIX=/usr/local
BINDIR=$(PREFIX)/bin

all:
	@echo "Run \"sudo make install\" to install tailosd"
	@echo "   (equivalent to \"sudo python2 setup.py install\""

install:
	python2 setup.py install

clean:
	python2 setup.py clean
	rm -rf build dist tailosd.egg-info
	rm -f *.pyc
