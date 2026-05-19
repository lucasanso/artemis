import scrapy


class CrawlerItem(scrapy.Item):
    palavra_chave = scrapy.Field()
    data_coleta = scrapy.Field()
    data_noticia = scrapy.Field()
    portal = scrapy.Field()
    url = scrapy.Field()
    titulo = scrapy.Field()
    corpo_texto = scrapy.Field()
    aceito_por = scrapy.Field()
    
    # Par de palavras-chave: Agressor - Ação Violenta
    data_evento = scrapy.Field()
    historico_agressao = scrapy.Field()
    medida_protetiva = scrapy.Field()
    espaco = scrapy.Field()
    municipio = scrapy.Field()
    estado = scrapy.Field()
    causa = scrapy.Field()
    vitima_idade = scrapy.Field()
    agressor_idade = scrapy.Field()
    preso = scrapy.Field()
    auto_exterminio = scrapy.Field()
    profissao_agressor = scrapy.Field()
    vinculo = scrapy.Field()
    classificacao_automatica = scrapy.Field()
    confianca_modelo = scrapy.Field()
    data_classificacao = scrapy.Field()
