.PHONY: default mkdir_release install_packages create_actor_env activate deactivate generate_exe

MKDIR_P := mkdir -p

CONDA_HOME = $(HOME)/miniconda3
CONDA_BIN_DIR = $(CONDA_HOME)/bin

ENV_NAME = classroom-downloader
ENV_DIR = $(CONDA_HOME)/envs/$(ENV_NAME)
ENV_BIN_DIR = $(ENV_DIR)/bin
ENV_LIB_DIR = $(ENV_DIR)/lib
ENV_PYTHON = $(ENV_BIN_DIR)/python
ENV_CONDA = $(ENV_BIN_DIR)/conda

default:
	@echo 'python command: $(ENV_PYTHON)'
	@echo 'conda command: $(ENV_CONDA)'

mkdir_release:
	@${MKDIR_P} ./release

install_packages:
	$(ENV_BIN_DIR)/pip install -r requirements.txt

create_actor_env:
	$(CONDA_BIN_DIR)/conda create -n classroom-downloader python=2.7

activate:
	source activate classroom-downloader

deactivate:
	source deactivate

generate_exe: mkdir_release
	@$(ENV_BIN_DIR)/pyinstaller --onefile main.py --name crd --clean \
	--distpath ./release/dist --workpath ./release/build --specpath ./release
