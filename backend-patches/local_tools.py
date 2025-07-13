"""
Local tools to replace external API dependencies
Ferramentas locais para substituir dependências de APIs externas
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.logger import logger
from utils.config import config, is_local_mode


class LocalSearchTool:
    """Local search tool that returns predefined results"""
    
    name = "local_search"
    description = "Busca informações localmente sem usar APIs externas"
    
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> Dict[str, List[Dict]]:
        """Load local knowledge base"""
        return {
            "tecnologia": [
                {
                    "title": "Inteligência Artificial e Machine Learning",
                    "content": "IA e ML são tecnologias fundamentais para automação e análise de dados.",
                    "url": "http://localhost/tech/ai-ml"
                },
                {
                    "title": "Desenvolvimento de Software",
                    "content": "Práticas modernas de desenvolvimento incluem DevOps, CI/CD e arquiteturas em nuvem.",
                    "url": "http://localhost/tech/software-dev"
                }
            ],
            "negócios": [
                {
                    "title": "Transformação Digital",
                    "content": "Empresas estão adotando tecnologias digitais para melhorar eficiência e competitividade.",
                    "url": "http://localhost/business/digital-transformation"
                }
            ],
            "geral": [
                {
                    "title": "Informação Local",
                    "content": "Esta é uma resposta padrão para consultas gerais no modo local.",
                    "url": "http://localhost/general/info"
                }
            ]
        }
    
    async def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search for information locally"""
        
        if not is_local_mode():
            raise ValueError("LocalSearchTool should only be used in LOCAL mode")
        
        query_lower = query.lower()
        results = []
        
        # Simple keyword matching
        for category, items in self.knowledge_base.items():
            if any(keyword in query_lower for keyword in [category, "tecnologia", "tech", "ai", "ml"]):
                results.extend(items)
        
        # If no specific matches, return general results
        if not results:
            results = self.knowledge_base["geral"]
        
        # Add query-specific information
        for result in results:
            result["query"] = query
            result["timestamp"] = datetime.now().isoformat()
        
        return results[:max_results]


class LocalImageGenerationTool:
    """Local image generation tool that returns placeholder images"""
    
    name = "local_image_generation"
    description = "Gera imagens placeholder localmente"
    
    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1
    ) -> Dict[str, Any]:
        """Generate placeholder images"""
        
        if not is_local_mode():
            raise ValueError("LocalImageGenerationTool should only be used in LOCAL mode")
        
        # Create placeholder image data (1x1 transparent PNG)
        placeholder_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        
        images = []
        for i in range(n):
            images.append({
                "url": f"data:image/png;base64,{placeholder_data}",
                "b64_json": placeholder_data,
                "revised_prompt": f"Imagem placeholder para: {prompt}"
            })
        
        return {
            "created": int(datetime.now().timestamp()),
            "data": images
        }


class LocalVectorStore:
    """Local vector store using simple text matching"""
    
    def __init__(self, store_path: str = None):
        self.store_path = store_path or config.VECTOR_STORE_PATH
        self.documents = self._load_documents()
    
    def _load_documents(self) -> List[Dict]:
        """Load documents from local storage"""
        doc_file = os.path.join(self.store_path, "documents.json")
        
        if os.path.exists(doc_file):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading documents: {e}")
        
        return []
    
    def _save_documents(self):
        """Save documents to local storage"""
        os.makedirs(self.store_path, exist_ok=True)
        doc_file = os.path.join(self.store_path, "documents.json")
        
        try:
            with open(doc_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving documents: {e}")
    
    async def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add texts to the vector store"""
        
        ids = []
        for i, text in enumerate(texts):
            doc_id = str(uuid.uuid4())
            document = {
                "id": doc_id,
                "text": text,
                "metadata": metadatas[i] if metadatas and i < len(metadatas) else {},
                "created_at": datetime.now().isoformat()
            }
            self.documents.append(document)
            ids.append(doc_id)
        
        self._save_documents()
        return ids
    
    async def similarity_search(
        self,
        query: str,
        k: int = 4
    ) -> List[Dict[str, Any]]:
        """Search for similar texts using simple text matching"""
        
        query_lower = query.lower()
        scored_docs = []
        
        for doc in self.documents:
            text_lower = doc["text"].lower()
            
            # Simple scoring based on keyword matches
            score = 0
            query_words = query_lower.split()
            
            for word in query_words:
                if word in text_lower:
                    score += 1
            
            if score > 0:
                scored_docs.append((score, doc))
        
        # Sort by score (descending) and return top k
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:k]]


class LocalDataProvider:
    """Local data provider for mock data"""
    
    def __init__(self):
        self.mock_data = {
            "weather": {
                "temperature": "22°C",
                "condition": "Ensolarado",
                "humidity": "65%",
                "location": "Local"
            },
            "news": [
                {
                    "title": "Notícia Local 1",
                    "content": "Conteúdo da primeira notícia local.",
                    "date": datetime.now().isoformat()
                },
                {
                    "title": "Notícia Local 2", 
                    "content": "Conteúdo da segunda notícia local.",
                    "date": datetime.now().isoformat()
                }
            ],
            "stocks": {
                "PETR4": {"price": "R$ 35.50", "change": "+1.2%"},
                "VALE3": {"price": "R$ 65.80", "change": "-0.5%"},
                "ITUB4": {"price": "R$ 28.90", "change": "+0.8%"}
            }
        }
    
    async def get_weather(self, location: str = "Local") -> Dict[str, Any]:
        """Get mock weather data"""
        return self.mock_data["weather"]
    
    async def get_news(self, category: str = "geral") -> List[Dict[str, Any]]:
        """Get mock news data"""
        return self.mock_data["news"]
    
    async def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Get mock stock data"""
        return self.mock_data["stocks"].get(symbol, {
            "price": "N/A",
            "change": "N/A"
        })


# Global instances
local_search_tool = LocalSearchTool()
local_image_tool = LocalImageGenerationTool()
local_vector_store = LocalVectorStore()
local_data_provider = LocalDataProvider()

