from requests import get


def get_brazilian_cities():
    estados = {
        'AC': [], 'AL': [], 'AP': [], 'AM': [], 'BA': [], 'CE': [], 'DF': [],
        'ES': [], 'GO': [], 'MA': [], 'MT': [], 'MS': [], 'MG': [], 'PA': [],
        'PB': [], 'PR': [], 'PE': [], 'PI': [], 'RJ': [], 'RN': [], 'RS': [],
        'RO': [], 'RR': [], 'SC': [], 'SP': [], 'SE': [], 'TO': []
    }
    
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
    
    try:
        print("Buscando dados no IBGE (isso pode levar alguns segundos)...")
        response = get(url)
        
        lista_municipios = response.json()
        
        for municipio in lista_municipios:
            if not municipio or not isinstance(municipio, dict):
                continue
           
            microrregiao = municipio.get('microrregiao') or {}
            mesorregiao = microrregiao.get('mesorregiao') or {}
            uf = mesorregiao.get('UF') or {}
            sigla_estado = uf.get('sigla')
           
            if sigla_estado and sigla_estado in estados:
                nome_cidade = municipio.get('nome')
                if nome_cidade:
                    estados[sigla_estado].append(nome_cidade)

        return estados

    except Exception as e:
        print(f"[ERRO] Falha ao processar e estruturar os dados do dicionário: {e}")