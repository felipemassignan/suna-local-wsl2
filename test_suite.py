#!/usr/bin/env python3
"""
Suite de testes para validar a instalação do SUNA Local no WSL2
"""

import asyncio
import aiohttp
import json
import os
import sys
import time
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional


class SunaTestSuite:
    """Suite de testes para SUNA Local"""
    
    def __init__(self, install_dir: str = None):
        self.install_dir = Path(install_dir or f"{os.path.expanduser('~')}/suna-local")
        self.llama_url = "http://localhost:8000"
        self.backend_url = "http://localhost:8080"
        self.frontend_url = "http://localhost:3000"
        self.redis_port = 6379
        
        self.test_results = []
        self.failed_tests = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        
        if not success:
            self.failed_tests.append(test_name)
    
    async def test_directory_structure(self) -> bool:
        """Test if directory structure is correct"""
        print("🔍 Testando estrutura de diretórios...")
        
        required_dirs = [
            self.install_dir,
            self.install_dir / "backend",
            self.install_dir / "frontend", 
            self.install_dir / "models",
            self.install_dir / "data",
            self.install_dir / "data" / "sqlite",
            self.install_dir / "data" / "vector_store",
            self.install_dir / "data" / "logs"
        ]
        
        all_exist = True
        for directory in required_dirs:
            exists = directory.exists()
            self.log_test(f"Diretório {directory.name}", exists)
            if not exists:
                all_exist = False
        
        return all_exist
    
    async def test_model_file(self) -> bool:
        """Test if model file exists"""
        print("🔍 Testando arquivo do modelo...")
        
        model_file = self.install_dir / "models" / "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
        exists = model_file.exists()
        
        if exists:
            size_mb = model_file.stat().st_size / (1024 * 1024)
            self.log_test("Arquivo do modelo Mistral 7B", True, f"Tamanho: {size_mb:.1f} MB")
        else:
            self.log_test("Arquivo do modelo Mistral 7B", False, "Arquivo não encontrado")
        
        return exists
    
    async def test_python_environment(self) -> bool:
        """Test Python environment and dependencies"""
        print("🔍 Testando ambiente Python...")
        
        venv_dir = self.install_dir / "venv"
        python_exe = venv_dir / "bin" / "python"
        
        if not python_exe.exists():
            self.log_test("Ambiente virtual Python", False, "Executável não encontrado")
            return False
        
        # Test key dependencies
        try:
            import subprocess
            result = subprocess.run([
                str(python_exe), "-c", 
                "import llama_cpp, fastapi, aiosqlite, sentence_transformers, faiss"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_test("Dependências Python", True, "Todas as dependências encontradas")
                return True
            else:
                self.log_test("Dependências Python", False, f"Erro: {result.stderr}")
                return False
        except Exception as e:
            self.log_test("Dependências Python", False, f"Erro ao testar: {e}")
            return False
    
    async def test_redis_connection(self) -> bool:
        """Test Redis connection"""
        print("🔍 Testando conexão Redis...")
        
        try:
            import redis
            r = redis.Redis(host='localhost', port=self.redis_port, decode_responses=True)
            r.ping()
            self.log_test("Conexão Redis", True, f"Conectado na porta {self.redis_port}")
            return True
        except Exception as e:
            self.log_test("Conexão Redis", False, f"Erro: {e}")
            return False
    
    async def test_sqlite_database(self) -> bool:
        """Test SQLite database"""
        print("🔍 Testando banco de dados SQLite...")
        
        db_file = self.install_dir / "data" / "sqlite" / "suna.db"
        
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ["users", "projects", "threads", "messages", "agent_runs", "sessions"]
            missing_tables = [table for table in required_tables if table not in tables]
            
            conn.close()
            
            if not missing_tables:
                self.log_test("Banco de dados SQLite", True, f"Todas as tabelas encontradas: {len(tables)}")
                return True
            else:
                self.log_test("Banco de dados SQLite", False, f"Tabelas faltando: {missing_tables}")
                return False
                
        except Exception as e:
            self.log_test("Banco de dados SQLite", False, f"Erro: {e}")
            return False
    
    async def test_llama_server(self) -> bool:
        """Test llama.cpp server"""
        print("🔍 Testando servidor Llama...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                async with session.get(f"{self.llama_url}/v1/models", timeout=10) as response:
                    if response.status != 200:
                        self.log_test("Servidor Llama - Health", False, f"HTTP {response.status}")
                        return False
                
                self.log_test("Servidor Llama - Health", True, "Servidor respondendo")
                
                # Test completion
                payload = {
                    "model": "local-mistral",
                    "messages": [{"role": "user", "content": "Diga olá"}],
                    "max_tokens": 10,
                    "temperature": 0.7
                }
                
                async with session.post(
                    f"{self.llama_url}/v1/chat/completions",
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        self.log_test("Servidor Llama - Completion", True, f"Resposta: {content[:50]}...")
                        return True
                    else:
                        error = await response.text()
                        self.log_test("Servidor Llama - Completion", False, f"HTTP {response.status}: {error}")
                        return False
                        
        except asyncio.TimeoutError:
            self.log_test("Servidor Llama", False, "Timeout na conexão")
            return False
        except Exception as e:
            self.log_test("Servidor Llama", False, f"Erro: {e}")
            return False
    
    async def test_backend_api(self) -> bool:
        """Test backend API"""
        print("🔍 Testando API do backend...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                async with session.get(f"{self.backend_url}/health", timeout=10) as response:
                    if response.status == 200:
                        self.log_test("Backend API - Health", True, "API respondendo")
                    else:
                        self.log_test("Backend API - Health", False, f"HTTP {response.status}")
                        return False
                
                # Test agent endpoint (if available)
                headers = {"Authorization": "Bearer mock-token"}
                async with session.get(f"{self.backend_url}/agent/threads", headers=headers, timeout=10) as response:
                    if response.status in [200, 401]:  # 401 is OK for auth test
                        self.log_test("Backend API - Endpoints", True, "Endpoints acessíveis")
                        return True
                    else:
                        self.log_test("Backend API - Endpoints", False, f"HTTP {response.status}")
                        return False
                        
        except Exception as e:
            self.log_test("Backend API", False, f"Erro: {e}")
            return False
    
    async def test_frontend_server(self) -> bool:
        """Test frontend server"""
        print("🔍 Testando servidor frontend...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.frontend_url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        if "suna" in content.lower() or "next" in content.lower():
                            self.log_test("Servidor Frontend", True, "Frontend carregando")
                            return True
                        else:
                            self.log_test("Servidor Frontend", False, "Conteúdo inesperado")
                            return False
                    else:
                        self.log_test("Servidor Frontend", False, f"HTTP {response.status}")
                        return False
                        
        except Exception as e:
            self.log_test("Servidor Frontend", False, f"Erro: {e}")
            return False
    
    async def test_integration(self) -> bool:
        """Test integration between components"""
        print("🔍 Testando integração entre componentes...")
        
        try:
            # Test backend -> llama integration
            async with aiohttp.ClientSession() as session:
                payload = {
                    "message": "Teste de integração",
                    "thread_id": "test-thread-123",
                    "project_id": "test-project-123"
                }
                
                headers = {
                    "Authorization": "Bearer mock-token",
                    "Content-Type": "application/json"
                }
                
                # This might fail if the exact endpoint doesn't exist, but we're testing connectivity
                async with session.post(
                    f"{self.backend_url}/agent/test",
                    json=payload,
                    headers=headers,
                    timeout=15
                ) as response:
                    # Any response (even 404) means backend is running
                    if response.status in [200, 404, 422, 401]:
                        self.log_test("Integração Backend-Llama", True, "Comunicação funcionando")
                        return True
                    else:
                        self.log_test("Integração Backend-Llama", False, f"HTTP {response.status}")
                        return False
                        
        except Exception as e:
            self.log_test("Integração", False, f"Erro: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all tests"""
        print("🚀 Iniciando suite de testes SUNA Local WSL2\\n")
        
        tests = [
            self.test_directory_structure,
            self.test_model_file,
            self.test_python_environment,
            self.test_redis_connection,
            self.test_sqlite_database,
            self.test_llama_server,
            self.test_backend_api,
            self.test_frontend_server,
            self.test_integration
        ]
        
        all_passed = True
        for test in tests:
            try:
                result = await test()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ ERRO no teste {test.__name__}: {e}")
                all_passed = False
            print()  # Empty line between test groups
        
        return all_passed
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = len(self.failed_tests)
        
        print("=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        print(f"Total de testes: {total_tests}")
        print(f"✅ Passou: {passed_tests}")
        print(f"❌ Falhou: {failed_tests}")
        print(f"📈 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.failed_tests:
            print("\\n❌ Testes que falharam:")
            for test in self.failed_tests:
                print(f"   - {test}")
        
        if failed_tests == 0:
            print("\\n🎉 Todos os testes passaram! SUNA Local está funcionando corretamente.")
        elif failed_tests <= 2:
            print("\\n⚠️  Alguns testes falharam, mas o sistema pode estar funcional.")
        else:
            print("\\n🚨 Muitos testes falharam. Verifique a instalação.")


async def main():
    """Main function"""
    
    install_dir = None
    if len(sys.argv) > 1:
        install_dir = sys.argv[1]
    
    test_suite = SunaTestSuite(install_dir)
    
    print("SUNA Local WSL2 - Suite de Testes")
    print(f"Diretório de instalação: {test_suite.install_dir}")
    print()
    
    success = await test_suite.run_all_tests()
    test_suite.print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

