FROM apache/airflow:2.9.0-python3.12

USER root
RUN apt-get update && apt-get install -y jq && apt-get clean
USER airflow
