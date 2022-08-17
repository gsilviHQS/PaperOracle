#!/bin/bash
conda activate PaperOracle
# pyinstaller --hidden-import="pkg_resources.py2_warn" --hidden-import="googleapiclient" --hidden-import="apiclient"  --copy-metadata tqdm --copy-metadata regex --copy-metadata requests --copy-metadata packaging --copy-metadata filelock --copy-metadata numpy --copy-metadata tokenizers  --hidden-import=“sklearn.utils._cython_blas” --hidden-import=“sklearn.neighbors.typedefs” --hidden-import=“sklearn.neighbors.quad_tree” --hidden-import=“sklearn.tree” --hidden-import=“sklearn.tree._utils” UI.py
pyinstaller  --copy-metadata tqdm  --copy-metadata regex --copy-metadata requests --copy-metadata packaging --copy-metadata filelock --copy-metadata numpy --copy-metadata tokenizers UI.py
