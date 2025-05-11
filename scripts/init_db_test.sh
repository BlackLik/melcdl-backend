#!/bin/bash

docker exec -i deployment-db-1 psql -U $POSTGRES_USER -d $POSTGRES_DB <<SQL
    CREATE DATABASE test_db;
    CREATE USER test_user WITH ENCRYPTED PASSWORD 'test_pass';
    GRANT ALL PRIVILEGES ON DATABASE test_db TO test_user;
    \c test_db
    GRANT ALL PRIVILEGES ON SCHEMA public TO test_user;
  SQL
