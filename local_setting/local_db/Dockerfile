FROM mysql:8

COPY ./local_setting/local_db/init.sql /docker-entrypoint-initdb.d/
# COPY ./local-db/insert_dummy_locations.sql /docker-entrypoint-initdb.d/
COPY ./local_setting/local_db/conf.d /etc/mysql/conf.d
RUN chmod 644 /etc/mysql/conf.d/my.cnf
