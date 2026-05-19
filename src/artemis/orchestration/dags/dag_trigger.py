from datetime import datetime
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.empty import EmptyOperator
from airflow.decorators import task
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

default_args = {
    'owner': 'artemis',
    'start_date': datetime(2026, 1, 1),
}

with DAG('artemis_extraction_pipeline', default_args=default_args, schedule='@daily', catchup=False) as dag:

    inicia_processo = EmptyOperator(
        task_id="iniciar"
    )

    # scrapy_consumer = DockerOperator(
    #     task_id='iniciar_consumer_scrapy',
    #     image='artemis-scrapy-consumer',
    #     command='python3 scrapy_kafka_consumer.py',
    #     network_mode='artemis-network',
    #     auto_remove='force'
    # )

    brasil_de_fato = DockerOperator(
        task_id='rodar_crawler_bdf',
        image='artemis-scrapy:latest',
        command='scrapy crawl bdf -s CLOSESPIDER_TIMEOUT=300',
        network_mode='artemis-network',
        auto_remove='force',
        # environment={
        #     'KAFKA_TOPIC': 'raw_news',
        #     'MONGO_DB_DATABASE': 'news'
        # }
    )

    # folha_sp = DockerOperator(
    #     task_id='rodar_crawler_fsp',
    #     image='artemis-scrapy:latest',
    #     command='scrapy crawl folha -s CLOSESPIDER_TIMEOUT=30',
    #     network_mode='artemis-network',
    #     auto_remove='force',
    # )

    # diplomatique = DockerOperator(
    #     task_id='rodar_diplomatique',
    #     image='artemis-scrapy:latest',
    #     command='scrapy crawl diplomatique -s CLOSESPIDER_TIMEOUT=30',
    #     network_mode='artemis-network',
    #     auto_remove='force',
    # )

    # chama_consumer = TriggerDagRunOperator(
    #     task_id="chama_consumer",
    #     trigger_dag_id="artemis_scrapy_consumer",  # ID exato da DAG que deve começar
    #     wait_for_completion=False,       # False = Dispara e finaliza a DAG A. True = Segura a DAG A até a B terminar.
    #     poke_interval=60,
    # )

    # consumer = DockerOperator(
    #     task_id="consumir",
    #     image="artemis-scrapy-consumer:latest",
    #     command="python3 scrapy_kafka_consumer.py",
    #     network_mode="artemis-network",
    #     auto_remove='force'
    # )

    encerra_processo = EmptyOperator(
        task_id="encerrar"
    )

    inicia_processo >> [brasil_de_fato] >> encerra_processo