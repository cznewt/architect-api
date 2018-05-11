#!/usr/bin/env bash

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

printf "Installing Python 3 dependencies..."
apt-get -y install python-virtualenv python3-dev python3-pip libxml2-dev libxslt1-dev libffi-dev graphviz libpq-dev libssl-dev

printf "Upgrading pip"
pip3 install --upgrade pip

mkdir -p /etc/architect
cat << EOF > /etc/architect/api.yml
databases:
  default:
    ENGINE: django.db.backends.postgresql_psycopg2
    NAME: architect
    USER: architect
    PASSWORD: password
    HOST: 127.0.0.1
    PORT: 5432
caches:
  default:
    BACKEND: django.core.cache.backends.memcached.MemcachedCache
    LOCATION: 127.0.0.1:11211
inventory:
  sample-cluster:
    engine: hier-cluster
    service_class_dir:
    system_class_dir:
    cluster_class_dir:
    class_dir: /srv/architect/mcp/classes
    formula_dir: /srv/salt-formulas/formulas
  sample-deploy:
    engine: hier-deploy
    class_dir: /srv/architect/mcp/classes
    node_dir: /srv/architect/mcp/nodes/sample-deploy
EOF

git clone https://github.com/cznewt/architect-api.git /opt/architect
cd /opt/architect

printf "Installing architect-api code"
virtualenv -p python3 venv
. venv/bin/activate
pip install -r requirements/base.txt
pip install psycopg2-binary
pip install git+https://github.com/salt-formulas/reclass.git@python3

printf "Installing static files tools"
apt-get -y install npm rubygems ruby-dev

sudo gem install sass --no-user-install

npm install

python manage.py collectstatic --noinput
python manage.py compress
python manage.py migrate

# Now you can run following 2 services

# python manage.py runserver 0.0.0.0:8181

# celery -A architect worker -l info
