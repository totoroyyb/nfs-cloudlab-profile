#!/bin/bash

set -x
# Increases number of open FDs
ulimit -n 1048576
set +x