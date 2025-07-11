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

# Clonar repositório Suna
echo -e "${YELLOW}[3/8] Clonando repositório Suna...${NC}"
git clone https://github.com/88atman77/suna-local-setup.git /opt/suna/repo
cp -r /opt/suna/repo/backend /opt/suna/
cp -r /opt/suna/repo/frontend /opt/suna/

# Baixar modelo Mistral 7B
echo -e "${YELLOW}[4/8] Baixando modelo Mistral 7B...${NC}"
mkdir -p /etc/suna/models
wget -O /etc/suna/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# Instalar Redis (sem systemd)
echo -e "${YELLOW}[5/8] Configurando Redis...${NC}"
sudo apt install -y redis-server

# Configurar ambiente Python
echo -e "${YELLOW}[6/8] Criando ambiente virtual...${NC}"
sudo mkdir -p /opt/suna
sudo chown -R $USER:$USER /opt/suna
python3 -m venv /opt/suna/venv
source /opt/suna/venv/bin/activate

# Instalar llama-cpp-python com suporte a CUDA E requirements
echo -e "${YELLOW}[7/8] Instalando llama-cpp-python e Requirements do Backend...${NC}"
CMAKE_ARGS="-DLLAMA_CUDA=ON -DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" \
pip install llama-cpp-python[server] 
cd /opt/suna/frontend
pip install –r requirements.txt

# Instalar dependências do frontend
echo -e "${YELLOW}[7/8] Instalando dependências do frontend...${NC}"
cd /opt/suna/frontend
npm install

echo -e "${GREEN}✅ Instalação concluída com sucesso!${NC}"
echo -e "Execute o Suna com: ${YELLOW}./start-suna-wsl2.sh${NC}"
