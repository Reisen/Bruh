#!/bin/bash
# This script is run during container build to get the environment
# bootstrapped.

set -e

# Get walnut
git clone https://github.com/reisen/walnut.git /walnut
mv /walnut/config /config
ln -s /config/config /walnut
ln -s /walnut /bruh

# Add bruh user
useradd bruh --home=/bruh --shell=/bin/bash
echo bruh:bruh | chpasswd
chown -R bruh:bruh /bruh /walnut

# Build
# We use an older version of pip because pyhyphen relies on
# behavior of it.
su -c 'bash -' bruh <<EOF
set -e
# Install bruh deps
cd /bruh
virtualenv env
(. env/bin/activate &&
   pip install pip==6.0.8 &&
   pip install -r requirements.txt &&
   python -c "from hyphen.dictools import install; install('en_US'); install('en_GB')")

cd /walnut
cabal sandbox init
cabal update
cabal install --only-dependencies
EOF
