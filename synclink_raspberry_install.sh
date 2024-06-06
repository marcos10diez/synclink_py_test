# run as root
# build synclink tools
tar xJvf linuxwan.tar.xz
cd synclink/tools
# instalar make
sudo apt-get install build-essential
make
make install
# build drivers requirements for raspberry
apt-get install raspberrypi-kernel-headers -y
# setup drivers
cd ../drivers
./setup
cd ../..
# copy python scripts
cp -rf python/ synclink/
# install python mgapi
cd python
sudo apt install python3-pip -y
pip install mgapi.tar.gz
