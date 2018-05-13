#!/bin/bash -ex

export DEBIAN_FRONTEND=noninteractive
export LC_ALL=en_US.utf8

printf "Update Ubuntu ..."
sudo apt-get update -y

printf "Install servers ..."
apt-get -y install memcached redis-server postgresql-9.5

printf "Setup Postgresql ..."
sudo -u postgres psql -c "CREATE DATABASE architect"
sudo -u postgres psql -c "CREATE USER architect WITH PASSWORD 'password'"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE architect TO architect"
