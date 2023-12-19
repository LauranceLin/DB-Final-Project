# FurAlert!

## Backup Existing Database

In the root directory, run the following to restore our existing database:
Here we assume the username is postgres.

```
pg_restore -h localhost -p 5432 -U postgres -v -Fc sql/furalert_db_backup.sql --schema=public -d furalert
```

## Dependencies

The `backend` directory will be where we run everything from.

`cd backend`

1. We initialize a python virtual environment and activate it:

```
virtualenv venv

source venv/bin/activate

pip install -r requirements.txt
```

## Run Application

`cd backend`

Open 3 terminals and run each of the following scripts in one of the terminals:

```
# terminal 1
./run-flask.sh

# terminal 2
./run-celery.sh

# terminal 3
./run-redis.sh
```

- `run-flask.sh`: the flask application
- `run-celery.sh`: the celery worker that sends out our notifications. Since notification insertion may take up a lot of time, we separate it to a background process to prevent lagging for the event reporter.
- `run-redis.sh`: acts as the broker for celery worker

Note that `run-redis.sh` has some additional dependencies(ex. `curl`, `tar`), since it compiles the stable version of redis on our machine. Make sure to install them when encountering any errors.
