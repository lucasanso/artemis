import json
import os
from datetime import date

import pymongo
from confluent_kafka import Consumer, KafkaError
from dotenv import load_dotenv
from pymongo.errors import DuplicateKeyError
from scrapy_kafka_processor import TransformData

load_dotenv(dotenv_path=".env.consumer")
# from minio import Minio
# from datetime import datetime
# import io

# Configurações do Broker
conf = {
    # alterado host de localhost para broker
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'artemis-scrapy-consumer', 
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True
}

class KafkaPyConsumer:
    def __init__(self):
        self.consumer = Consumer(conf)
        self.consumer.subscribe([os.getenv("KAFKA_TOPIC")])
        self.client = None
        # Configurações MinIO
        # self.minio_configs = configs['minio']
        # self.minio_client = Minio(
        #     self.minio_configs['endpoint'],
        #     access_key=self.minio_configs['access_key'],
        #     secret_key=self.minio_configs['secret_key'],
        #     secure=self.minio_configs['secure']
        # )

        print(f"[PROCESO] Iniciando Consumer no grupo: {conf['group.id']}")
        print(f"[PROCESSO] Aguardando mensagens do tópico '{os.getenv("KAFKA_TOPIC")}'...")

        # self._ensure_bucket_exists()

    # def _ensure_bucket_exists(self):
    #     bucket = self.minio_configs['bucket_name']
    #     if not self.minio_client.bucket_exists(bucket):
    #         self.minio_client.make_bucket(bucket)
    #         print(f"[MINIO] Bucket '{bucket}' criado.")

    # def upload_to_minio(self, content: dict, filename: str):
    #     """Converte o dict em JSON e envia para o MinIO"""
    #     try:
    #         # Converter dict para bytes
    #         json_data = json.dumps(content, ensure_ascii=False, default=str).encode('utf-8')
    #         data_stream = io.BytesIO(json_data)
            
    #         self.minio_client.put_object(
    #             self.minio_configs['bucket_name'],
    #             f"news/{filename}.json",
    #             data_stream,
    #             length=len(json_data),
    #             content_type='application/json'
    #         )
    #     except Exception as e:
    #         print(f"[ERRO MINIO] Falha ao fazer upload: {e}")

    def queue_monitoring(self):
        try:
            while True:
                msg = self.consumer.poll(5.0) 

                if msg is None:
                    print("[AVISO] A fila está vazia. Monitorando...")
                    continue
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        print(f"[AVISO] Fim da partição {msg.topic()} [{msg.partition()}]")
                    else:
                        print(f"[ERRO] Erro no Kafka: {msg.error()}")
                        break
                else:
                    try:
                        content = json.loads(msg.value().decode("utf-8"))
                
                        if content.get("accepted_by"):
                            content["acquisition_date"] = self.processing(content.get("acquisition_date"))
                            content["publication_date"] = self.processing(content.get("publication_date"))
                            content["last_update"] = self.processing(content.get("last_update"))
                            content["article"] = TransformData.clean_string(content.get("article"))
                            self.accepted_news_collection.insert_one(content)
                            # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

                            # # Opcional: Manter o id_event junto ao timestamp para unicidade absoluta
                            # file_name = f"news_{timestamp}_id{content.get('id_event', 'unknown')}"

                            # self.upload_to_minio(content, file_name)
                            # print(f"[SUCESSO] JSON enviado para o MinIO: {file_name}.json")
                            print("[SUCESSO] Notícia aceita inserida")

                        else:
                            if content.get("url") is None or not content.get("url"):
                                continue

                            self.unaccepted_news_collection.insert_one(content)
                            # Opcional: Manter o id_event junto ao timestamp para unicidade absoluta
                            # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            # file_name = f"news_{timestamp}_id{content.get('id_event', 'unknown')}"

                            # self.upload_to_minio(content, file_name)
                            # print(f"[SUCESSO] JSON enviado para o MinIO: {file_name}.json")
                            print("[SUCESSO] Notícia recusada inserida") 
                            
                    except DuplicateKeyError:
                        print("[AVISO] Notícia já está no banco")

                    # except AttributeError:
                    #     print(f"[ERRO] Tem algo de errado com a formatação: {content}")
                
        except KeyboardInterrupt:
            print("\n[AVISO] Encerrando consumer...")
        finally:
            self.consumer.close()

    def establishing_conns(self):
        try:    
            self.client = pymongo.MongoClient(os.getenv("MONGO_DB_URI"))
            self.accepted_news_collection = self.client.get_database(os.getenv("MONGO_DB_DATABASE")).get_collection(os.getenv("MONGO_DB_ACCEPTED"))
            self.unaccepted_news_collection = self.client.get_database(os.getenv("MONGO_DB_DATABASE")).get_collection(os.getenv("MONGO_DB_UNACCEPTED"))

        except Exception as e:
            print(f"[ERRO] Erro ao estabelecer conexão SSH {e}")
    
    def processing(self, date_field: str) -> date:
        lista_processamento = [
            TransformData.cvt_timestampz_to_date,   
            TransformData.clean_string,   
            TransformData.bar_date_processing,      
            TransformData.string_date_processing,    
            TransformData.cvt_inverted_date,   
        ]
        
        for method in lista_processamento:
            date_field = method(date_field)

        return date_field

if __name__ == "__main__":
    consumindo = KafkaPyConsumer()

    consumindo.establishing_conns()
    consumindo.queue_monitoring()
