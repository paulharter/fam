#! /bin/sh

#mkdir -p /opt
#apt-get update
#apt-get -q -y install git bc wget build-essential
#wget https://storage.googleapis.com/golang/go1.4.2.linux-amd64.tar.gz
#
#tar -C /usr/local -xzf go1.4.2.linux-amd64.tar.gz
#
#export PATH=$PATH:/usr/local/go/bin


sudo git clone git@github.com:paulharter/sync_gateway.git
sudo cd sync_gateway
sudo git submodule init
sudo git submodule update
sudo ./build.sh
sudo cp bin/sync_gateway /usr/local/bin

