# QuadroPublico

Portal de transparência para consulta de dados de servidores municipais. Coleta automaticamente informações de contracheques e cargos do portal de transparência do governo e apresenta em uma interface web moderna e acessível.

## Funcionalidades

- Busca e listagem de servidores municipais com paginação
- Visualização de cargos e histórico de contracheques
- Gráficos e tabelas de remuneração
- Sincronização automática de dados a cada 24h
- Busca com suporte a acentos (buscar "Jose" encontra "José")
- Interface responsiva e acessível

## Tecnologias

| Camada   | Stack                                                    |
| -------- | -------------------------------------------------------- |
| Backend  | FastAPI, SQLAlchemy, Alembic, PostgreSQL 16               |
| Frontend | React 19, TypeScript, Tailwind CSS, Shadcn/ui, Recharts |
| Infra    | Docker, Docker Compose, Nginx                            |
| Testes   | Pytest (backend), Vitest + Testing Library (frontend)    |

## Estrutura do Projeto

```
QuadroPublico/
├── backend/
│   ├── app/
│   │   ├── main.py              # App FastAPI, middlewares, rotas
│   │   ├── database.py          # Configuração SQLAlchemy
│   │   ├── models.py            # Modelos ORM
│   │   ├── funcionarios/        # Módulo de servidores
│   │   ├── cargos/              # Módulo de cargos
│   │   ├── contracheques/       # Módulo de contracheques
│   │   └── scraping/            # Web scraping e sincronização
│   ├── alembic/                 # Migrations do banco
│   ├── tests/                   # Testes do backend
│   ├── requirements.txt         # Dependências de produção
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # Componentes React
│   │   ├── hooks/               # Custom hooks
│   │   ├── services/            # Camada de API
│   │   ├── types/               # Tipos TypeScript
│   │   └── lib/                 # Utilitários
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── Makefile
└── Dockerfile                   # Build de produção (multi-stage)
```

## Como Rodar

### Pré-requisitos

- Docker e Docker Compose instalados

### Desenvolvimento

```bash
# Subir todos os serviços (PostgreSQL + Backend + Frontend)
make dev

# Parar os serviços
make down

# Rebuild das imagens
make build
```

Após `make dev`, acesse:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Health check:** http://localhost:8000/health

### Testes

```bash
make test
```

Isso executa:
- `pytest -v` no backend
- `npm test` no frontend

## API

| Método | Endpoint                                     | Descrição                          |
| ------ | -------------------------------------------- | ---------------------------------- |
| GET    | `/funcionarios/?q=nome&skip=0&limit=50`      | Lista servidores com busca         |
| GET    | `/funcionarios/{id}`                          | Detalhe do servidor com cargos     |
| GET    | `/funcionarios/{id}/cargos/`                  | Lista cargos do servidor           |
| GET    | `/funcionarios/{id}/cargos/{cargo_id}`        | Detalhe do cargo com contracheques |
| GET    | `/cargos/{cargo_id}/contracheques/`           | Lista contracheques do cargo       |
| GET    | `/cargos/{cargo_id}/contracheques/{id}`       | Detalhe de um contracheque         |
| GET    | `/health`                                     | Status da aplicação e banco        |

## Banco de Dados

Quatro tabelas principais:

- **funcionarios** — nome, CPF parcial, timestamps
- **cargos** — matrícula, órgão, setor, cargo, vínculo, carga horária
- **contracheques** — provento, desconto, líquido, mês/ano de referência
- **sync_logs** — histórico de sincronizações

## Sincronização de Dados

O sistema coleta dados automaticamente do portal [Governo Transparente](https://folha.governotransparente.com.br). A sincronização:

- Roda automaticamente a cada 24h via thread daemon
- Descobre períodos disponíveis (anos e meses)
- Busca páginas em paralelo (4 workers em produção)
- Insere/atualiza registros em lotes de 50 usando upsert do PostgreSQL

## Licença

Dados públicos conforme Lei de Acesso à Informação (Lei 12.527/2011).
