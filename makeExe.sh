#!/bin/bash
conda activate PaperOracle
pyinstaller  --copy-metadata tqdm  --copy-metadata regex --copy-metadata requests --copy-metadata packaging --copy-metadata filelock --copy-metadata numpy --copy-metadata tokenizers UI.py
