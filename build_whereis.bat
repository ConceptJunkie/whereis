copy whereis.py whereis.pyx
python setup_whereis.py build
move build\lib.win-amd64-3.6\whereis.cp36-win_amd64.pyd
del /sxyz build
del whereis.pyx

