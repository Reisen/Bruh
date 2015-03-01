#!/bin/bash
# This script is run during container build to get the environment
# bootstrapped.

set -e

# Get and build walnut
git clone https://github.com/reisen/walnut.git /walnut
cd /walnut
cabal sandbox init
cabal update
cabal install --only-dependencies
ln -s /config/config /walnut
ln -s /walnut/drivers /bruh

# Install bruh deps
cd /bruh
virtualenv env
(. env/bin/activate && pip install -r requirements.txt &&
                       pip install pyhyphen)

# Add bruh user
useradd bruh --home=/bruh --shell=/bin/bash
echo bruh:bruh | chpasswd
chown -R bruh:bruh /bruh /walnut

# Generate host keys
ssh-keygen -N '' -t dsa -f /etc/ssh/ssh_host_dsa_key
ssh-keygen -N '' -t rsa -f /etc/ssh/ssh_host_rsa_key
sed -i /etc/ssh/sshd_config -e 's/^UsePAM .*/UsePAM no/'
