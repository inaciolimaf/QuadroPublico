# Documentação Técnica — QuadroPublico

Este documento explica em detalhes as tecnologias, configurações e conceitos técnicos utilizados no projeto.

---

## Sumário

1. [FastAPI](#fastapi)
2. [SQLAlchemy](#sqlalchemy)
3. [Alembic](#alembic)
4. [Docker](#docker)
5. [Frontend React](#frontend-react)
6. [Hooks do React (useState, useEffect, useContext)](#hooks-do-react)
7. [Arquitetura Geral](#arquitetura-geral)

---

## FastAPI

### O que é

FastAPI é um framework web Python moderno e de alta performance para construção de APIs. Ele é baseado em **type hints** do Python e usa **Pydantic** para validação automática de dados.

### Conceitos principais

#### Rotas (Endpoints)

As rotas são funções Python decoradas que respondem a requisições HTTP:

```python
@router.get("/funcionarios/")
def list_funcionarios(q: str | None = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    ...
```

- `@router.get(...)` define o método HTTP e o caminho
- Os parâmetros da função viram automaticamente query parameters
- O FastAPI gera documentação OpenAPI/Swagger automaticamente

#### Injeção de Dependências

O FastAPI usa `Depends()` para injetar dependências nas rotas. No projeto, a sessão do banco é injetada assim:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Uso na rota:
def list_funcionarios(db: Session = Depends(get_db)):
    ...
```

Isso garante que cada requisição tem sua própria sessão e que ela é fechada ao final.

#### Schemas Pydantic

Pydantic valida e serializa os dados automaticamente:

```python
class FuncionarioOut(BaseModel):
    id: int
    nome: str
    cpf_parcial: str | None
    criado_em: datetime
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)
```

- `from_attributes=True` permite converter objetos SQLAlchemy diretamente para o schema
- O FastAPI usa esses schemas para validar entrada e formatar saída

#### Middleware

O projeto usa dois middlewares:

1. **CORS Middleware** — permite que o frontend (porta 3000) acesse a API (porta 8000):
   ```python
   app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET"], ...)
   ```

2. **Security Headers** — adiciona cabeçalhos de segurança (X-Content-Type-Options, X-Frame-Options, etc.)

#### Lifespan

O `lifespan` é um context manager que roda código na inicialização e encerramento da aplicação:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()  # Inicia sync automático
    yield
    # Cleanup aqui se necessário
```

---

## SQLAlchemy

### O que é

SQLAlchemy é um ORM (Object-Relational Mapper) que permite interagir com o banco de dados usando classes Python em vez de SQL puro.

### Configuração no projeto

O arquivo `database.py` configura a conexão:

```python
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://quadro:quadro@db:5432/quadropublico"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,          # conexões mantidas no pool
    max_overflow=10,      # conexões extras permitidas
    pool_pre_ping=True    # testa conexão antes de usar
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

- **engine** — gerencia a conexão com o PostgreSQL
- **SessionLocal** — fábrica de sessões (cada sessão = uma transação)
- **Base** — classe base que todos os modelos herdam
- **pool_pre_ping** — evita erros com conexões que caíram

### Modelos

Os modelos definem a estrutura das tabelas:

```python
class Funcionario(Base):
    __tablename__ = "funcionarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(300), nullable=False, index=True)
    cpf_parcial = Column(String(20), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cargos = relationship("Cargo", back_populates="funcionario", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("nome", "cpf_parcial"),)
```

Conceitos importantes:
- **relationship** — define a relação entre tabelas (1:N entre Funcionário e Cargo)
- **cascade="all, delete-orphan"** — ao deletar um funcionário, seus cargos são deletados junto
- **UniqueConstraint** — impede duplicatas no banco
- **index=True** — cria índice para buscas mais rápidas no campo `nome`
- **selectinload** — carrega relacionamentos em uma única query extra (usado no repository)

### Padrão Repository

O projeto separa a lógica de acesso ao banco em repositórios:

```python
# repository.py
def search_funcionarios(db: Session, query: str | None, skip: int, limit: int):
    q = db.query(Funcionario)
    if query:
        for term in query.strip().split():
            pattern = f"%{term}%"
            q = q.filter(func.unaccent(Funcionario.nome).ilike(func.unaccent(pattern)))
    return q.order_by(Funcionario.nome).offset(skip).limit(limit).all()
```

A função `unaccent()` é uma extensão do PostgreSQL que remove acentos, permitindo buscar "Jose" e encontrar "José".

---

## Alembic

### O que é

Alembic é a ferramenta de **migrations** (migrações de banco de dados) do SQLAlchemy. Ele versiona o schema do banco, permitindo aplicar e reverter alterações de forma controlada — similar ao que o Git faz para código, mas para a estrutura do banco.

### Por que usar migrations

Sem migrations, mudanças no banco precisariam ser feitas manualmente com SQL. Com Alembic:
- Cada alteração é um arquivo Python versionado
- Você pode subir (`upgrade`) ou reverter (`downgrade`) mudanças
- O time inteiro tem o mesmo schema de banco
- Em produção, o deploy aplica as migrations automaticamente

### Configuração

#### `alembic.ini`

Arquivo principal de configuração:

```ini
[alembic]
script_location = alembic          # pasta com os scripts de migration
sqlalchemy.url = postgresql://quadro:quadro@db:5432/quadropublico
```

#### `alembic/env.py`

Conecta o Alembic aos modelos do SQLAlchemy:

```python
from app.models import Base
target_metadata = Base.metadata
```

Isso permite que o Alembic compare o estado atual do banco com os modelos Python e gere migrations automaticamente.

### Comandos

```bash
# Gerar uma nova migration automaticamente
alembic revision --autogenerate -m "descrição da alteração"

# Aplicar todas as migrations pendentes
alembic upgrade head

# Reverter a última migration
alembic downgrade -1

# Ver o histórico de migrations
alembic history

# Ver a migration atual do banco
alembic current
```

### Como funciona o `--autogenerate`

Quando você roda `alembic revision --autogenerate`, o Alembic:

1. Lê os modelos Python (via `target_metadata`)
2. Conecta ao banco e lê o schema atual
3. Compara os dois e gera um script com as diferenças
4. Cria um arquivo na pasta `alembic/versions/`

Exemplo de migration gerada:

```python
def upgrade():
    op.create_table(
        "funcionarios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(length=300), nullable=False),
        ...
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_funcionarios_nome"), "funcionarios", ["nome"])

def downgrade():
    op.drop_index(op.f("ix_funcionarios_nome"))
    op.drop_table("funcionarios")
```

### Migrations do projeto

O projeto tem três migrations:

1. **`e1a5c7b60371`** — Criação das tabelas `funcionarios`, `cargos` e `contracheques`
2. **`ac412e2c02a4`** — Adiciona extensão `unaccent` no PostgreSQL (para busca sem acentos)
3. **`b3f7a1d20e45`** — Criação da tabela `sync_logs`

### Execução automática

No `entrypoint.sh` do container, as migrations rodam antes do servidor iniciar:

```bash
alembic upgrade head    # Aplica todas as migrations pendentes
uvicorn app.main:app    # Depois inicia o servidor
```

Isso garante que o banco está sempre atualizado ao fazer deploy.

---

## Docker

### O que é

Docker empacota a aplicação e suas dependências em **containers** isolados. Docker Compose orquestra múltiplos containers que precisam trabalhar juntos.

### Arquitetura dos containers

```
┌──────────────────────────────────────────────┐
│              docker-compose.yml              │
├──────────────┬──────────────┬────────────────┤
│     db       │   backend    │   frontend     │
│  PostgreSQL  │   FastAPI    │  React + Nginx │
│  porta 5432  │  porta 8000  │  porta 3000    │
└──────────────┴──────────────┴────────────────┘
```

### docker-compose.yml

Define três serviços:

#### Banco de Dados (db)

```yaml
db:
  image: postgres:16-alpine
  environment:
    POSTGRES_USER: quadro
    POSTGRES_PASSWORD: quadro
    POSTGRES_DB: quadropublico
  volumes:
    - pgdata:/var/lib/postgresql/data   # Dados persistem entre restarts
  healthcheck:
    test: pg_isready -U quadro -d quadropublico
    interval: 5s
    timeout: 3s
    retries: 5
```

- Usa Alpine Linux (imagem menor)
- O **healthcheck** garante que o banco está pronto antes do backend iniciar
- O **volume** persiste os dados mesmo se o container for destruído

#### Backend

```yaml
backend:
  build: ./backend
  ports:
    - "8000:8000"
  volumes:
    - ./backend:/app          # Hot reload: edita no host, reflete no container
  depends_on:
    db:
      condition: service_healthy
  environment:
    - DATABASE_URL=postgresql://quadro:quadro@db:5432/quadropublico
```

- `depends_on` com `condition: service_healthy` espera o banco estar pronto
- O volume monta o código do host no container, permitindo **live reload** com Uvicorn

#### Frontend

```yaml
frontend:
  build: ./frontend
  ports:
    - "3000:3000"
  volumes:
    - ./frontend:/app
    - /app/node_modules       # Preserva node_modules do container
  depends_on:
    - backend
```

- O volume `/app/node_modules` evita conflito entre node_modules do host e do container

### Dockerfile de Produção (raiz)

Build multi-stage que combina frontend e backend em uma única imagem:

```dockerfile
# Stage 1: Build do frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY frontend/package*.json .
RUN npm ci
COPY frontend/ .
RUN npm run build                # Gera /app/dist com HTML/JS/CSS

# Stage 2: Backend + arquivos estáticos
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=frontend-build /app/dist static/   # Copia build do frontend
EXPOSE 8000
CMD ["./entrypoint.sh"]
```

Em produção, o FastAPI serve os arquivos estáticos do React diretamente, eliminando a necessidade de Nginx separado.

### Dockerfile do Frontend (desenvolvimento vs produção)

```dockerfile
# Build
FROM node:20-alpine AS build
RUN npm ci && npm run build

# Produção: Nginx serve os arquivos estáticos
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
```

---

## Frontend React

### O que é React

React é uma biblioteca JavaScript para construir interfaces de usuário. Ele usa **componentes** — blocos reutilizáveis de UI — e um **DOM virtual** para atualizar a tela de forma eficiente.

### Estrutura do frontend

```
src/
├── components/          # Componentes visuais
│   ├── Header.tsx       # Cabeçalho
│   ├── Footer.tsx       # Rodapé
│   ├── FuncionarioList.tsx    # Lista de servidores
│   ├── FuncionarioCard.tsx    # Card expandível de servidor
│   ├── CargoItem.tsx          # Cargo com contracheques
│   ├── SearchBar.tsx          # Barra de busca
│   ├── Pagination.tsx         # Paginação
│   ├── ContrachequeTable.tsx  # Tabela de contracheques
│   ├── ContrachequeChart.tsx  # Gráfico de contracheques
│   └── ui/                    # Componentes base (Shadcn/ui)
├── hooks/               # Lógica reutilizável
│   ├── useFuncionarios.ts
│   ├── useFuncionarioDetail.ts
│   ├── useContracheques.ts
│   └── useDebounce.ts
├── services/            # Comunicação com API
│   ├── api.ts
│   ├── funcionarios.ts
│   └── contracheques.ts
├── types/               # Interfaces TypeScript
└── lib/                 # Utilitários (formatação BRL, etc.)
```

### Fluxo de dados

```
App.tsx
 └── FuncionarioList (usa useFuncionarios hook)
      ├── SearchBar (input controlado)
      ├── FuncionarioCard[] (um por servidor)
      │    ├── CargoItem[] (um por cargo)
      │    │    ├── ContrachequeTable
      │    │    └── ContrachequeChart
      │    └── useFuncionarioDetail (lazy load)
      └── Pagination
```

### Comunicação com a API

```typescript
// services/api.ts
const API_BASE = import.meta.env.DEV ? "/api" : "";

export async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}
```

- Em **desenvolvimento**, o Vite faz proxy de `/api` para `http://backend:8000`
- Em **produção**, o FastAPI serve o frontend, então as chamadas vão direto

### Shadcn/ui

Shadcn/ui é uma coleção de componentes acessíveis baseados em **Radix UI**. Diferente de bibliotecas tradicionais, você copia os componentes para seu projeto e os customiza:

- `button.tsx` — botões com variantes (default, ghost)
- `card.tsx` — cards com header, content, footer
- `badge.tsx` — badges coloridos (success, destructive)
- `table.tsx` — tabela estilizada
- `tabs.tsx` — abas (usado para alternar tabela/gráfico)
- `skeleton.tsx` — placeholder de carregamento

---

## Hooks do React

### O que são Hooks

Hooks são funções que permitem usar estado e outros recursos do React em componentes funcionais. Os principais são:

### useState

Cria uma variável de estado que, ao ser alterada, re-renderiza o componente:

```typescript
const [query, setQuery] = useState("");        // string vazia inicial
const [page, setPage] = useState(1);           // número 1 inicial
const [loading, setLoading] = useState(false);  // booleano false inicial
```

- `query` é o valor atual
- `setQuery` é a função para atualizar o valor
- Quando `setQuery("novo valor")` é chamado, o componente re-renderiza com o novo valor

No projeto, `useState` é usado para:
- Termo de busca (`query`)
- Página atual (`page`)
- Estado de carregamento (`loading`)
- Dados recebidos da API (`funcionarios`, `detail`, `contracheques`)
- Estado de expansão dos cards (`expanded`)
- Aba ativa no CargoItem (`activeTab`)

### useEffect

Executa efeitos colaterais (chamadas de API, timers, etc.) em resposta a mudanças:

```typescript
useEffect(() => {
  // Isso roda quando debouncedQuery ou page mudam
  setLoading(true);
  listFuncionarios({ q: debouncedQuery, skip: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE })
    .then(data => {
      setFuncionarios(data.items);
      setTotal(data.total);
    })
    .finally(() => setLoading(false));
}, [debouncedQuery, page]);  // Array de dependências
```

- O array `[debouncedQuery, page]` diz ao React para re-executar quando essas variáveis mudarem
- Sem o array, rodaria em todo render. Com array vazio `[]`, roda só na montagem

### useCallback

Memoriza uma função para evitar recriações desnecessárias:

```typescript
const handleSearch = useCallback((value: string) => {
  setQuery(value);
  setPage(1);
}, []);
```

Útil quando a função é passada como prop para componentes filhos — evita re-renders desnecessários.

### useRef

Cria uma referência mutável que persiste entre renders sem causar re-render:

```typescript
const fetched = useRef(false);

useEffect(() => {
  if (!enabled || fetched.current) return;
  fetched.current = true;
  // fetch data...
}, [enabled]);
```

No projeto, `useRef` é usado para evitar que dados sejam buscados mais de uma vez (quando o card já foi expandido).

### useContext

Compartilha dados entre componentes sem passar props manualmente por toda a árvore. No projeto atual, o estado é simples o suficiente para usar apenas `useState` + props, mas `useContext` seria usado assim:

```typescript
// Criar o contexto
const ThemeContext = createContext("light");

// Prover o valor no topo
<ThemeContext.Provider value="dark">
  <App />
</ThemeContext.Provider>

// Consumir em qualquer componente filho
function Button() {
  const theme = useContext(ThemeContext);  // "dark"
}
```

`useContext` resolve o problema de **prop drilling** — quando você precisa passar dados por muitos níveis de componentes.

### Custom Hooks

O projeto encapsula lógica complexa em hooks customizados:

#### useFuncionarios

```typescript
export function useFuncionarios() {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [funcionarios, setFuncionarios] = useState<Funcionario[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const debouncedQuery = useDebounce(query, 400);

  useEffect(() => {
    // Busca servidores quando query ou página mudam
  }, [debouncedQuery, page]);

  return { funcionarios, total, loading, query, setQuery, page, setPage, totalPages };
}
```

#### useDebounce

```typescript
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);   // Limpa timer anterior
  }, [value, delay]);

  return debouncedValue;
}
```

Espera 400ms após o usuário parar de digitar antes de fazer a busca — evita chamadas excessivas à API.

---

## Arquitetura Geral

### Fluxo completo de uma requisição

```
1. Usuário digita "Maria" na SearchBar
2. useDebounce espera 400ms
3. useFuncionarios dispara useEffect
4. fetchJson("/funcionarios/?q=Maria&skip=0&limit=20")
5. Vite proxy encaminha para backend:8000
6. FastAPI recebe, injeta sessão do banco via Depends(get_db)
7. Repository usa unaccent() + ilike() no PostgreSQL
8. Pydantic serializa o resultado
9. JSON retorna para o frontend
10. useState atualiza, React re-renderiza a lista
```

### Fluxo de sincronização de dados

```
1. App inicia → lifespan chama start_scheduler()
2. Thread daemon verifica último sync_log
3. Se > 24h, chama sync_all()
4. Descobre anos/meses disponíveis no site fonte
5. Classifica períodos (novos + recentes para refresh)
6. ThreadPoolExecutor (4 workers) busca/parseia páginas
7. Queue com buffer de 2 itens
8. Consumer consome fila, faz upsert em lotes de 50
9. Grava sync_log com resultado
```

### Testes

**Backend (Pytest):**
```bash
cd backend
pip install -r requirements-dev.txt
pytest -v
```

**Frontend (Vitest):**
```bash
cd frontend
npm test
```

Os testes do backend usam `httpx.AsyncClient` como test client do FastAPI. Os testes do frontend usam `@testing-library/react` para renderizar componentes e simular interações.
