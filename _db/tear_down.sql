/**
 Usage:
 ```
 psql \
   -U $(whoami) \
   -d postgres \
   -f _db/tear_down.sql
 ```
**/

DROP DATABASE IF EXISTS testdjereo;

DROP USER IF EXISTS testdjereo;
