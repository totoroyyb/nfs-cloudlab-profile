#!/bin/bash

set -x
# make mount /mydata
sudo mkdir -p /mydata
sudo /usr/local/etc/emulab/mkextrafs.pl /mydata
set +x