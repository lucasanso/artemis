import json

import scrapy
import yaml
from confluent_kafka import Producer

from .exceptions import YamlNotFoundError
from .items import CrawlerItem

try:
    with open('config.yaml', 'r') as configs_file:
        configs = yaml.safe_load(configs_file)
        print("[SUCESSO] Arquivo .yaml de configurações foi lido com sucesso")

except FileNotFoundError:
    raise YamlNotFoundError

class CrawlersPipeline:
    """
    Classe responsável pelas conexões SSH e cliente do MongoDB para realizar inserção de notícias, envio de email e logs automatizados.
    """
    def __init__(self) -> None:
        self.kafka_producer_config = {
            'bootstrap.servers' : 'broker:29092',
            'client.id' : 'scrapy'
        }

    def open_spider(self, spider: scrapy.Spider) -> None:
        print(f'[PROCESSO] Iniciando bot de extração: {spider.name}')
        self.producer = Producer(**self.kafka_producer_config)

        try:
            self.producer = Producer(**self.kafka_producer_config)

        except Exception as e:
            spider.logger.error(f"[ERRO] Erro crítico ao conectar com o broker do Kafka: {e}")
            
    def close_spider(self, spider: scrapy.Spider) -> None:
        """
        Método que é chamado automaticamente pelo scrapy no momento em que encerra-se a extração.
        
        Args:
            spider(scrapy.Spider): Bot em execução.

        Note:
            Uma extração pode ser finalizada ou interrompida.

            Finalizada: Todas as palavras-chave foram processadas.

            Interrompida: O responsável pela execução do código pressionou CTRL + C. 
        """
        print("[AVISO] Encerrando extração.")

        self.generate_log(spider.name)

        if self.client:
            self.client.close()
        if self.server:
            self.server.stop()

    def process_item(self, item: CrawlerItem, spider: scrapy.Spider) -> None:
        """
        Orquestra o fluxo de persistência de um item extraído.

        Realiza a deduplicação via URL, diferencia notícias aceitas/não aceitas 
        com base nas palavras-chave e incrementa os contadores da sessão.

        Args:
            item (CrawlerItem): Objeto contendo os dados estruturados da notícia.
            spider (scrapy.Spider): Bot em execução.
            test_output (bool): Se True, ativa logs extras ou exportação local (Default: False).

        Note:
            A deduplicação é feita consultando o conjunto 'self.all' carregado no início da execução.
        """
        self.data = dict(CrawlerItem(item))

        url = self.data.get("url")

        if not url:
            print("[AVISO] A notícia possui formatação totalmente diferente (URL nula).")
            return
        
        try:
            topic = "raw_news"
            key = str(self.data.get("id_event", "0"))
            payload = json.dumps(self.data, ensure_ascii=False, default=str).encode('utf-8')

            if self.data.get("accepted_by"):
                spider.logger.info(f"[SUCESSO] Enviando URL {url} aceita para o Kafka")
            else:
                spider.logger.info(f"[AVISO] Enviando URL {url} não aceita para o Kafka")

            self.producer.produce(
                topic=topic,
                key=key,
                value=payload,
                callback=self.sent_product
            )
            self.producer.flush()

        except Exception as e:
            spider.logger.error(f"[ERRO] Falha ao processar item {url}: {e}")
    
    def sent_product(self, err, msg):
        if err is not None:
            print("[ERRO] Não foi possível enviar a URL.")

        else:
            print(f"[SUCESSO] Conteúdo [{msg.topic()}] enviado para fila na partição [{msg.partition()}]")