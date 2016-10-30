setup : data/dump.tar.gz
	tar -xzvf data/dump.tar.gz -C data/
	python3 data/name_symlinks.py data/pokemon
	python3 data/name_symlinks.py data/move
	python3 data/name_symlinks.py data/ability
	python3 data/name_symlinks.py data/pokemon-species
	
