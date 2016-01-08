#! /bin/sh

#mkdir -p /opt
#apt-get update
#apt-get -q -y install git bc wget build-essential
#wget https://storage.googleapis.com/golang/go1.4.2.linux-amd64.tar.gz
#
#tar -C /usr/local -xzf go1.4.2.linux-amd64.tar.gz
#
#export PATH=$PATH:/usr/local/go/bin

cd /opt

git clone https://github.com/couchbase/sync_gateway.git

cd /opt/sync_gateway
git submodule init
git submodule update
./build.sh
cp bin/sync_gateway /usr/local/bin

mkdir -p /opt/sync_gateway/data
rm go1.4.2.linux-amd64.tar.gz
rm -rf /opt/sync_gateway