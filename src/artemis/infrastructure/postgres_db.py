import os

from psycopg2 import connect, Error
from dotenv import load_dotenv
from artemis.infrastructure.utils.postgres_cities_api import get_brazilian_cities

load_dotenv(dotenv_path="../../../.env.dev")

class PostgresConnect:
    def __init__ (self):
        self.client = None

    def create_initial_tables(self):
        sql_path = "init_db.sql"
        dicionario_estados = get_brazilian_cities()
        
        if not dicionario_estados:
            print("[ERRO] Não foi possível obter os dados das cidades.")
            return

        try:
            with open(sql_path, "r", encoding="utf-8") as file:
                init_query = file.read()

            with self.client.cursor() as cursor:
                cursor.execute(init_query)
                self.client.commit()
                print("[SUCESSO] Todas as tabelas foram inicializadas")

                insert_query = """
                    INSERT INTO municipios(nome_municipio, id_estado) 
                    VALUES (%s, %s)
                    ON CONFLICT (nome_municipio, id_estado) DO NOTHING;
                """

                cities_query = "SELECT id, sigla FROM estados;"
                cursor.execute(cities_query)
                mapa_estados = {sigla: id for id, sigla in cursor.fetchall()}

                for sigla_estado, cidades in dicionario_estados.items():
                    id_estado_fk = mapa_estados.get(sigla_estado)
                    
                    for nome_cidade in cidades:
                        if nome_cidade:
                            cursor.execute(insert_query, (nome_cidade, id_estado_fk))
                    
                self.client.commit()
                print("[SUCESSO] Todas as cidades brasileiras foram inseridas")

        except Exception as e:
            print(f"[ERRO] Ocorreu um erro ao criar as tabelas iniciais: {e}")
            if self.client:
                self.client.rollback()
       
    def connect(self):
        try:
            self.client = connect(
                database="artemis",
                user="artemis_admin",
                password=os.getenv("POSTGRES_PASSWORD"),
                host="localhost",
                port="5433"
            )

        except Error as e:
            print(f"[ERRO] {e}")

    def disconnect(self):
        if self.client:
            self.client.close()

    def insert_brazilian_cities(self):
        dicionario = get_brazilian_cities()
        print(dicionario.get("GO"))

if __name__ == "__main__":
    conexao = PostgresConnect()
    conexao.connect()
    conexao.create_initial_tables()
    