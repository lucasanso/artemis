"""
Classe que contém exceções personalizadas para tratar erros que podem ocorrer durante o pipeline do Scrapy.
"""

class CrawlerException(Exception):
    pass

class YamlNotFoundError(CrawlerException):
    def __init__(self):
        super().__init__("Arquivo.yaml não foi encontrado")