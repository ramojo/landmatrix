# postgis instructions

The postgis extension to PostgreSQL needs to be installed for the maplandmatrix app to run.

## Installing postgis on your system
It's not trivial, because it's neither in the official debian nor ubuntu repositories :-(

`<insert instructions to install postgis on the system here.>`

## Installing postgis on your Postgres DB
```
sudo -u postgres psql $DB -c 'create extension postgis;'
```

## Getting the postgis extension installed on the test DB

To install postgis on the test DB on every test run does not work out of the box due to:
`django.db.utils.ProgrammingError: permission denied to create extension "postgis"
HINT:  Must be superuser to create this extension.`

Solution (found here: http://calvinx.com/2012/12/05/geodjango-postgis-test-databases/):
```
$ sudo -U postgres psql -c "CREATE DATABASE template_postgis ENCODING='utf-8';"
$ sudo -U postgres psql -c "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis';"
$ POSTGIS_SQL_PATH=$(dirname $(locate /postgis.sql))
$ sudo -U postgres psql -d template_postgis -f $POSTGIS_SQL_PATH/postgis.sql
$ sudo -U postgres psql -d template_postgis -f $POSTGIS_SQL_PATH/spatial_ref_sys.sql
$ sudo -U postgres psql -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"
$ sudo -U postgres psql -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"
$ sudo -U postgres psql -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"
```