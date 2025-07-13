# Guia Completo de Instalação - SUNA Local WSL2

Este guia fornece instruções passo a passo para instalar e configurar o SUNA Local no WSL2 do Windows.

## 📋 Pré-requisitos

### 1. Verificar Requisitos do Sistema

Antes de começar, verifique se seu sistema atende aos requisitos:

- **Windows 10 versão 2004+** ou **Windows 11**
- **16GB RAM** (mínimo) - 32GB recomendado
- **20GB espaço livre** em disco
- **Processador x64** com suporte à virtualização

### 2. Habilitar WSL2

#### No PowerShell como Administrador:

```powershell
# Habilitar WSL
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Habilitar Virtual Machine Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Reiniciar o computador
Restart-Computer
```

#### Após reiniciar:

```powershell
# Baixar e instalar o kernel do WSL2
# Baixe de: https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi

# Definir WSL2 como padrão
wsl --set-default-version 2

# Instalar Ubuntu
wsl --install -d Ubuntu
```

### 3. Configurar Ubuntu no WSL2

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências básicas
sudo apt install -y curl wget git build-essential
```

## 🚀 Instalação do SUNA Local

### Passo 1: Baixar o Projeto

```bash
# Clonar o repositório
git clone <url-do-repositorio> ~/suna-wsl2-setup
cd ~/suna-wsl2-setup

# Verificar conteúdo
ls -la
```

### Passo 2: Executar Instalação Automática

```bash
# Tornar o script executável
chmod +x install-wsl2.sh

# Executar instalação (como usuário normal, não root)
./install-wsl2.sh
```

O script de instalação irá:

1. ✅ Verificar e instalar dependências do sistema
2. ✅ Configurar ambiente Python com virtual environment
3. ✅ Instalar llama-cpp-python com suporte OpenBLAS
4. ✅ Baixar modelo Mistral 7B (pode demorar 10-30 minutos)
5. ✅ Clonar e configurar repositório SUNA original
6. ✅ Aplicar patches para modo local
7. ✅ Configurar frontend Next.js
8. ✅ Criar scripts de inicialização
9. ✅ Configurar banco de dados SQLite
10. ✅ Criar atalho no desktop do Windows (se disponível)

### Passo 3: Verificar Instalação

```bash
# Verificar estrutura criada
ls -la ~/suna-local/

# Executar testes
cd ~/suna-wsl2-setup
python test_suite.py ~/suna-local
```

## 🔧 Configuração Manual (se necessário)

### Se a Instalação Automática Falhar

#### 1. Configurar Ambiente Python

```bash
# Criar diretório
mkdir -p ~/suna-local
cd ~/suna-local

# Criar virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalar llama-cpp-python
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python[server]

# Instalar outras dependências
pip install fastapi uvicorn aiosqlite sentence-transformers faiss-cpu redis python-dotenv
```

#### 2. Baixar Modelo Manualmente

```bash
# Criar diretório de modelos
mkdir -p ~/suna-local/models

# Baixar modelo Mistral 7B
wget -O ~/suna-local/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
```

#### 3. Configurar Backend

```bash
# Clonar SUNA original
git clone https://github.com/kortix-ai/suna.git ~/suna-local/suna-repo

# Copiar backend
cp -r ~/suna-local/suna-repo/backend ~/suna-local/

# Aplicar patches
cd ~/suna-wsl2-setup
python backend-patches/apply_patches.py ~/suna-local/backend ./backend-patches/

# Instalar dependências do backend
cd ~/suna-local/backend
source ../venv/bin/activate
pip install -r requirements.txt
```

#### 4. Configurar Frontend

```bash
# Copiar frontend
cp -r ~/suna-local/suna-repo/frontend ~/suna-local/

# Instalar dependências
cd ~/suna-local/frontend
npm install

# Build do frontend
npm run build
```

#### 5. Criar Configurações

```bash
# Configuração do backend
cat > ~/suna-local/backend/.env << EOF
ENV_MODE=LOCAL
OPENAI_API_KEY=sk-dummy-key
OPENAI_API_BASE=http://localhost:8000/v1
SUPABASE_URL=https://dummy.supabase.co
SUPABASE_KEY=dummy-key
REDIS_URL=redis://localhost:6379
SQLITE_DB_PATH=./data/sqlite/suna.db
VECTOR_STORE_PATH=./data/vector_store
MODELS_PATH=../models
EOF

# Configuração do frontend
cat > ~/suna-local/frontend/.env.local << EOF
NEXT_PUBLIC_SUPABASE_URL=https://dummy.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=dummy-key
NEXT_PUBLIC_API_URL=http://localhost:8080
ENV_MODE=LOCAL
EOF
```

## 🎯 Primeira Execução

### Passo 1: Iniciar Serviços

```bash
cd ~/suna-local

# Iniciar todos os serviços
./start-suna.sh
```

O script irá:
1. Iniciar Redis
2. Iniciar servidor Llama (pode demorar 1-2 minutos)
3. Iniciar backend FastAPI
4. Iniciar frontend Next.js

### Passo 2: Verificar Serviços

```bash
# Verificar se todos os serviços estão rodando
ps aux | grep -E "(llama_cpp|uvicorn|node|redis)"

# Verificar portas
netstat -tlnp | grep -E "(8000|8080|3000|6379)"

# Testar endpoints
curl http://localhost:8000/v1/models    # Llama
curl http://localhost:8080/health       # Backend
curl http://localhost:3000              # Frontend
```

### Passo 3: Acessar Interface

1. Abra o navegador no Windows
2. Acesse: http://localhost:3000
3. A interface do SUNA deve carregar

## 🔍 Verificação e Testes

### Teste Rápido

```bash
# Executar suite de testes
cd ~/suna-wsl2-setup
python test_suite.py ~/suna-local
```

### Teste Manual do Llama

```bash
cd ~/suna-local/backend
python test_llama_server.py
```

### Teste de Integração

```bash
# Testar completion via API
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-mistral",
    "messages": [{"role": "user", "content": "Olá, como você está?"}],
    "max_tokens": 50
  }'
```

## 🛠️ Solução de Problemas na Instalação

### Problema: Download do Modelo Falha

```bash
# Tentar download manual com curl
curl -L -o ~/suna-local/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"

# Ou usar wget com retry
wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 0 \
  -O ~/suna-local/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
```

### Problema: Erro de Compilação llama-cpp-python

```bash
# Instalar dependências de build
sudo apt install -y build-essential cmake pkg-config libopenblas-dev

# Limpar cache pip
pip cache purge

# Reinstalar com flags específicos
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install --no-cache-dir llama-cpp-python[server]
```

### Problema: Node.js Muito Antigo

```bash
# Instalar Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verificar versão
node --version  # Deve ser 18+
npm --version
```

### Problema: Permissões

```bash
# Corrigir permissões do diretório
sudo chown -R $USER:$USER ~/suna-local

# Tornar scripts executáveis
chmod +x ~/suna-local/*.sh
```

### Problema: Porta em Uso

```bash
# Verificar o que está usando as portas
sudo netstat -tlnp | grep -E "(8000|8080|3000|6379)"

# Matar processos se necessário
sudo pkill -f "llama_cpp"
sudo pkill -f "uvicorn"
sudo pkill -f "node.*next"
```

## 🔄 Configuração de Inicialização Automática

### Criar Serviço Systemd (Opcional)

```bash
# Criar arquivo de serviço
sudo tee /etc/systemd/system/suna-local.service << EOF
[Unit]
Description=SUNA Local Service
After=network.target

[Service]
Type=forking
User=$USER
WorkingDirectory=$HOME/suna-local
ExecStart=$HOME/suna-local/start-suna.sh
ExecStop=$HOME/suna-local/stop-suna.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Habilitar serviço
sudo systemctl enable suna-local.service
sudo systemctl start suna-local.service
```

### Atalho no Desktop do Windows

Se o script de instalação não criou automaticamente:

```batch
@echo off
wsl -d Ubuntu bash -c "cd ~/suna-local && ./start-suna.sh"
```

Salve como `SUNA-Local.bat` no desktop.

## 📊 Monitoramento da Instalação

### Verificar Progresso

```bash
# Monitorar logs durante instalação
tail -f ~/suna-local/data/logs/llama.log
tail -f ~/suna-local/data/logs/backend.log

# Verificar uso de recursos
htop

# Verificar espaço em disco
df -h
```

### Verificar Integridade

```bash
# Verificar arquivos importantes
ls -la ~/suna-local/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
ls -la ~/suna-local/backend/.env
ls -la ~/suna-local/frontend/.env.local

# Verificar banco de dados
sqlite3 ~/suna-local/data/sqlite/suna.db ".tables"
```

## ✅ Checklist de Instalação Completa

- [ ] WSL2 instalado e funcionando
- [ ] Ubuntu configurado no WSL2
- [ ] Script de instalação executado com sucesso
- [ ] Modelo Mistral 7B baixado (arquivo ~4GB)
- [ ] Ambiente Python criado e dependências instaladas
- [ ] Frontend Next.js configurado
- [ ] Banco de dados SQLite inicializado
- [ ] Todos os serviços iniciando corretamente
- [ ] Interface web acessível em http://localhost:3000
- [ ] Testes passando com `python test_suite.py`

## 🎉 Próximos Passos

Após a instalação bem-sucedida:

1. **Explore a Interface**: Acesse http://localhost:3000 e familiarize-se com a interface
2. **Teste o Agente**: Crie um novo thread e teste conversas com o agente
3. **Configure Preferências**: Ajuste configurações conforme necessário
4. **Backup**: Faça backup da configuração funcionando
5. **Monitore Performance**: Use `htop` para monitorar uso de recursos

---

**Suporte**: Se encontrar problemas, consulte a seção de solução de problemas no README.md ou execute `python test_suite.py` para diagnóstico automático.

