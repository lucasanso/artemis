from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime
from airflow.providers.standard.operators.empty import EmptyOperator 

default_args = {
    'owner': 'artemis',
    'start_date': datetime(2026, 1, 1),
}

with DAG('artemis_scrapy_consumer', default_args=default_args, schedule="@daily", catchup=False) as dag:
    consumer = DockerOperator(
        task_id="consumir",
        image="artemis-scrapy-consumer:latest",
        command="python3 scrapy_kafka_consumer.py",
        network_mode="artemis-network",
        auto_remove='force'
    )

    inicia_processo = EmptyOperator(
        task_id="iniciar"
    )

    encerra_processo = EmptyOperator(
        task_id="encerrar"
    )

    inicia_processo >> consumer >> encerra_processo

    