#!/bin/sh

cat FA2.py utests/*.py main_FA2.py > /tmp/test.py
~/smartpy-cli/SmartPy.sh test /tmp/test.py out --purge --html
