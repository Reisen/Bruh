#!/bin/bash

supervisord -c /bruh/docker/supervisord.conf

while :
do
    echo "Starting supervisorctl ..."
    supervisorctl -c /bruh/docker/supervisord.conf
done
