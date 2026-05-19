
CREATE TABLE IF NOT EXISTS regioes (
    id SERIAL PRIMARY KEY,
    nome_regiao VARCHAR(20) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS estados (
    id SERIAL PRIMARY KEY,
    nome_estado VARCHAR(50) UNIQUE NOT NULL,
    sigla VARCHAR(2) UNIQUE NOT NULL,
    id_regiao INTEGER REFERENCES regioes (id)
);

CREATE TABLE IF NOT EXISTS municipios (
    id SERIAL PRIMARY KEY,
    nome_municipio VARCHAR(100) NOT NULL,
    id_estado INTEGER REFERENCES estados (id),
    CONSTRAINT unique_municipio_por_estado UNIQUE (nome_municipio, id_estado)
);

CREATE TABLE IF NOT EXISTS classificacoes_espacos(
    id SERIAL PRIMARY KEY,
    nome_classificacao VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS vinculos (
    id SERIAL PRIMARY KEY,
    nome_vinculo VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS portais_de_noticia (
    id SERIAL PRIMARY KEY,
    nome_portal VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS profissoes_agressores (
    id SERIAL PRIMARY KEY,
    nome_profissao VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS causas (
    id SERIAL PRIMARY KEY,
    nome_causa VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS artigos (
    id SERIAL PRIMARY KEY,
    id_mongo UUID UNIQUE NOT NULL,
    id_portal INTEGER REFERENCES portais_de_noticia (id),
    titulo VARCHAR(500) NOT NULL,
    data_publicacao DATE NOT NULL,
    data_evento DATE,
    id_municipio INTEGER REFERENCES municipios (id),
    id_espaco INTEGER REFERENCES classificacoes_espacos (id),
    id_causa INTEGER REFERENCES causas (id),
    idade_vitima INTEGER,
    idade_agressor INTEGER,
    id_vinculo INTEGER REFERENCES vinculos (id),
    id_profissao INTEGER REFERENCES profissoes_agressores (id),
    historico_agressao BOOLEAN,
    medida_protetiva BOOLEAN,
    auto_exterminio BOOLEAN,
    preso BOOLEAN,
);

INSERT INTO regioes (nome_regiao) VALUES 
('Norte'),
('Nordeste'),
('Centro-Oeste'),
('Sudeste'),
('Sul')
ON CONFLICT (nome_regiao) DO NOTHING;

INSERT INTO estados (sigla, nome_estado, id_regiao) VALUES ('AC', 'Acre', 1), ('AL', 'Alagoas', 2), ('AP', 'Amapá', 1),
('AM', 'Amazonas', 1), ('BA', 'Bahia', 2), ('CE', 'Ceará', 2), ('DF', 'Distrito Federal', 3), ('ES', 'Espírito Santo', 4),
('GO', 'Goiás', 3), ('MA', 'Maranhão', 2), ('MT', 'Mato Grosso', 3), ('MS', 'Mato Grosso do Sul', 3),
('MG', 'Minas Gerais', 4), ('PA', 'Pará', 1), ('PB', 'Paraíba', 2), ('PR', 'Paraná', 5), ('PE', 'Pernambuco', 2),
('PI', 'Piauí', 2), ('RJ', 'Rio de Janeiro', 4), ('RN', 'Rio Grande do Norte', 2), ('RS', 'Rio Grande do Sul', 5),
('RO', 'Rondônia', 1), ('RR', 'Roraima', 1), ('SC', 'Santa Catarina', 5), ('SP', 'São Paulo', 4), ('SE', 'Sergipe', 2),
('TO', 'Tocantins', 1)
ON CONFLICT (sigla) DO NOTHING;

INSERT INTO portais_de_noticia (nome_portal) VALUES 
('Folha de São Paulo'),
('G1'),
('Brasil de Fato'),
('Estadão'),
('Diário da Manhã'),
('Le Monde Brasil Diplomatique'),
('Correio do Povo'),
('Carta Capital')
ON CONFLICT (nome_portal) DO NOTHING;
