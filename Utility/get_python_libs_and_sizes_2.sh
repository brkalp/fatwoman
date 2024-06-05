#!/bin/bash

# Get the directory where Python libraries are installed
python_lib_dir=$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")

# Get the sizes of all directories in the Python libraries directory
library_sizes=$(du -sh $python_lib_dir/* 2>/dev/null)

# Output the results
echo "$library_sizes"
