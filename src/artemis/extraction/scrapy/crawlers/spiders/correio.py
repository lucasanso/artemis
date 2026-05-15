import re
from datetime import datetime

import pytz
import scrapy
from scrapy import signals

from ..items import CrawlerItem
from ..keywords import KEYWORDS
from ..utils import (
    get_processed_kwords,
    save_processed_kword,
    search_gangs,
    validate_article,
)
from .base_spider import BaseSpider


class SpiderCorreioDoPovo(BaseSpider):
    name = 'correio'
    allowed_domains = ['correiodopovo.com.br']

    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True, "timeout": 20000},
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": True,
        "DEFAULT_REQUEST_HEADERS": {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Referer': 'https://www.google.com/'
        },
    }

    search_url_template = 'https://www.correiodopovo.com.br/busca?q={keyword}&page={page_number}&sort=date'
    next_page_selector = '//li/a[@title="Next page"]' 
    article_title_selector = '//h1[contains(@class, "article__headline")]/text() | //h1/text()'
    article_date_selector = '//time/@datetime'
    article_content_selector = '//div[contains(@class, "article__body")]/p//text() | //div[contains(@class, "content-text")]/p//text()'
    payed_articles_selector = '//div[contains(@class, "conteudo_pago")]'
    
    news_pattern = re.compile(r'-\d+\.\d+$')

    def start_requests(self):
        """
        Inicia a corrente: pega todas as palavras, remove as processadas e 
        dispara APENAS a primeira, passando o restante na 'mochila' (meta).
        """
        if hasattr(self, 'user_keyword') and self.user_keyword:
            all_terms = [self.user_keyword]
        else:
            all_terms = KEYWORDS.get('GANGS', []) + KEYWORDS.get('ORGANIZED CRIME', [])
        
        processed_terms = get_processed_kwords(self.name)
        search_terms = [k for k in all_terms if k not in processed_terms]
        
        self.logger.info(f'[FILTRO] Total: {len(all_terms)} | Processadas: {len(processed_terms)} | Restantes: {len(search_terms)}')

        if not search_terms:
            self.logger.info("Nenhuma palavra-chave pendente.")
            return

        # Tira a primeira palavra da lista para começar
        first_keyword = search_terms.pop(0)
        
        url = self.search_url_template.format(keyword=first_keyword.replace(' ', '+'), page_number=1)
        yield scrapy.Request(
            url=url, 
            callback=self.parse,
            meta={
                'playwright': True, 
                'playwright_include_page': True,
                'keyword': first_keyword,
                'page_number': 1,
                'remaining_keywords': search_terms, # PASSA O RESTANTE AQUI
                'previous_links': []
            },
            errback=self.errback_close_page,
            dont_filter=True
        )

    def _trigger_next_keyword(self, remaining_keywords):
        """
        Função auxiliar para puxar a próxima palavra da lista e iniciar a busca.
        """
        if not remaining_keywords:
            self.logger.info("[FIM] Todas as palavras-chave foram processadas!")
            return None

        next_keyword = remaining_keywords.pop(0)
        self.logger.info(f'[INÍCIO] Iniciando próxima palavra-chave: {next_keyword}')
        
        url = self.search_url_template.format(keyword=next_keyword.replace(' ', '+'), page_number=1)
        return scrapy.Request(
            url=url, 
            callback=self.parse,
            meta={
                'playwright': True, 
                'playwright_include_page': True,
                'keyword': next_keyword,
                'page_number': 1,
                'remaining_keywords': remaining_keywords, # Continua passando a lista
                'previous_links': []
            },
            errback=self.errback_close_page,
            dont_filter=True
        )

    async def parse(self, response):
        page = response.meta.get("playwright_page")
        keyword = response.meta.get("keyword")
        curr_page = response.meta.get("page_number")
        remaining_keywords = response.meta.get("remaining_keywords")
        previous_links = response.meta.get("previous_links")

        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

            hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => a.href)")
            article_links = list(set([l for l in hrefs if l and self.news_pattern.search(l)]))

            # --- CONDIÇÃO DE PARADA: LOOP OU SEM LINKS ---
            if not article_links or set(article_links) == set(previous_links):
                self.logger.info(f'[CONCLUÍDO] Loop ou fim de resultados na pág {curr_page}. Finalizando {keyword}.')
                save_processed_kword(keyword, self.name)
                
                # ACABOU A PALAVRA ATUAL. CHAMA A PRÓXIMA!
                next_req = self._trigger_next_keyword(remaining_keywords)
                if next_req: yield next_req
                return

            # Extração das notícias encontradas (processadas em background pelo Scrapy)
            for link in article_links:
                yield scrapy.Request(
                    url=link, 
                    callback=self.parse_item, 
                    meta={'keyword': keyword},
                    errback=self.handle_failure, 
                    dont_filter=True
                )

            # --- PAGINAÇÃO DA PALAVRA ATUAL ---
            sel = scrapy.Selector(text=await page.content())
            next_page_href = sel.xpath(f'{self.next_page_selector}/@href').get()

            if next_page_href:
                next_url = response.urljoin(next_page_href)
                next_page_num = curr_page + 1
                
                self.logger.info(f'[PAGINAÇÃO] {keyword} | Indo para página {next_page_num}')
                
                yield scrapy.Request(
                    url=next_url, 
                    callback=self.parse,
                    meta={
                        'playwright': True, 
                        'playwright_include_page': True,
                        'keyword': keyword,
                        'page_number': next_page_num,
                        'remaining_keywords': remaining_keywords, # Mantém a mochila!
                        'previous_links': article_links 
                    },
                    errback=self.errback_close_page,
                    dont_filter=True
                )
            else:
                self.logger.info(f'[CONCLUÍDO] Sem botão de próxima página. Finalizando: {keyword}')
                save_processed_kword(keyword, self.name)
                
                # ACABOU A PALAVRA ATUAL. CHAMA A PRÓXIMA!
                next_req = self._trigger_next_keyword(remaining_keywords)
                if next_req: yield next_req

        finally:
            if page: 
                await page.close()

    def parse_item(self, response):
        keyword = response.meta.get("keyword")
        
        if not response.xpath(self.payed_articles_selector).get():
            item = CrawlerItem()
            body = ' '.join(response.xpath(self.article_content_selector).getall()).strip()
            validate = validate_article(body)
            
            item['keyword'] = keyword
            item['url'] = response.url
            
            if validate:
                item['title'] = (response.xpath(self.article_title_selector).get() or "").strip()
                item['acquisition_date'] = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d-%m-%Y')
                item['newspaper'] = 'Correio do Povo'
                item['article'] = body
                item['accepted_by'] = validate
                item['gangs'] = search_gangs(body)
                
                dt = response.xpath(self.article_date_selector).get()
                item['publication_date'] = dt.split('T')[0] if dt and 'T' in dt else dt
                yield item
            else:
                yield item

    def handle_failure(self, failure):
        self.logger.error(f"Erro na requisição da notícia: {failure.request.url}")

    async def errback_close_page(self, failure):
        page = failure.request.meta.get("playwright_page")
        remaining_keywords = failure.request.meta.get("remaining_keywords", [])
        
        if page: 
            await page.close()
        self.logger.error(f"Erro de Playwright na busca: {failure.request.url}")
        
        # Se a busca de uma palavra der erro fatal, pula para a próxima para não travar o bot
        next_req = self._trigger_next_keyword(remaining_keywords)
        if next_req: yield next_req

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SpiderCorreioDoPovo, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        self.logger.info("Spider encerrada.")