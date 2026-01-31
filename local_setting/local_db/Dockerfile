FROM mysql:8.0-debian

COPY ./local_setting/local_db/init.sql /docker-entrypoint-initdb.d/
COPY ./local_setting/local_db/conf.d /etc/mysql/conf.d
RUN chmod 644 /etc/mysql/conf.d/my.cnf
