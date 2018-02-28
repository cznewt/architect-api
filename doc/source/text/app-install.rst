
===============================
Architect Services Installation
===============================

Following steps show how to deploy various components of the Architect service
and connections to external services. It covers the basic development
deployment.


Service ``architect-api`` Installation
======================================

The core service responsible for handling HTTP API requests and providing
simple UI based on Material design. Release version of architect-api is
currently available on `Pypi <https://pypi.org/project/architect-api/>`_, to
install it, simply execute:

.. code-block:: bash

    pip install architect-api

To bootstrap latest development version into local virtualenv, run following
commands:

.. code-block:: bash

    virtualenv venv -p python3
    source venv/bin/activate

    git clone git@github.com:cznewt/architect-api.git

    cd architect-api

    python setup.py install

Or you you can install service by pip ``architect-api`` package.

.. code-block:: bash

    virtualenv venv
    source venv/bin/activate

    pip install architect-api -e


Initial Setup for UI
--------------------

Architect-api uses the ``npm`` to install its JavaScript dependencies, which
are collected by ``django-npm`` static files collector. You can install all
static nodesj libraries by following commands. More about installing Node.js
and NPM can be found at https://www.npmjs.com/get-npm.

.. code-block:: bash

    apt install npm

    cd architect-api

    npm install

Architect uses the Bootstrap 4 library wich uses SASS 3.5 style preprocessing.
No python SASS interpreter does it well so we need to get the ruby's gems this
time. The static file compress utility uses this ruby binary to perform the
processing of SASS styles. You can install the SASS compiler by following
commands. More about installing SASS can be found at
http://sass-lang.com/install.

.. code-block:: bash

    apt install gem ruby-dev

    sudo gem install sass --no-user-install

    sass --version

The ``saas --version`` command should return Sass 3.5 or higher.


Now you can collect all your static assets, run following command in architect
base dir and sourced.

.. code-block:: bash

    # python manage.py collectstatic --noinput

    X static files copied to '/python-apps/architect/static', Y unmodified.


Now you can compress and compile your static assets, in architect base dir and
sourced run following command.

.. code-block:: bash

    # python manage.py compress

    Found 'compress' tags in:
        /python-apps/architect/architect/templates/_head.html
        /python-apps/architect/architect/templates/_body.html


Initial Setup for Database
--------------------------

You must synchronise your database content with the current migration scheme,
command will create entire schema and apply all the migrations if run for the
first time. In architect base dir and sourced run following command.

.. code-block:: bash

    python manage.py migrate

You need also setup your user credentials if creating a new deployment.

.. code-block:: bash

    python manage.py createsuperuser

You can install sample metadata fixtures by following command.

.. code-block:: bash

    # python manage.py loaddata sample_saltstack

    Installed 614 object(s) from 2 fixture(s)

You must set database configuration by settings in architect-api configuration
file. Example PostgreSQL settings in architect-api configuration file.

.. code-block:: yaml

    databases:
      default:
        ENGINE: django.db.backends.postgresql_psycopg2
        NAME: architect
        USER: architect
        PASSWORD: password
        HOST: 127.0.0.1
        PORT: 5432

The similar applies for the cache backend, which can be changed to the
Memcached backend, for example:

.. code-block:: yaml

    caches:
      default:
        BACKEND: django.core.cache.backends.memcached.MemcachedCache
        LOCATION: 127.0.0.1:11211


Main Configuration File
-----------------------

You provide one YAML configuration file for all settings. The default
location is ``/etc/architect/api.yaml``.

You can setup basic configuration of database and cache also you can provide
defaults for your initial inventories, managers and monitors.

You can override the default location of the configuration file by setting the
``ARCHITECT_CONFIG_FILE`` environmental variable to your custom location.

The configuration file currently supports following options:

.. code-block:: yaml

    databases:
      default:
        ENGINE: django.db.backends.postgresql_psycopg2
        ...
    caches:
      default:
        BACKEND: django.core.cache.backends.memcached.MemcachedCache
        ...
    monitor:
      monitor01:
        name: Dashboard 01
        ...
    manager:
      manager01:
        engine: salt
        ...
    inventory:
      inventory01:
        engine: reclass
        ...

The ``databases`` and ``caches`` keys are used in the application settings.
But the ``monitor``, ``manager`` and ``inventory`` configuration settings need
to be sychronised to database by management commands in architect base dir and
sourced.

.. code-block:: bash

    # python manage.py sync_inventories

    Inventory "inventory01" resource updated
    ...

    # python manage.py sync_managers

    Manager "manager01" resource updated
    ...

    # python manage.py sync_monitors

    Monitor "monitor01" resource updated
    ...

You can run the configuration multiple times and update existing resources.
The actual resources used are stored in the database and can be changed at the
architect's admin app available at http://127.0.0.1:8181/admin/ after you
start the development server.

Look at the the documentation pages for individual inventory, manager or
monitor configuration options and installation problems.


Running Development Server
--------------------------

To start development server, in architect base dir and sourced run following
command.

.. code-block:: bash

    # python manage.py runserver 0.0.0.0:8181

    Performing system checks...

    System check identified no issues (0 silenced).
    January 27, 2018 - 13:12:47
    Django version 2.0.1, using settings 'architect.settings'
    Starting development server at http://0.0.0.0:8181/
    Quit the server with CONTROL-C.



Service ``architect-worker`` Installation
=========================================

The architect relies on standalone workers to perform the tasks
asynchronously. For the development environment, you can just simply install
redis server to serve as message bus by following command.

.. code-block:: bash

    apt install redis server

Now you can start running your architect worker instances. The redis is
hardcoded and celery can be replaced by airflow, this is up to discussion.


Running development worker
--------------------------

To start development worker, in architect base dir and sourced run following
command.

.. code-block:: bash

    # celery -A architect worker -l info

     -------------- celery@wst01 v4.1.0 (latentcall)
    ---- **** -----
    --- * ***  * -- Linux-4.10.0-42
    -- * - **** ---
    - ** ---------- [config]
    - ** ---------- .> app:         architect:0x7ff566a38e80
    - ** ---------- .> transport:   redis://localhost:6379//
    - ** ---------- .> results:     redis://localhost:6379/
    - *** --- * --- .> concurrency: 4 (prefork)
    -- ******* ---- .> task events: OFF
    --- ***** -----
     -------------- [queues]
                    .> celery           exchange=celery(direct) key=celery

    [tasks]
      . architect.celery.debug_task
      . get_manager_status_task

    [2018-01-27 13:15:55,852: INFO/MainProcess] Connected to redis://localhost:6379//
    [2018-01-27 13:15:55,860: INFO/MainProcess] mingle: searching for neighbors
    [2018-01-27 13:15:56,880: INFO/MainProcess] mingle: all alone
    [2018-01-27 13:15:56,892: INFO/MainProcess] celery@<your-node-hostname> ready.

You should see ``celery@<your-node-hostname> ready`` in the output of the
command run. If not, check if redis service ``systemctl status redis-server``
is running. You need at least one instance of worker running.


Service ``architect-client`` Installation
=========================================

Following steps show how to deploy and configure Architect Client. You need to
install client on configuration management servers to integrate the inventory
service.

.. code-block:: bash

    pip install architect-client

Create configuration file ``/etc/architect/client.yml`` for client.

.. code-block:: yaml

    project: project-name
    host: architect-api
    port: 8181
    username: salt
    password: password
