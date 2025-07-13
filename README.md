# SUNA Local WSL2 Setup

Uma implementação completamente local do framework de agente de IA SUNA, adaptada especificamente para rodar no WSL2 do Windows. Este sistema substitui todas as dependências de nuvem por alternativas locais, utilizando o modelo Mistral 7B via llama.cpp e banco de dados SQLite.

## 🎯 Características Principais

- **Operação 100% offline** - sem dependências de APIs externas
- **Otimizado para WSL2** - configuração específica para Windows Subsystem for Linux 2
- **Modelo Mistral 7B local** via llama.cpp com API compatível com OpenAI
- **Banco de dados SQLite** substituindo Supabase
- **Autenticação local** sem necessidade de serviços externos
- **Vector store local** usando FAISS para busca semântica
- **Interface web completa** com frontend Next.js
- **Ferramentas locais** substituindo APIs externas (busca, geração de imagem, etc.)

## 📋 Requisitos do Sistema

### Hardware Mínimo
- **CPU**: 4 cores (recomendado 8+ cores)
- **RAM**: 16GB (recomendado 32GB)
- **Armazenamento**: 20GB livres
- **GPU**: Não necessária (otimizado para CPU)

### Software
- **Windows 10/11** com WSL2 habilitado
- **Ubuntu 20.04+** no WSL2
- **Python 3.8+**
- **Node.js 18+**
- **Git**

## 🚀 Instalação Rápida

### 1. Preparar o WSL2

```bash
# No PowerShell como Administrador
wsl --install Ubuntu
wsl --set-default-version 2
```

### 2. Clonar o Repositório

```bash
# No terminal WSL2
git clone <este-repositorio>
cd suna-wsl2-setup
```

### 3. Executar Instalação

```bash
# Executar como usuário normal (não root)
./install-wsl2.sh
```

### 4. Iniciar o Sistema

```bash
cd ~/suna-local
./start-suna.sh
```

### 5. Acessar a Interface

- **Frontend**: http://localhost:3000
- **API Backend**: http://localhost:8080
- **API Llama**: http://localhost:8000

## 📁 Estrutura do Projeto

```
~/suna-local/
├── backend/                 # Backend FastAPI
│   ├── agent/              # Lógica do agente
│   ├── services/           # Serviços locais
│   └── utils/              # Utilitários
├── frontend/               # Frontend Next.js
├── models/                 # Modelos de IA
│   └── mistral-7b-instruct-v0.2.Q4_K_M.gguf
├── data/                   # Dados locais
│   ├── sqlite/            # Banco SQLite
│   ├── vector_store/      # Vector store FAISS
│   └── logs/              # Logs do sistema
├── venv/                   # Ambiente virtual Python
└── scripts/                # Scripts de controle
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente

O sistema usa as seguintes variáveis de ambiente principais:

```bash
# Backend (.env)
ENV_MODE=LOCAL
OPENAI_API_KEY=sk-dummy-key
OPENAI_API_BASE=http://localhost:8000/v1
SQLITE_DB_PATH=./data/sqlite/suna.db
VECTOR_STORE_PATH=./data/vector_store
REDIS_URL=redis://localhost:6379

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8080
ENV_MODE=LOCAL
```

### Configuração do Modelo

Para usar um modelo diferente:

1. Baixe o modelo GGUF desejado
2. Coloque em `~/suna-local/models/`
3. Edite `start-llama.sh` para apontar para o novo modelo
4. Ajuste `MODEL_FILE` em `backend/.env`

### Configuração de Performance

Para otimizar performance:

```bash
# Editar start-llama.sh
python -m llama_cpp.server \
    --model ./models/seu-modelo.gguf \
    --n_threads $(nproc) \        # Usar todos os cores
    --n_ctx 4096 \                # Contexto maior
    --n_batch 512                 # Batch maior
```

## 🧪 Testes

### Suite de Testes Automatizada

```bash
# Executar todos os testes
python test_suite.py

# Testar diretório específico
python test_suite.py /caminho/para/suna-local
```

### Testes Manuais

#### 1. Testar Servidor Llama
```bash
cd ~/suna-local/backend
python test_llama_server.py
```

#### 2. Testar Backend
```bash
curl http://localhost:8080/health
```

#### 3. Testar Frontend
```bash
curl http://localhost:3000
```

## 🛠️ Solução de Problemas

### Problemas Comuns

#### 1. Servidor Llama não inicia
```bash
# Verificar logs
tail -f ~/suna-local/data/logs/llama.log

# Verificar modelo
ls -la ~/suna-local/models/

# Testar manualmente
cd ~/suna-local
source venv/bin/activate
python -m llama_cpp.server --model ./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf --host 0.0.0.0 --port 8000
```

#### 2. Backend não conecta ao Llama
```bash
# Verificar se Llama está rodando
curl http://localhost:8000/v1/models

# Verificar logs do backend
tail -f ~/suna-local/data/logs/backend.log
```

#### 3. Frontend não carrega
```bash
# Verificar se backend está rodando
curl http://localhost:8080/health

# Verificar logs do frontend
cd ~/suna-local/frontend
npm run dev
```

#### 4. Erro de memória
```bash
# Reduzir contexto do modelo
# Editar start-llama.sh: --n_ctx 2048

# Usar modelo menor
# Baixar versão Q2_K em vez de Q4_K_M
```

### Logs e Diagnóstico

```bash
# Ver todos os logs
tail -f ~/suna-local/data/logs/*.log

# Verificar processos
ps aux | grep -E "(llama|uvicorn|node)"

# Verificar portas
netstat -tlnp | grep -E "(8000|8080|3000|6379)"

# Testar Redis
redis-cli ping
```

## 🔄 Controle do Sistema

### Scripts de Controle

```bash
# Iniciar todos os serviços
./start-suna.sh

# Parar todos os serviços
./stop-suna.sh

# Iniciar serviços individuais
./start-llama.sh      # Apenas Llama
./start-backend.sh    # Apenas Backend
./start-frontend.sh   # Apenas Frontend
./start-redis.sh      # Apenas Redis
```

### Monitoramento

```bash
# Verificar status dos serviços
ps aux | grep -E "(llama_cpp|uvicorn|node|redis)"

# Verificar uso de recursos
htop

# Verificar logs em tempo real
tail -f ~/suna-local/data/logs/llama.log
tail -f ~/suna-local/data/logs/backend.log
```

## 🔧 Desenvolvimento

### Modificar o Backend

```bash
cd ~/suna-local/backend
source ../venv/bin/activate

# Editar código
nano agent/run.py

# Reiniciar backend
pkill -f "uvicorn.*api:app"
./start-backend.sh
```

### Modificar o Frontend

```bash
cd ~/suna-local/frontend

# Editar código
nano src/pages/index.tsx

# O frontend recarrega automaticamente em modo dev
```

### Adicionar Novas Ferramentas

1. Criar nova ferramenta em `backend/agent/tools/`
2. Registrar em `backend/agent/run.py`
3. Testar com `python test_suite.py`

## 📊 Performance e Otimização

### Benchmarks Típicos

| Componente | Tempo de Inicialização | Uso de RAM | Uso de CPU |
|------------|----------------------|------------|------------|
| Llama Server | 30-60s | 4-8GB | 50-100% |
| Backend | 5-10s | 200-500MB | 5-15% |
| Frontend | 10-20s | 100-300MB | 5-10% |
| Redis | 1-2s | 50-100MB | 1-5% |

### Otimizações

#### Para Sistemas com Pouca RAM
```bash
# Usar modelo menor
wget -O ~/suna-local/models/mistral-7b-q2.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q2_K.gguf"

# Reduzir contexto
# Editar start-llama.sh: --n_ctx 2048
```

#### Para Sistemas com Muitos Cores
```bash
# Aumentar threads
# Editar start-llama.sh: --n_threads 16

# Aumentar batch size
# Editar start-llama.sh: --n_batch 1024
```

## 🔐 Segurança

### Configurações de Segurança

- **Autenticação local**: Sistema de tokens JWT local
- **Isolamento**: Todos os serviços rodam localmente
- **Dados**: Todos os dados ficam no sistema local
- **Rede**: Sem comunicação externa necessária

### Backup e Recuperação

```bash
# Backup dos dados
tar -czf suna-backup-$(date +%Y%m%d).tar.gz ~/suna-local/data/

# Backup da configuração
cp ~/suna-local/backend/.env ~/suna-local/backend/.env.backup
cp ~/suna-local/frontend/.env.local ~/suna-local/frontend/.env.local.backup

# Restaurar dados
tar -xzf suna-backup-YYYYMMDD.tar.gz -C ~/
```

## 🆕 Atualizações

### Atualizar o Sistema

```bash
# Parar serviços
./stop-suna.sh

# Fazer backup
tar -czf suna-backup-$(date +%Y%m%d).tar.gz ~/suna-local/data/

# Atualizar código
git pull origin main

# Aplicar patches
python backend-patches/apply_patches.py ~/suna-local/backend ./backend-patches/

# Reinstalar dependências se necessário
cd ~/suna-local/backend
source ../venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install

# Reiniciar serviços
./start-suna.sh
```

## 🤝 Contribuição

### Reportar Problemas

1. Execute `python test_suite.py` e inclua os resultados
2. Inclua logs relevantes de `~/suna-local/data/logs/`
3. Descreva o ambiente (WSL2, Ubuntu version, hardware)

### Desenvolvimento

1. Fork o repositório
2. Crie uma branch para sua feature
3. Teste com `python test_suite.py`
4. Submeta um pull request

## 📄 Licença

Este projeto é licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

## 🙏 Agradecimentos

- [SUNA AI](https://github.com/kortix-ai/suna) - Framework original
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Inferência eficiente de modelos LLaMA
- [Mistral AI](https://mistral.ai/) - Modelo Mistral 7B
- [FAISS](https://github.com/facebookresearch/faiss) - Biblioteca de busca vetorial

## 📞 Suporte

Para suporte técnico:

1. Consulte a seção de Solução de Problemas
2. Execute a suite de testes: `python test_suite.py`
3. Verifique os logs em `~/suna-local/data/logs/`
4. Abra uma issue no repositório com informações detalhadas

---

**Desenvolvido por Manus AI** - Adaptação local do SUNA para WSL2

