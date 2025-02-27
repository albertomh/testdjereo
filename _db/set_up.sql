/**
 Usage:
 ```
 psql \
   -U $(whoami) \
   -d postgres \
   -v APP_USER_PASSWORD='password' \
   -f _db/set_up.sql
 ```
**/

BEGIN;
CREATE USER testdjereo WITH PASSWORD :'APP_USER_PASSWORD';
ALTER USER testdjereo CREATEDB;
COMMIT;

CREATE DATABASE testdjereo OWNER testdjereo;
