FROM debian:stretch

ARG version=2018.3
ENV VERSION $version

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -qq update && \
  apt-get install -y wget gnupg2 && \
  wget -O - https://repo.saltstack.com/apt/debian/9/amd64/latest/SALTSTACK-GPG-KEY.pub | apt-key add - && \
  echo "deb http://repo.saltstack.com/apt/debian/9/amd64/${VERSION} stretch main" >/etc/apt/sources.list.d/saltstack.list && \
  apt-get update && apt-get install -y salt-master salt-api pwgen python-pip && \
  pip install architect-client && \
  mkdir -p /var/run/salt /etc/salt/pki/master/minions && \
  apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN useradd --system salt && \
  chown -R salt:salt /etc/salt /var/cache/salt /var/log/salt /var/run/salt && \
  echo "user: salt" >> /etc/salt/master

ENV TINI_VERSION 0.14.0
ENV TINI_SHA 6c41ec7d33e857d4779f14d9c74924cab0c7973485d2972419a3b7c7620ff5fd

# Use tini as subreaper in Docker container to adopt zombie processes
RUN wget https://github.com/krallin/tini/releases/download/v${TINI_VERSION}/tini-static-amd64 -O /bin/tini && chmod +x /bin/tini \
  && echo "$TINI_SHA  /bin/tini" | sha256sum -c -

# Install molten
ENV MOLTEN_VERSION 0.3.1
ENV MOLTEN_MD5 04483620978a3167827bdd1424e34505
ADD https://github.com/martinhoefling/molten/releases/download/v${MOLTEN_VERSION}/molten-${MOLTEN_VERSION}.tar.gz molten-${MOLTEN_VERSION}.tar.gz
RUN echo "${MOLTEN_MD5}  molten-${MOLTEN_VERSION}.tar.gz" | md5sum --check
RUN mkdir -p /opt/molten && tar -xf molten-${MOLTEN_VERSION}.tar.gz -C /opt/molten --strip-components=1

VOLUME ['/etc/salt/pki', '/srv/salt' '/etc/salt/master.d']
ADD files/architect.py /srv/salt-engines/

EXPOSE 4505 4506 8000

COPY files/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/bin/tini", "--", "/entrypoint.sh"]
