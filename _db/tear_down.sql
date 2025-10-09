/**
 Usage:
 ```
 psql \
   -U $(whoami) \
   -d postgres \
   -f _db/tear_down.sql
 ```
**/

SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'testdjereo'
  AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS testdjereo;

DROP USER IF EXISTS testdjereo;

SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'test_testdjereo'
  AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS test_testdjereo;

DROP USER IF EXISTS test_testdjereo;
