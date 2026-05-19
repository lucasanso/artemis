import json
import ollama
import pymongo
from dotenv import load_dotenv
import os
from time import sleep
from datetime import datetime
import pytz

load_dotenv(dotenv_path="../.env.dev")

class OllamaData:
    def __init__(self):
        self.MODEL_NAME = "qwen2.5:7b-instruct-q4_K_M"
        print(f"[PROCESSO] Iniciando enriquecimento de dados com o modelo {self.MODEL_NAME} do Ollama")

    def establishing_conns(self):
        try:    
            self.client = pymongo.MongoClient(os.getenv("MONGO_DB_URI"))
            db = self.client.get_database(os.getenv("MONGO_DB_DATABASE"))
            self.accepted_news_collection = db.get_collection(os.getenv("MONGO_DB_ACCEPTED"))
            self.unaccepted_news_collection = db.get_collection(os.getenv("MONGO_DB_UNACCEPTED"))
        except Exception as e:
            print(f"[ERRO] Erro ao estabelecer conexão com o banco {e}")

    def data_processing(self):
        query = {
            "classificacao_automatica": None
        }

        prompt_sistema = """
            Você é um extrator de dados estruturados especialista em segurança pública e casos de feminicídio/violência contra a mulher.
            Analise a notícia fornecida e retorne ESTRITAMENTE um objeto JSON válido. 

            REGRAS VITAIS:
            1. Se a notícia NÃO for sobre feminicídio/violência doméstica (classificacao_automatica = 0), preencha todos os outros campos com null.
            2. NUNCA invente novas chaves E novos valores. Use APENAS as chaves listadas abaixo.
            3. Não adicione textos antes ou depois do JSON.

            FORMATO EXATO DE SAÍDA OBRIGATÓRIO (Copie esta estrutura):
            {
                "classificacao_automatica": 0 ou 1,
                "data_evento": "AAAA-MM-DD" ou null,
                "municipio": "Nome da Cidade" ou "Não mencionado",
                "estado": "Sigla" ou "Não Mencionado",
                "vitima_idade": inteiro ou 0 (se não mencionado),
                "agressor_idade": inteiro ou 0 (se não mencionado),
                "historico_agressao": true ou false,
                "medida_protetiva": true ou false,
                "preso": true ou false,
                "auto_exterminio": true, false ou null,
                "espaco": inteiro ou 0,
                "causa": inteiro ou 0,
                "profissao_agressor": inteiro ou 0,
                "vinculo": inteiro ou 0
            }
        """
        
        cursor = self.accepted_news_collection.find(query)

        for doc in cursor:
            print(f"Título: {doc.get('titulo', 'Sem título')}. Iniciando processamento...")
            sleep(1) 

            noticia = doc.get('corpo_texto', '')
            if not noticia:
                print("[AVISO] Notícia vazia, pulando...")
                continue
            
            if doc['classificacao_automatica']:
                continue
            
            try:
                resposta = ollama.chat(
                    model=self.MODEL_NAME,
                    messages=[
                        {"role": "system", "content": prompt_sistema},
                        {"role": "user", "content": f"Extraia os dados desta notícia:\n\n{noticia}"}
                    ],
                    options={
                        "temperature": 0.0,
                        "num_ctx": 4096 
                    },
                    format="json"
                )

                conteudo = resposta['message']['content']
                dados_enriquecidos = json.loads(conteudo)

                dados_enriquecidos['data_evento'] = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime(r'%d-%m-%Y')
                print(dados_enriquecidos)
                print("-" * 50)
                
                self.accepted_news_collection.update_one({"_id": doc["_id"]}, {"$set": dados_enriquecidos})

                print("Notícia atualizada")

            except json.JSONDecodeError as e:
                print(f"[ERRO DE JSON] O modelo gerou um JSON inválido para a notícia {doc['_id']}. Erro: {e}")
                print(f"Saída gerada: {conteudo}")

            except Exception as e:
                print(f"[ERRO GERAL] Falha na notícia {doc['_id']}: {e}")

if __name__ == "__main__":
    teste = OllamaData()
    teste.establishing_conns()
    teste.data_processing()