# run as root
# build synclink tools
tar xJvf linuxwan.tar.xz
cd synclink/tools
make
make install
# build drivers requirements for raspberry
apt-get install raspberrypi-kernel-headers -y
# setup drivers
cd ../drivers
./setup
cd ../..
# copy python scripts
cp -rf python/ synclink/python/
# install python mgapi
