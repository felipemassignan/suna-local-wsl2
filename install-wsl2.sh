#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Instalando Suna Local Setup no WSL2...${NC}"

# Atualizar sistema
echo -e "${YELLOW}[1/8] Atualizando sistema...${NC}"
sudo apt update && sudo apt upgrade -y

# Instalar dependências
echo -e "${YELLOW}[2/8] Instalando dependências...${NC}"
sudo apt install -y python3 python3-pip python3-venv nodejs npm git wget build-essential ninja-build

# Configurar ambiente Python
echo -e "${YELLOW}[3/8] Criando ambiente virtual...${NC}"
sudo mkdir -p /opt/suna
sudo chown -R $USER:$USER /opt/suna
python3 -m venv /opt/suna/venv
source /opt/suna/venv/bin/activate

# Instalar llama-cpp-python com suporte a CUDA
echo -e "${YELLOW}[4/8] Instalando llama-cpp-python...${NC}"
CMAKE_ARGS="-DLLAMA_CUDA=ON -DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" \
pip install llama-cpp-python[server] torch numpy fastapi uvicorn
pip install requirements.txt

# Baixar modelo Mistral 7B
echo -e "${YELLOW}[5/8] Baixando modelo Mistral 7B...${NC}"
mkdir -p /etc/suna/models
wget -O /etc/suna/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# Instalar Redis
echo -e "${YELLOW}[6/8] Configurando Redis...${NC}"
sudo apt install -y redis-server

# Clonar repositório Suna e instalar dependências
echo -e "${YELLOW}[7/8] Configurando Suna...${NC}"
git clone https://github.com/felipemassignan/suna-local-wsl2.git /opt/suna/repo
cp -r /opt/suna/repo/backend /opt/suna/
cp -r /opt/suna/repo/frontend /opt/suna/

# Instalar requirements do backend
cd /opt/suna/backend
pip install -r requirements.txt

# Instalar dependências do frontend
echo -e "${YELLOW}[8/8] Instalando frontend...${NC}"
cd /opt/suna/frontend
npm install
npm audit fix --force

echo -e "${GREEN}✅ Instalação concluída com sucesso!${NC}"
echo -e "Execute o Suna com: ${YELLOW}./start-suna-wsl2.sh${NC}"