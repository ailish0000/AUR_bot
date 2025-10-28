"""
Search Service - поиск продуктов с улучшенным fallback
"""
import logging
import requests
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from frontend.config.settings import settings
from frontend.utils.synonyms import expand_query_with_synonyms

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Результат поиска"""
    product: Dict[str, Any]
    score: float
    relevance: str


class SearchService:
    """Сервис для поиска продуктов"""
    
    def __init__(self):
        """Инициализация сервиса поиска"""
        self.backend_url = settings.BACKEND_API_URL
        logger.info(f"Search Service initialized with backend: {self.backend_url}")
    
    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Поиск продуктов с расширением синонимами
        
        Args:
            query: поисковый запрос
            category: категория для фильтрации
            limit: максимальное количество результатов
        
        Returns:
            Список результатов поиска
        """
        logger.info(f"Searching for: {query} (category: {category}, limit: {limit})")
        
        try:
            # Расширяем запрос синонимами
            expanded_query = expand_query_with_synonyms(query)
            if expanded_query != query:
                logger.debug(f"Query expanded with synonyms")
            
            # Пробуем искать через Backend API
            results = await self._search_via_backend(expanded_query, category, limit)
            
            if results:
                logger.info(f"Backend search returned {len(results)} results")
                return results
            
            # Fallback к локальному поиску
            logger.warning("Backend search failed, using local fallback")
            return await self._search_local(expanded_query, limit)
            
        except Exception as e:
            logger.error(f"Error searching products: {e}", exc_info=True)
            # Последний fallback - локальный поиск
            try:
                return await self._search_local(query, limit)
            except:
                return []
    
    async def _search_via_backend(
        self,
        query: str,
        category: Optional[str],
        limit: int
    ) -> List[SearchResult]:
        """Поиск через Backend API"""
        try:
            url = f"{self.backend_url}/api/v1/search/query"
            
            payload = {
                "query": query,
                "category": category,
                "limit": limit
            }
            
            response = requests.post(
                url,
                json=payload,
                timeout=(5, 10)  # (connect timeout, read timeout)
            )
            response.raise_for_status()  # Проверка статуса
            
            data = response.json()
            products = data.get('products', [])
            
            return [
                SearchResult(
                    product=product,
                    score=0.8,  # TODO: получить из API
                    relevance="high"
                )
                for product in products
            ]
                
        except requests.Timeout:
            logger.warning(f"Backend search timeout after 10s, using local fallback")
            return await self._search_local(query, limit)
            
        except requests.ConnectionError:
            logger.warning("Backend unavailable, using local fallback")
            return await self._search_local(query, limit)
            
        except requests.HTTPError as e:
            logger.error(f"Backend HTTP error {e.response.status_code}, using local fallback")
            return await self._search_local(query, limit)
            
        except Exception as e:
            logger.error(f"Unexpected backend error: {e}", exc_info=True)
            return await self._search_local(query, limit)
    
    async def _search_local(
        self,
        query: str,
        limit: int
    ) -> List[SearchResult]:
        """Улучшенный локальный поиск с ранжированием"""
        try:
            # Загружаем базу знаний локально
            with open("knowledge_base.json", "r", encoding="utf-8") as f:
                knowledge_base = json.load(f)
            
            query_terms = query.lower().split()
            results = []
            
            for product in knowledge_base:
                # Поля для поиска
                searchable_fields = {
                    "product": product.get('product', ''),
                    "description": product.get('description', ''),
                    "short_description": product.get('short_description', ''),
                    "category": product.get('category', ''),
                    "benefits": ' '.join(product.get('benefits', [])),
                    "composition": product.get('composition', ''),
                }
                
                # Подсчитываем релевантность
                relevance_score = 0
                
                for field_name, field_text in searchable_fields.items():
                    if not field_text:
                        continue
                    
                    field_text_lower = field_text.lower()
                    
                    # Точное совпадение названия
                    if field_name == "product" and any(term in field_text_lower for term in query_terms):
                        relevance_score += 10
                    
                    # Совпадение в других полях
                    matches = sum(1 for term in query_terms if term in field_text_lower)
                    if matches > 0:
                        if field_name in ["description", "benefits"]:
                            relevance_score += matches * 3
                        else:
                            relevance_score += matches
                
                # Если есть совпадения, добавляем в результаты
                if relevance_score > 0:
                    # Нормализуем score
                    normalized_score = min(0.95, 0.3 + relevance_score * 0.05)
                    
                    results.append(
                        SearchResult(
                            product=product,
                            score=normalized_score,
                            relevance="high" if normalized_score > 0.7 else "medium"
                        )
                    )
            
            # Сортируем по релевантности
            results.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"Local search found {len(results)} products")
            return results[:limit]
            
        except FileNotFoundError:
            logger.error("knowledge_base.json not found")
            return []
        except Exception as e:
            logger.error(f"Local search error: {e}", exc_info=True)
            return []
    
    async def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Получить продукт по ID"""
        try:
            url = f"{self.backend_url}/api/v1/products/{product_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {e}")
            return None
    
    async def get_categories(self) -> List[str]:
        """Получить список категорий"""
        try:
            url = f"{self.backend_url}/api/v1/products/categories/list"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return []
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    async def get_products_by_category(
        self,
        category: str,
        limit: int = 10
    ) -> List[Dict]:
        """Получить продукты по категории"""
        try:
            url = f"{self.backend_url}/api/v1/products/"
            params = {"category": category, "limit": limit}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('products', [])
            return []
            
        except Exception as e:
            logger.error(f"Error getting products by category: {e}")
            return []


# Создаем глобальный экземпляр сервиса
search_service = SearchService()
