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

# collect statics
python manage.py collectstatic --noinput

# start app
# TODO: cznewt - howto start
exec gunicorn app.wsgi:application --bind 0.0.0.0:8000

