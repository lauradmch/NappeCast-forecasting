.PHONY: install data train predict test lint clean docker-build docker-train docker-notebook api streamlit

install:
	pip install -r requirements.txt

data:
	python -m src.data.make_dataset --save-csv --skip-historical

data_histo:
	python -m src.data.make_dataset --save-csv

data_featuring:
	python -m src.data.feat_dataset --save-csv

