from datetime import datetime

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

with DAG(dag_id='teste_socket_docker', start_date=datetime(2026, 1, 1), schedule=None) as dag:
    
    teste_conexao = DockerOperator(
        task_id='verificar_docker',
        image='hello-world',
        # Aponta para o socket que você acabou de mapear dentro do container
        docker_url='unix://var/run/docker.sock', 
        auto_remove='success'
    )