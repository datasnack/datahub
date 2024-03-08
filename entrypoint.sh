#!/bin/bash

# wait for PostgreSQL/PostGIS to be ready before running migrations
readonly SLEEP_TIME=2
until PGPASSWORD=$DB_PASSWORD timeout 3 psql -h $DB_HOST -U $DB_USER -c "select 1" -d $DB_NAME > /dev/null
do
  printf "Waiting %s seconds for PostgreSQL to come up: %s@%s/%s...\n" $SLEEP_TIME $DB_USER $DB_HOST $DB_NAME
  sleep $SLEEP_TIME;
done

# Merge/copy local saved data into actual data directory.
# Some data sources are stored locally in the git repo due to complicated/
# unreliable downloads of the source.
# trailing slash is required!
rsync -a data/datalayers.local/ data/datalayers/

python manage.py collectstatic --clear --noinput
python manage.py migrate
python manage.py runserver 0.0.0.0:8000 --noreload

# start gunicorn
#gunicorn --bind 0.0.0.0:80 --timeout 0 datahub.wsgi
