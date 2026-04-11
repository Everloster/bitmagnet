#!/bin/sh
echo "nameserver 192.168.55.10" > /etc/resolv.conf
exec /usr/bin/bitmagnet "$@"
