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

sudo git clone https://github.com/couchbase/sync_gateway.git

sudo cd /opt/sync_gateway
sudo git submodule init
sudo git submodule update
sudo ./build.sh
sudo cp bin/sync_gateway /usr/local/bin

sudo mkdir -p /opt/sync_gateway/data
sudo rm go1.4.2.linux-amd64.tar.gz
sudo rm -rf /opt/sync_gateway