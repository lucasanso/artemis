import json
import os
from datetime import date
import pymongo
from confluent_kafka import Consumer, KafkaError
from dotenv import load_dotenv
from pymongo.errors import DuplicateKeyError
from scrapy_kafka_processor import TransformData
from datetime import timedelta, datetime

load_dotenv(dotenv_path="../../../.env.dev")

# Configurações do Broker
conf = {
    # alterado host de localhost para broker
    'bootstrap.servers': 'broker:29092',
    'group.id': 'artemis-scrapy-consumer', 
    'auto.offset.reset': 'earliest'
}

# Tempo de consumo do Kafka com timeout configurado
class KafkaPyConsumer:
    def __init__(self):
        self.consumer = Consumer(conf)
        self.consumer.subscribe([os.getenv("KAFKA_TOPIC")])
        self.client = None

        print(f"[PROCESSO] Iniciando Consumer no grupo: {conf['group.id']}")
        print(f"[PROCESSO] Aguardando mensagens do tópico {os.getenv('KAFKA_TOPIC')}...")

    def queue_monitoring(self, timeout=30):
        now = datetime.now()
        end = now + timedelta(seconds=timeout)
        print(f"[AVISO] Timeout configurado: {timeout}s")
        try:
            while datetime.now() < end:
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
                
                        if content.get("aceito_por"):
                            content["data_coleta"] = self.processing(content.get("data_coleta"))
                            content["data_noticia"] = self.processing(content.get("data_noticia"))
                            content["corpo_texto"] = TransformData.clean_string(content.get("corpo_texto"))
                            self.accepted_news_collection.insert_one(content)
                        
                            print("[SUCESSO] Notícia aceita inserida")

                        else:
                            if content.get("url") is None or not content.get("url"):
                                continue
                            unaccepted = {
                                'url' : content.get('url')
                            }
                            self.unaccepted_news_collection.insert_one(unaccepted)
                            
                            print("[SUCESSO] Notícia recusada inserida")

                    except DuplicateKeyError:
                        print("[AVISO] Notícia já está no banco")

            print("[SUCESSO] Consumer finalizado")

        except KeyboardInterrupt:
            print("\n[AVISO] Encerrando consumer de maneira forçada...")
        finally:
            self.consumer.close()

    def establishing_conns(self):
        try:    
            self.client = pymongo.MongoClient(os.getenv("MONGO_DB_URI"))
            self.accepted_news_collection = self.client.get_database(os.getenv("MONGO_DB_DATABASE")).get_collection(os.getenv("MONGO_DB_ACCEPTED"))
            self.unaccepted_news_collection = self.client.get_database(os.getenv("MONGO_DB_DATABASE")).get_collection(os.getenv("MONGO_DB_UNACCEPTED"))

        except Exception as e:
            print(f"[ERRO] Erro ao estabelecer conexão com o banco {e}")
    
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
