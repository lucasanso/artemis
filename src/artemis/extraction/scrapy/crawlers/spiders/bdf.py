import re
from datetime import datetime

import pytz
import scrapy

from ..items import CrawlerItem
from ..keywords import KEYWORDS
from ..utils import (
    get_processed_kwords,
    save_processed_kword,
    validate_article,
)
from .base_spider import BaseSpider

# Configurações de URL
INIT_URL = 'https://www.brasildefato.com.br/?s={}' 
SEARCH_PAGE_URL = 'https://www.brasildefato.com.br/page/{}/?s={}'

class BdfSpider(BaseSpider):
    """
    Spider especializado para o portal Brasil de Fato.
    
    A extração é baseada em uma lógica de paginação recursiva simples. O spider 
    percorre os resultados de busca e, enquanto encontrar links de artigos válidos, 
    incrementa o contador de páginas na URL.
    """

    name = 'bdf'
    allowed_domains = ['www.brasildefato.com.br']

    def __init__(self):
        """
        Inicializa o spider e recupera o histórico de progresso.

        Notes:
            Utiliza o utilitário 'get_processed_kwords' para carregar os termos 
            que já foram finalizados, permitindo a retomada de crawls interrompidos.
        """
        self.processed_kwords = get_processed_kwords(self.name)

    def start_requests(self):
        palavras = KEYWORDS['AGRESSOR'] + KEYWORDS['ACAO_VIOLENTA'] 
        
        for p in palavras:
            if self.processed_kwords and p in self.processed_kwords:
                self.logger.info(f'Palavra-chave "{p}" já foi processada. Pulando...')
                continue
            
            self.logger.info(f'Iniciando busca para a palavra-chave: {p}')
            
            yield scrapy.Request(
                url=SEARCH_PAGE_URL.format(1, p),
                callback=self.parse,
                meta={'keyword': p, 'page': 1}
            )

    def parse(self, response):
        keyword = response.meta.get('keyword')
        current_page = response.meta.get('page')
        
        # Seleciona os links dos artigos na página de resultados
        links = response.css('h2 a::attr(href)').getall()

        # Verificação de fim de resultados
        # Se não houver links, a palavra-chave terminou ou não tem resultados
        if not links:
            self.logger.info(f'Palavra-chave "{keyword}" totalmente processada na página {current_page}.')
            save_processed_kword(keyword, self.name)
            return

        # Segue para os links dos artigos encontrados
        for link in set(links):
            yield response.follow(
                url=link,
                callback=self.parse_item,
                meta={'keyword': keyword}
            )

        # Paginação recursiva
        # Gera o pedido para a PRÓXIMA página apenas se esta atual teve links
        next_page = current_page + 1
        next_url = SEARCH_PAGE_URL.format(next_page, keyword)
        
        yield scrapy.Request(
            url=next_url,
            callback=self.parse,
            meta={'keyword': keyword, 'page': next_page}
        )

    def parse_item(self, response):
        item = CrawlerItem()
        
        all_paragraphs = response.css('.elementor-element.elementor-element-8136daa.elementor-widget.elementor-widget-theme-post-content .elementor-widget-container p::text, p > a::text, p em::text').getall()

        for p in all_paragraphs:
            if re.findall(r'::', p):
                continue

            full_text = " ".join(all_paragraphs)

        validate = validate_article(full_text)

        if validate:
            item['titulo'] = response.css('h1::text').get()
            item['corpo_texto'] = full_text
            item['palavra_chave'] = response.meta.get('keyword')

            date = response.url[32:42]
            item['data_noticia'] = date
            item['data_coleta'] = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime(r'%d-%m-%Y')
            item['aceito_por'] = validate
            item['portal'] = 'Brasil de Fato'
            item['data_evento'] = None
            item['historico_agressao'] = None
            item['medida_protetiva'] = None
            item['espaco'] = None
            item['municipio'] = None
            item['estado'] = None
            item['causa'] = None
            item['vitima_idade'] = None
            item['agressor_idade'] = None
            item['preso'] = None
            item['auto_exterminio'] = None
            item['profissao_agressor'] = None
            item['vinculo'] = None
            item['classificacao_automatica'] = None
            item['confianca_modelo'] = None
            item['data_classificacao'] = None

        item['url'] = response.url

        yield item