#!/bin/bash

# migrate
MIGRATED=1
while true; do
	python manage.py migrate --noinput
	if [ "$?" == "0" ]; then
		break;
	else
		echo "unable to migrate, waiting for 5s ..."
		sleep 5
	fi
done

exec python manage.py runserver 0.0.0.0:8181

