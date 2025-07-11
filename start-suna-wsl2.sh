#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para verificar se um serviço está rodando
check_service() {
  if ! pgrep -f "$1" >/dev/null; then
    echo -e "${RED}Erro: $1 não está rodando${NC}"
    exit 1
  fi
}

echo -e "${GREEN}Iniciando serviços do Suna no WSL2...${NC}"

# Iniciar Redis
echo -e "${YELLOW}[1/4] Iniciando Redis...${NC}"
redis-server --daemonize yes
check_service "redis-server"

# Iniciar llama.cpp server
echo -e "${YELLOW}[2/4] Iniciando llama.cpp server...${NC}"
cd /opt/suna
source venv/bin/activate
python -m llama_cpp.server \
  --model /etc/suna/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  --host 0.0.0.0 --port 8000 \
  --n_gpu_layers -1 \
  --n_ctx 4096 > /var/log/suna/llama.log 2>&1 &
check_service "llama_cpp.server"

# Esperar inicialização do llama.cpp
echo -e "${YELLOW}Aguardando inicialização do llama.cpp (10s)...${NC}"
sleep 10

# Iniciar backend
echo -e "${YELLOW}[3/4] Iniciando backend...${NC}"
cd /opt/suna/backend
source ../venv/bin/activate
uvicorn api:app --host 0.0.0.0 --port 8080 > /var/log/suna/backend.log 2>&1 &
check_service "uvicorn"

# Iniciar frontend
echo -e "${YELLOW}[4/4] Iniciando frontend...${NC}"
cd /opt/suna/frontend
npm run dev > /var/log/suna/frontend.log 2>&1 &
check_service "npm run dev"

echo -e "${GREEN}✅ Todos os serviços iniciados com sucesso!${NC}"
echo -e "\nAcesse:"
echo -e "  Frontend: ${YELLOW}http://localhost:3000${NC}"
echo -e "  API: ${YELLOW}http://localhost:8080${NC}"
echo -e "\nPara parar os serviços:"
echo -e "  ${YELLOW}pkill -f 'llama_cpp.server|uvicorn|npm run dev'${NC}"
echo -e "\nPara ver logs:"
echo -e "  ${YELLOW}tail -f /var/log/suna/*.log${NC}"