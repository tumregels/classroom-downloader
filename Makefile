.PHONY: default test install uninstall clean realclean


CONDA_HOME = $(HOME)/miniconda2
CONDA_BIN_DIR = $(CONDA_HOME)/bin

ENV_NAME = classroom
ENV_DIR = $(CONDA_HOME)/envs/$(ENV_NAME)
ENV_BIN_DIR = $(ENV_DIR)/bin
ENV_LIB_DIR = $(ENV_DIR)/lib
ENV_PYTHON = $(ENV_BIN_DIR)/python
ENV_CONDA = $(ENV_BIN_DIR)/conda

default:
	@echo 'python command: $(ENV_PYTHON)'
	@echo 'conda command: $(ENV_CONDA)'

pyinstaller:
	@$(ENV_BIN_DIR)/pyinstaller --onefile main.py --name classroom-downloader \
	--distpath ./release/dist --workpath ./release/build --specpath ./release