#!/bin/bash

supervisord -c /bruh/docker/supervisord.conf
echo "Starting supervisorctl ..."
exec supervisorctl -c /bruh/docker/supervisord.conf
