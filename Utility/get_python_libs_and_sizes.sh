#!/bin/bash

# Get a list of installed packages
packages=$(pip list --format=freeze | cut -d= -f1)

# Iterate over each package
for package in $packages
do
    # Get the directory of the package
    package_dir=$(pip show $package | awk '/^Location:/ {print $2}')

    # Get the size of the directory
    size=$(du -sh "$package_dir" | awk '{print $1}')

    # Output package name and size
    echo "$package: $size"
	pip show $package
done

#Name: aiohttp
#Version: 3.9.3
#Summary: Async http client/server framework (asyncio)
#Home-page: https://github.com/aio-libs/aiohttp
#Author: None
#Author-email: None
#License: Apache 2
#Location: /home/fatwoman/.local/lib/python3.8/site-packages
#Requires: async-timeout, aiosignal, attrs, multidict, frozenlist, yarl
#Required-by: python-binance