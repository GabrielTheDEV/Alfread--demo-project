# Alfread-demo-project

> *"Always at your service, sir."*

Um assistente de IA inspirado no mordomo Alfred Pennyworth (universo Batman), dividido em duas partes que trabalham em conjunto:

| Componente | O que é |
|-----------|-----------|
| **MCP Server** (`uv run alfred`) | Um servidor [FastMCP](https://github.com/jlowin/fastmcp) que expõe ferramentas (notícias, busca na web, informações do sistema, …) via SSE. Pense nele como a "Mansão Wayne" nos bastidores — é quem faz o trabalho de fato. |
| **Voice Agent** (`uv run alfred_voice`) | Um pipeline de voz [LiveKit Agents](https://github.com/livekit/agents) que escuta o microfone, raciocina com um LLM (Gemini 2.5 Flash por padrão) e responde por voz com OpenAI TTS — buscando ferramentas do MCP server em tempo real. |

---

## Como funciona

```
Microfone ──► STT (Sarvam Saaras v3)
                    │
                    ▼
             LLM (Gemini 2.5 Flash)  ◄──────► MCP Server (FastMCP / SSE)
                    │                              ├─ get_world_news
                    ▼                              ├─ open_world_monitor
             TTS (OpenAI onyx)                     ├─ search_web
                    │                              └─ …mais ferramentas
                    ▼
             Alto-falante / sala LiveKit
```

O voice agent se conecta ao MCP server via SSE em `http://127.0.0.1:8000/sse` (resolvido automaticamente para o IP do host Windows quando rodando dentro do WSL).

---

## Estrutura do projeto

```
alfread-demo-project/
├── server.py            # uv run alfred  → inicia o MCP server (SSE na :8000)
├── agent_alfred.py       # uv run alfred_voice → inicia o voice agent LiveKit
├── pyproject.toml
├── .env.example          # copie → .env e preencha suas chaves
│
└── alfred/               # pacote do MCP server
    ├── config.py         # carregamento de variáveis de ambiente e configs
    ├── tools/             # ferramentas MCP (chamáveis pelo LLM)
    │   ├── web.py         # search_web, fetch_url, get_world_news, open_world_monitor
    │   ├── system.py      # get_current_time, get_system_info
    │   └── utils.py       # format_json, word_count
    ├── prompts/            # templates de prompt MCP (summarize, explain_code, …)
    └── resources/          # recursos MCP expostos aos clientes (alfred://info)
```

---

## Início rápido

### 1. Pré-requisitos

- Python ≥ 3.11
- [`uv`](https://github.com/astral-sh/uv) — `pip install uv` ou `curl -Lsf https://astral.sh/uv/install.sh | sh`
- Um projeto [LiveKit Cloud](https://cloud.livekit.io) (o plano gratuito funciona)

### 2. Clonar e instalar

```bash
git clone https://github.com/SAGAR-TAMANG/alfread-demo-project.git
cd alfread-demo-project
uv sync          # cria o .venv e instala todas as dependências
```

### 3. Configurar o ambiente

```bash
cp .env.example .env
# Abra o .env e preencha suas chaves de API (veja a seção abaixo)
```

### 4. Executar — dois terminais

**Terminal 1 — MCP server** (precisa iniciar primeiro)

```bash
uv run alfred
```

Inicia o servidor FastMCP em `http://127.0.0.1:8000/sse`. O voice agent se conecta aqui para buscar suas ferramentas.

**Terminal 2 — Voice agent**

```bash
uv run alfred_voice
```

Inicia o voice agent LiveKit em **modo dev** — ele entra numa sala LiveKit e começa a escutar. Abra o [LiveKit Agents Playground](https://agents-playground.livekit.io) e conecte-se à sua sala para conversar com o Alfred.

---

## `uv run alfred` vs `uv run alfred_voice`

| Comando | Entry point | O que faz |
|---------|------------|--------------|
| `uv run alfred` | `server.py → main()` | Inicia o **servidor FastMCP** via transporte SSE na porta 8000. É o "backend" — registra todas as ferramentas, prompts e recursos que o LLM pode chamar. |
| `uv run alfred_voice` | `agent_alfred.py → dev()` | Inicia o **voice agent LiveKit**. Monta o pipeline STT / LLM / TTS, conecta-se à sua sala LiveKit e liga o MCP server como fonte de ferramentas. O wrapper `dev()` injeta automaticamente a flag `dev` da CLI para você não precisar digitá-la manualmente. |

> Os dois processos precisam rodar **simultaneamente**. O voice agent chama o MCP server em tempo real sempre que precisa de uma ferramenta (ex: buscar notícias).

---

## Variáveis de ambiente

Copie `.env.example` → `.env` e preencha os valores abaixo.

| Variável | Obrigatória | Onde conseguir |
|----------|----------|----------------|
| `LIVEKIT_URL` | ✅ | [LiveKit Cloud dashboard](https://cloud.livekit.io) → URL do seu projeto |
| `LIVEKIT_API_KEY` | ✅ | LiveKit Cloud → API Keys |
| `LIVEKIT_API_SECRET` | ✅ | LiveKit Cloud → API Keys |
| `GROQ_API_KEY` | opcional | [console.groq.com](https://console.groq.com) — só necessário se trocar `LLM_PROVIDER` para `"groq"` |
| `SARVAM_API_KEY` | ✅ (STT padrão) | [dashboard.sarvam.ai](https://dashboard.sarvam.ai) |
| `OPENAI_API_KEY` | ✅ (TTS padrão) | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `DEEPGRAM_API_KEY` | opcional | [console.deepgram.com](https://console.deepgram.com) |
| `GOOGLE_APPLICATION_CREDENTIALS` | opcional | caminho do JSON de service-account do GCP — apenas para `STT_PROVIDER = "google"` |
| `GOOGLE_API_KEY` | ✅ (LLM padrão) | [aistudio.google.com](https://aistudio.google.com/projects) |
| `SUPABASE_URL` | opcional | [supabase.com](https://supabase.com) — para a ferramenta de ticketing |
| `SUPABASE_API_KEY` | opcional | Supabase project → API settings |

---

## Trocando de provedor

Abra `agent_alfred.py` e altere as constantes de provedor no topo do arquivo:

```python
STT_PROVIDER = "sarvam"   # "sarvam" | "whisper"
LLM_PROVIDER = "gemini"   # "gemini" | "openai"
TTS_PROVIDER = "openai"   # "openai" | "sarvam"
```

---

## Adicionando uma nova ferramenta

1. Crie ou abra um arquivo em `alfred/tools/`
2. Defina uma função `register(mcp)` e decore as ferramentas com `@mcp.tool()`
3. Importe e chame `register(mcp)` dentro de `alfred/tools/__init__.py`

O MCP server vai carregá-la automaticamente na próxima inicialização.

---

## Stack técnica

- **[FastMCP](https://github.com/jlowin/fastmcp)** — framework de servidor MCP
- **[LiveKit Agents](https://github.com/livekit/agents)** — pipeline de voz em tempo real
- **Sarvam Saaras v3** — STT (otimizado para inglês indiano)
- **Google Gemini 2.5 Flash** — LLM
- **OpenAI TTS** (voz `onyx`) — TTS
- **[uv](https://github.com/astral-sh/uv)** — gerenciador de pacotes Python rápido

---

## Licença

MIT