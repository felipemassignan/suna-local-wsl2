"""
Local LLM service using llama.cpp server
Substitui a integração com OpenAI por uma implementação local
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from utils.logger import logger
from utils.config import config, is_local_mode


class LocalLLMService:
    """Service for interacting with local llama.cpp server"""
    
    def __init__(self):
        self.base_url = config.OPENAI_API_BASE or "http://localhost:8000/v1"
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def health_check(self) -> bool:
        """Check if the local LLM server is running"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/models", timeout=5) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def make_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Make a completion request to the local LLM"""
        
        if not is_local_mode():
            raise ValueError("LocalLLMService should only be used in LOCAL mode")
        
        model = model or config.DEFAULT_MODEL
        temperature = temperature or config.TEMPERATURE
        max_tokens = max_tokens or config.MAX_TOKENS
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        try:
            session = await self._get_session()
            
            if stream:
                return await self._stream_completion(session, payload)
            else:
                return await self._single_completion(session, payload)
                
        except Exception as e:
            logger.error(f"Completion request failed: {e}")
            # Return a fallback response
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}"
                    },
                    "finish_reason": "error"
                }],
                "usage": {"total_tokens": 0}
            }
    
    async def _single_completion(self, session: aiohttp.ClientSession, payload: Dict) -> Dict[str, Any]:
        """Make a single completion request"""
        async with session.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"HTTP {response.status}: {error_text}")
    
    async def _stream_completion(self, session: aiohttp.ClientSession, payload: Dict) -> AsyncGenerator[str, None]:
        """Make a streaming completion request"""
        async with session.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"HTTP {response.status}: {error_text}")
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                    except json.JSONDecodeError:
                        continue


# Global service instance
local_llm_service = LocalLLMService()


async def make_llm_api_call(
    model: str = None,
    messages: List[Dict[str, str]] = None,
    temperature: float = None,
    max_tokens: int = None,
    stream: bool = False
) -> Dict[str, Any]:
    """
    Make an API call to the local LLM service
    Compatible with the original make_llm_api_call interface
    """
    
    if not is_local_mode():
        # In non-local mode, fall back to original OpenAI implementation
        # This would be imported from the original services.llm module
        raise NotImplementedError("Non-local mode not implemented in this version")
    
    if not messages:
        messages = [{"role": "user", "content": "Hello"}]
    
    return await local_llm_service.make_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=stream
    )


async def stream_llm_response(
    model: str = None,
    messages: List[Dict[str, str]] = None,
    temperature: float = None,
    max_tokens: int = None
) -> AsyncGenerator[str, None]:
    """
    Stream response from the local LLM service
    """
    
    if not is_local_mode():
        raise NotImplementedError("Non-local mode not implemented in this version")
    
    if not messages:
        messages = [{"role": "user", "content": "Hello"}]
    
    async for chunk in local_llm_service._stream_completion(
        await local_llm_service._get_session(),
        {
            "model": model or config.DEFAULT_MODEL,
            "messages": messages,
            "temperature": temperature or config.TEMPERATURE,
            "max_tokens": max_tokens or config.MAX_TOKENS,
            "stream": True
        }
    ):
        yield chunk


# Cleanup function
async def cleanup_llm_service():
    """Cleanup the LLM service"""
    await local_llm_service.close()

