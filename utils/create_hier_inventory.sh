#!/bin/bash -ex

mkdir -p /srv/architect/mcp/classes/overrides
mkdir -p /srv/architect/mcp/classes/service
mkdir -p /srv/architect/mcp/classes/cluster/sample/infra
mkdir -p /srv/architect/mcp/nodes/sample-deploy

if [ ! -d "/srv/architect/mcp/classes/system" ]; then
  git clone https://github.com/Mirantis/reclass-system-salt-model /srv/architect/mcp/classes/system
fi;

if [ ! -d "/srv/salt-formulas" ]; then
  git clone https://github.com/salt-formulas/salt-formulas.git --recursive /srv/salt-formulas
fi;

for i in /srv/salt-formulas/formulas/* ; do
  if [ -d "$i" ]; then
    service=$(basename "$i")
    formula="${service/-/_}"
    if [ -d "/srv/salt-formulas/formulas/$service/metadata/service" ]; then
      if [ ! -L "/srv/architect/mcp/classes/service/$formula" ]; then
        ln -s "/srv/salt-formulas/formulas/$service/metadata/service" "/srv/architect/mcp/classes/service/$formula"
      fi;
    fi;
  fi;
done

cat << EOF > /srv/architect/mcp/classes/cluster/sample/infra/config.yml
classes:
- service.git.client
- system.linux.system.single
- system.linux.system.repo.mcp.salt
- system.salt.master.pkg
parameters:
  _param:
    salt_master_host: 127.0.0.1
    salt_master_environment_name: dev
    salt_master_environment_repository: https://github.com/salt-formulas
    salt_master_environment_revision: master
    salt_minion_ca_authority: salt_master_ca
  salt:
    master:
      user:
        salt:
          permissions:
          - '.*'
          - '@local'
          - '@wheel'   # to allow access to all wheel modules
          - '@runner'  # to allow access to all runner modules
          - '@jobs'    # to allow access to the jobs runner and/or wheel modules
      engine:
        architect:
          engine: architect
          project: sample-deploy
          host: 127.0.0.1
          port: 8181
          username: architect
          password: password
EOF

cat << EOF > /srv/architect/mcp/classes/overrides/sample-deploy.yml
parameters:
  _param:
    cluster_name: sample-deploy
    cluster_domain: sample.deploy
EOF

cat << EOF > /srv/architect/mcp/nodes/sample-deploy/cfg01.sample.deploy.yml
classes:
- cluster.sample.infra.config
- overrides.sample-deploy
parameters:
  _param:
    linux_system_codename: xenial
  linux:
    system:
      name: cfg01
      domain: sample.deploy
EOF
