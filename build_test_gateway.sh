#! /bin/sh

cd sync_gateway
git checkout circle-build
git submodule init
git submodule update
./build.sh
#cp bin/sync_gateway /usr/local/bin

