.PHONY: install data train predict test lint clean docker-build docker-train docker-notebook api streamlit

install:
	pip install -r requirements.txt

data:
	python -m src.data.make_dataset

