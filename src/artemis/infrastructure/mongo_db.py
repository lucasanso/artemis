import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv(dotenv_path=".env.dev")

class MongoDatabase:
    def __init__(self):
        print("[PROCESSO] Inicializando conexão com o MongoDB")
        self.uri = os.getenv("MONGO_DB_URI")
        self.client = None

    def connect(self):
        try:
            self.client = MongoClient(self.uri)
        except ConnectionFailure as e:
            print(f"[ERRO] Erro ao conectar com o banco {os.getenv("MONGO_DB_DATABASE")} do MongoDB: {e}")
            self.client = None

    def close(self):
        if self.client:
            self.client.close()
            print("[AVISO] Conexão com o MongoDB foi encerrada")

    # @property
    # def get_connection(self):
    #     if self.client is None:
    #         self.connect()

    #     return self.client


# Ideia interessante: ao ser importado já chega instanciado 
mongo = MongoDatabase()