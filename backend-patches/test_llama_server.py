#!/usr/bin/env python3
"""
Script de teste para verificar se o servidor llama.cpp está funcionando
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any


async def test_llama_server(base_url: str = "http://localhost:8000") -> bool:
    """Test the llama.cpp server"""
    
    print(f"Testando servidor Llama em {base_url}...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test 1: Check if server is running
            print("1. Verificando se o servidor está rodando...")
            async with session.get(f"{base_url}/v1/models", timeout=10) as response:
                if response.status == 200:
                    models = await response.json()
                    print(f"   ✓ Servidor está rodando. Modelos disponíveis: {len(models.get('data', []))}")
                else:
                    print(f"   ✗ Erro ao acessar modelos: HTTP {response.status}")
                    return False
            
            # Test 2: Simple completion
            print("2. Testando completion simples...")
            completion_payload = {
                "model": "local-mistral",
                "messages": [
                    {"role": "user", "content": "Diga olá em português"}
                ],
                "max_tokens": 50,
                "temperature": 0.7
            }
            
            async with session.post(
                f"{base_url}/v1/chat/completions",
                json=completion_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"   ✓ Completion funcionando. Resposta: {content[:100]}...")
                else:
                    error_text = await response.text()
                    print(f"   ✗ Erro no completion: HTTP {response.status} - {error_text}")
                    return False
            
            # Test 3: Streaming completion
            print("3. Testando streaming completion...")
            stream_payload = {
                "model": "local-mistral",
                "messages": [
                    {"role": "user", "content": "Conte até 5"}
                ],
                "max_tokens": 30,
                "temperature": 0.7,
                "stream": True
            }
            
            chunks_received = 0
            async with session.post(
                f"{base_url}/v1/chat/completions",
                json=stream_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        chunks_received += 1
                            except json.JSONDecodeError:
                                continue
                    
                    if chunks_received > 0:
                        print(f"   ✓ Streaming funcionando. Recebidos {chunks_received} chunks")
                    else:
                        print("   ⚠ Streaming conectou mas não recebeu chunks válidos")
                else:
                    error_text = await response.text()
                    print(f"   ✗ Erro no streaming: HTTP {response.status} - {error_text}")
                    return False
            
            print("\n✅ Todos os testes passaram! O servidor Llama está funcionando corretamente.")
            return True
            
    except asyncio.TimeoutError:
        print("   ✗ Timeout ao conectar com o servidor")
        return False
    except aiohttp.ClientConnectorError:
        print("   ✗ Não foi possível conectar ao servidor. Verifique se está rodando.")
        return False
    except Exception as e:
        print(f"   ✗ Erro inesperado: {e}")
        return False


async def wait_for_server(base_url: str = "http://localhost:8000", max_wait: int = 60) -> bool:
    """Wait for the server to be ready"""
    
    print(f"Aguardando servidor ficar pronto (máximo {max_wait}s)...")
    
    for i in range(max_wait):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/v1/models", timeout=5) as response:
                    if response.status == 200:
                        print(f"   ✓ Servidor pronto após {i+1}s")
                        return True
        except:
            pass
        
        if i % 10 == 0 and i > 0:
            print(f"   Ainda aguardando... ({i}s)")
        
        await asyncio.sleep(1)
    
    print(f"   ✗ Servidor não ficou pronto em {max_wait}s")
    return False


def print_usage():
    """Print usage information"""
    print("Uso:")
    print("  python test_llama_server.py [test|wait] [url]")
    print("")
    print("Comandos:")
    print("  test  - Testa o servidor (padrão)")
    print("  wait  - Aguarda o servidor ficar pronto")
    print("")
    print("Exemplos:")
    print("  python test_llama_server.py")
    print("  python test_llama_server.py test http://localhost:8000")
    print("  python test_llama_server.py wait")


async def main():
    """Main function"""
    
    command = "test"
    base_url = "http://localhost:8000"
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
    
    if len(sys.argv) > 2:
        base_url = sys.argv[2]
    
    if command not in ["test", "wait"]:
        print_usage()
        sys.exit(1)
    
    if command == "wait":
        success = await wait_for_server(base_url)
    else:
        success = await test_llama_server(base_url)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

