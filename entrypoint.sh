#!/bin/bash

cd /app

# migrate
MIGRATED=1

while true; do
	python3 manage.py migrate --noinput
	if [ "$?" == "0" ]; then
		break;
	else
		echo "unable to migrate, waiting for 5s ..."
		sleep 5
	fi
done

python3 manage.py sync_documents
python3 manage.py sync_inventories
python3 manage.py sync_managers
python3 manage.py sync_monitors
python3 manage.py sync_repositories

echo "from django.contrib.auth.models import User; User.objects.filter(username='$USER_NAME').delete(); User.objects.create_superuser('$USER_NAME', '$USER_EMAIL', '$USER_PASSWORD')" | python3 manage.py shell

exec /usr/local/bin/uwsgi /app/architect/wsgi/uwsgi.ini
