#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== SUNA Local Setup para WSL2 ===${NC}"
echo -e "${BLUE}Configuração totalmente local com Llama e banco de dados local${NC}"

# Check if running on WSL2
if ! grep -q "microsoft" /proc/version 2>/dev/null; then
    echo -e "${YELLOW}Aviso: Este script foi otimizado para WSL2. Continuando...${NC}"
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Por favor, execute como usuário normal (não root)${NC}"
    echo -e "${YELLOW}O script solicitará sudo quando necessário${NC}"
    exit 1
fi

# Get current user
CURRENT_USER=$(whoami)
INSTALL_DIR="$HOME/suna-local"
VENV_DIR="$INSTALL_DIR/venv"
MODELS_DIR="$INSTALL_DIR/models"
DATA_DIR="$INSTALL_DIR/data"

echo -e "${YELLOW}Usuário: $CURRENT_USER${NC}"
echo -e "${YELLOW}Diretório de instalação: $INSTALL_DIR${NC}"

# Create directories
echo -e "${YELLOW}Criando diretórios...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$MODELS_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$DATA_DIR/vector_store"
mkdir -p "$DATA_DIR/sqlite"
mkdir -p "$DATA_DIR/logs"

# Update system packages
echo -e "${YELLOW}Atualizando pacotes do sistema...${NC}"
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nodejs npm redis-server sqlite3 \
    build-essential cmake pkg-config libopenblas-dev wget curl git unzip

# Install Node.js 18+ if needed
NODE_VERSION=$(node --version 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1 || echo "0")
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${YELLOW}Instalando Node.js 18...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Set up Python virtual environment
echo -e "${YELLOW}Configurando ambiente virtual Python...${NC}"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install llama-cpp-python with OpenBLAS support for better CPU performance
echo -e "${YELLOW}Instalando llama-cpp-python com suporte OpenBLAS...${NC}"
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python[server]

# Install other Python dependencies
echo -e "${YELLOW}Instalando dependências Python...${NC}"
pip install fastapi uvicorn python-multipart redis \
    sentence-transformers faiss-cpu numpy pandas \
    python-dotenv pydantic requests aiofiles \
    streamlit plotly altair

# Download Mistral 7B model if not already present
MODEL_FILE="$MODELS_DIR/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
if [ ! -f "$MODEL_FILE" ]; then
    echo -e "${YELLOW}Baixando modelo Mistral 7B (isso pode demorar)...${NC}"
    wget -O "$MODEL_FILE" \
        "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
else
    echo -e "${GREEN}Modelo Mistral 7B já existe, pulando download${NC}"
fi

# Clone Suna repository if not exists
SUNA_REPO_DIR="$INSTALL_DIR/suna-repo"
if [ ! -d "$SUNA_REPO_DIR" ]; then
    echo -e "${YELLOW}Clonando repositório Suna...${NC}"
    git clone https://github.com/felipemassignan/suna-local-wsl2.git "$SUNA_REPO_DIR"
else
    echo -e "${GREEN}Repositório Suna já existe${NC}"
fi

# Copy and modify backend
echo -e "${YELLOW}Configurando backend...${NC}"
cp -r "$SUNA_REPO_DIR/backend" "$INSTALL_DIR/"
cd "$INSTALL_DIR/backend"

# Install backend dependencies
pip install -r requirements.txt

# Copy and modify frontend
echo -e "${YELLOW}Configurando frontend...${NC}"
cp -r "$SUNA_REPO_DIR/frontend" "$INSTALL_DIR/"
cd "$INSTALL_DIR/frontend"

# Install frontend dependencies
npm install

# Create backend configuration
echo -e "${YELLOW}Criando configuração do backend...${NC}"
cat > "$INSTALL_DIR/backend/.env" << EOF
ENV_MODE=LOCAL
OPENAI_API_KEY=sk-dummy-key
OPENAI_API_BASE=http://localhost:8000/v1
SUPABASE_URL=https://dummy.supabase.co
SUPABASE_KEY=dummy-key
REDIS_URL=redis://localhost:6379
SQLITE_DB_PATH=$DATA_DIR/sqlite/suna.db
VECTOR_STORE_PATH=$DATA_DIR/vector_store
MODELS_PATH=$MODELS_DIR
EOF

# Create frontend configuration
echo -e "${YELLOW}Criando configuração do frontend...${NC}"
cat > "$INSTALL_DIR/frontend/.env.local" << EOF
NEXT_PUBLIC_SUPABASE_URL=https://dummy.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=dummy-key
NEXT_PUBLIC_API_URL=http://localhost:8080
ENV_MODE=LOCAL
EOF

# Create startup scripts
echo -e "${YELLOW}Criando scripts de inicialização...${NC}"

# Llama server startup script
cat > "$INSTALL_DIR/start-llama.sh" << EOF
#!/bin/bash
source "$VENV_DIR/bin/activate"
echo "Iniciando servidor Llama..."
python -m llama_cpp.server \\
    --model "$MODEL_FILE" \\
    --host 0.0.0.0 \\
    --port 8000 \\
    --n_ctx 4096 \\
    --n_threads \$(nproc) \\
    --verbose
EOF

# Backend startup script
cat > "$INSTALL_DIR/start-backend.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR/backend"
source "$VENV_DIR/bin/activate"
echo "Iniciando backend..."
uvicorn api:app --host 0.0.0.0 --port 8080 --reload
EOF

# Frontend startup script
cat > "$INSTALL_DIR/start-frontend.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR/frontend"
echo "Iniciando frontend..."
npm run dev -- --port 3000
EOF

# Redis startup script
cat > "$INSTALL_DIR/start-redis.sh" << EOF
#!/bin/bash
echo "Iniciando Redis..."
redis-server --daemonize yes --port 6379
EOF

# Main startup script
cat > "$INSTALL_DIR/start-suna.sh" << EOF
#!/bin/bash

echo "=== Iniciando SUNA Local ==="

# Start Redis
echo "Iniciando Redis..."
redis-server --daemonize yes --port 6379
sleep 2

# Start Llama server in background
echo "Iniciando servidor Llama..."
cd "$INSTALL_DIR"
source "$VENV_DIR/bin/activate"
nohup python -m llama_cpp.server \\
    --model "$MODEL_FILE" \\
    --host 0.0.0.0 \\
    --port 8000 \\
    --n_ctx 4096 \\
    --n_threads \$(nproc) > "$DATA_DIR/logs/llama.log" 2>&1 &

echo "Aguardando servidor Llama inicializar..."
sleep 15

# Start backend in background
echo "Iniciando backend..."
cd "$INSTALL_DIR/backend"
nohup uvicorn api:app --host 0.0.0.0 --port 8080 > "$DATA_DIR/logs/backend.log" 2>&1 &

echo "Aguardando backend inicializar..."
sleep 5

# Start frontend
echo "Iniciando frontend..."
cd "$INSTALL_DIR/frontend"
npm run dev -- --port 3000

EOF

# Stop script
cat > "$INSTALL_DIR/stop-suna.sh" << EOF
#!/bin/bash

echo "=== Parando SUNA Local ==="

# Stop processes
pkill -f "llama_cpp.server"
pkill -f "uvicorn.*api:app"
pkill -f "next.*dev"
redis-cli shutdown

echo "Todos os serviços foram parados."
EOF

# Make scripts executable
chmod +x "$INSTALL_DIR"/*.sh

# Create desktop shortcut if in WSL2 with Windows integration
if command -v cmd.exe >/dev/null 2>&1; then
    echo -e "${YELLOW}Criando atalho no desktop do Windows...${NC}"
    WINDOWS_USER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')
    DESKTOP_PATH="/mnt/c/Users/$WINDOWS_USER/Desktop"
    
    if [ -d "$DESKTOP_PATH" ]; then
        cat > "$DESKTOP_PATH/SUNA-Local.bat" << EOF
@echo off
wsl -d Ubuntu bash -c "cd $INSTALL_DIR && ./start-suna.sh"
EOF
        echo -e "${GREEN}Atalho criado no desktop: SUNA-Local.bat${NC}"
    fi
fi

# Build frontend
echo -e "${YELLOW}Compilando frontend...${NC}"
cd "$INSTALL_DIR/frontend"
npm run build

echo -e "${GREEN}=== Instalação concluída! ===${NC}"
echo -e ""
echo -e "${BLUE}Para iniciar o SUNA:${NC}"
echo -e "  cd $INSTALL_DIR"
echo -e "  ./start-suna.sh"
echo -e ""
echo -e "${BLUE}Para parar o SUNA:${NC}"
echo -e "  ./stop-suna.sh"
echo -e ""
echo -e "${BLUE}URLs de acesso:${NC}"
echo -e "  Frontend: http://localhost:3000"
echo -e "  Backend API: http://localhost:8080"
echo -e "  Llama API: http://localhost:8000"
echo -e ""
echo -e "${YELLOW}Logs estão em: $DATA_DIR/logs/${NC}"
echo -e "${YELLOW}Dados estão em: $DATA_DIR/${NC}"

