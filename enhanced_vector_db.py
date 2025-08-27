# enhanced_vector_db.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import json
import os
import time
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from text_preprocessor import text_preprocessor

# Загружаем переменные
load_dotenv()

@dataclass
class KnowledgeChunk:
    product: str
    chunk_type: str  # benefits, composition, dosage, contraindications, description
    text: str
    metadata: Dict[str, Any]

@dataclass
class SearchResult:
    chunk: KnowledgeChunk
    score: float
    source: str

class ResponseCache:
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.access_count = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[str]:
        if key in self.cache:
            self.access_count[key] = self.access_count.get(key, 0) + 1
            return self.cache[key]
        return None
    
    def set(self, key: str, value: str):
        if len(self.cache) >= self.max_size:
            # Удаляем наименее используемый элемент
            least_used = min(self.access_count.items(), key=lambda x: x[1])
            del self.cache[least_used[0]]
            del self.access_count[least_used[0]]
        
        self.cache[key] = value
        self.access_count[key] = 1
    
    def clear(self):
        self.cache.clear()
        self.access_count.clear()

class EnhancedVectorDB:
    def __init__(self):
        # Подключаемся к Qdrant Cloud
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            https=True
        )
        
        # Модель для эмбеддингов
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # Кэш для ответов
        self.response_cache = ResponseCache()
        
        # Создаём коллекцию (если ещё не создана)
        self.collection_name = "aurora_knowledge_chunks"
        self._init_collection()
        
        # Хэш для отслеживания изменений
        # ВАЖНО: устанавливаем пустой хэш, чтобы первая индексация всегда выполнялась
        self.last_hash = ""
        
    def _init_collection(self):
        """Инициализирует коллекцию в Qdrant"""
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"✅ Коллекция '{self.collection_name}' создана")
            
            # Создаем индекс для поля chunk_type для фильтрации
            try:
                from qdrant_client.models import PayloadSchemaType, CreateFieldIndex
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="chunk_type",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="product",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                print("✅ Индексы для chunk_type и product созданы")
            except Exception as idx_error:
                print(f"⚠️ Не удалось создать индекс: {idx_error}")
                
        except Exception as e:
            print(f"ℹ️ Коллекция '{self.collection_name}' уже существует")
            # Проверяем и создаем индекс для существующей коллекции
            try:
                from qdrant_client.models import PayloadSchemaType, CreateFieldIndex
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="chunk_type", 
                    field_schema=PayloadSchemaType.KEYWORD
                )
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="product", 
                    field_schema=PayloadSchemaType.KEYWORD
                )
                print("✅ Индексы для chunk_type и product добавлены к существующей коллекции")
            except Exception as idx_error:
                print(f"ℹ️ Индекс уже существует или не требуется: {idx_error}")
    
    def _get_file_hash(self) -> str:
        """Получает хэш файлов базы знаний"""
        try:
            main_hash = hashlib.md5(open("knowledge_base.json", "rb").read()).hexdigest()
            new_hash = hashlib.md5(open("knowledge_base_new.json", "rb").read()).hexdigest()
            return hashlib.md5((main_hash + new_hash).encode()).hexdigest()
        except FileNotFoundError:
            return ""
    
    def _load_knowledge(self) -> List[Dict]:
        """Загружает базу знаний из обоих файлов"""
        knowledge_data = []
        
        # Загружаем основную базу знаний
        try:
            with open("knowledge_base.json", "r", encoding="utf-8") as f:
                main_data = json.load(f)
                knowledge_data.extend(main_data)
                print(f"✅ Загружено {len(main_data)} продуктов из knowledge_base.json")
        except FileNotFoundError:
            print("⚠️ Файл knowledge_base.json не найден")
        except Exception as e:
            print(f"❌ Ошибка чтения knowledge_base.json: {e}")
        
        # Загружаем новую базу знаний
        try:
            with open("knowledge_base_new.json", "r", encoding="utf-8") as f:
                new_data = json.load(f)
                knowledge_data.extend(new_data)
                print(f"✅ Загружено {len(new_data)} продуктов из knowledge_base_new.json")
        except FileNotFoundError:
            print("⚠️ Файл knowledge_base_new.json не найден")
        except Exception as e:
            print(f"❌ Ошибка чтения knowledge_base_new.json: {e}")
        
        return knowledge_data
    
    def _create_chunks(self, knowledge_data: List[Dict]) -> List[KnowledgeChunk]:
        """Разбивает данные на смысловые чанки"""
        chunks = []
        
        for item in knowledge_data:
            product = item["product"]
            
            # Чанк с полным описанием продукта (для поиска и ответов)
            if item.get("description"):
                cleaned_description = text_preprocessor.preprocess_knowledge_base_text(item["description"])
                chunks.append(KnowledgeChunk(
                    product=product,
                    chunk_type="description",
                    text=cleaned_description,
                    metadata={
                        "category": item.get("category", ""),
                        "form": item.get("form", ""),
                        "product_id": item.get("id", ""),
                        "use_cases": item.get("benefits", [])[:3],  # Первые 3 случая применения
                        "for_whom": ["взрослые"],  # По умолчанию
                        "source": "knowledge_base.json"
                    }
                ))
            
            # Чанк с кратким описанием (для дополнительного поиска)
            if item.get("short_description"):
                cleaned_short_description = text_preprocessor.preprocess_knowledge_base_text(item["short_description"])
                chunks.append(KnowledgeChunk(
                    product=product,
                    chunk_type="short_description",
                    text=cleaned_short_description,
                    metadata={
                        "category": item.get("category", ""),
                        "form": item.get("form", ""),
                        "product_id": item.get("id", ""),
                        "use_cases": item.get("short_benefits", item.get("benefits", []))[:3],
                        "for_whom": ["взрослые"],
                        "source": "knowledge_base.json"
                    }
                ))
            
            # Чанк с полными показаниями к применению
            if item.get("benefits"):
                benefits_text = "; ".join(item["benefits"])
                cleaned_benefits = text_preprocessor.preprocess_knowledge_base_text(f"Показания к применению: {benefits_text}")
                chunks.append(KnowledgeChunk(
                    product=product,
                    chunk_type="benefits",
                    text=cleaned_benefits,
                    metadata={
                        "category": item.get("category", ""),
                        "use_cases": item["benefits"],
                        "product_id": item.get("id", ""),
                        "for_whom": ["взрослые"],
                        "source": "knowledge_base.json"
                    }
                ))
            
            # Чанк с краткими показаниями (для поиска)
            if item.get("short_benefits"):
                short_benefits_text = "; ".join(item["short_benefits"])
                cleaned_short_benefits = text_preprocessor.preprocess_knowledge_base_text(f"Краткие показания: {short_benefits_text}")
                chunks.append(KnowledgeChunk(
                    product=product,
                    chunk_type="short_benefits",
                    text=cleaned_short_benefits,
                    metadata={
                        "category": item.get("category", ""),
                        "use_cases": item["short_benefits"],
                        "product_id": item.get("id", ""),
                        "for_whom": ["взрослые"],
                        "source": "knowledge_base.json"
                    }
                ))
            
            # Чанк с составом
            if item.get("composition"):
                cleaned_composition = text_preprocessor.preprocess_knowledge_base_text(f"Состав: {item['composition']}")
                chunks.append(KnowledgeChunk(
                    product=product,
                    chunk_type="composition",
                    text=cleaned_composition,
                    metadata={
                        "category": item.get("category", ""),
                        "product_id": item.get("id", ""),
                        "source": "knowledge_base.json"
                    }
                ))
            
            # Чанк с дозировкой
            if item.get("dosage"):
                dosage_text = item["dosage"]
                if item.get("duration"):
                    dosage_text += f", курс {item['duration']}"
                cleaned_dosage = text_preprocessor.preprocess_knowledge_base_text(f"Способ применения: {dosage_text}")
                chunks.append(KnowledgeChunk(
                    product=product,
                    chunk_type="dosage",
                    text=cleaned_dosage,
                    metadata={
                        "category": item.get("category", ""),
                        "product_id": item.get("id", ""),
                        "source": "knowledge_base.json"
                    }
                ))
            
            # Чанк с противопоказаниями
            if item.get("contraindications"):
                chunks.append(KnowledgeChunk(
                    product=product,
                    chunk_type="contraindications",
                    text=f"Противопоказания: {item['contraindications']}",
                    metadata={
                        "category": item.get("category", ""),
                        "product_id": item.get("id", ""),
                        "source": "knowledge_base.json"
                    }
                ))
        
        return chunks
    
    def index_knowledge(self):
        """Индексирует базу знаний в векторной БД"""
        try:
            current_hash = self._get_file_hash()
            if current_hash == self.last_hash and current_hash != "":
                return  # Нет изменений
            
            print("🔄 Обнаружены изменения в базах знаний — обновляем векторную базу...")
            knowledge_data = self._load_knowledge()
            
            if not knowledge_data:
                print("⚠️ База знаний пуста")
                return
            
            chunks = self._create_chunks(knowledge_data)
            points = []
            
            for i, chunk in enumerate(chunks):
                # Создаем текст для векторизации
                full_text = f"{chunk.product}: {chunk.text}"
                vector = self.model.encode(full_text).tolist()
                
                # Создаем уникальный ID
                point_id = f"{chunk.metadata.get('product_id', '')}_{chunk.chunk_type}_{i}"
                point_id_hash = hashlib.md5(point_id.encode()).hexdigest()
                
                # Подготавливаем payload
                payload = {
                    "product": chunk.product,
                    "chunk_type": chunk.chunk_type,
                    "text": chunk.text,
                    "full_text": full_text,
                    **chunk.metadata
                }
                
                points.append(PointStruct(
                    id=point_id_hash,
                    vector=vector,
                    payload=payload
                ))
            
            # Пересоздаем коллекцию с новыми данными
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            
            # Создаем необходимые индексы после пересоздания коллекции
            try:
                from qdrant_client.models import PayloadSchemaType
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="chunk_type",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="product",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                print("✅ Индексы созданы после пересоздания коллекции")
            except Exception as idx_error:
                print(f"⚠️ Ошибка создания индексов: {idx_error}")
            
            # Загружаем точки батчами для больших объемов данных
            batch_size = 50
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upload_points(
                    collection_name=self.collection_name,
                    points=batch
                )
            
            self.last_hash = current_hash
            
            # Очищаем кэш при обновлении базы
            self.response_cache.clear()
            
            print(f"✅ База знаний обновлена: {len(chunks)} чанков из {len(knowledge_data)} продуктов")
            
        except Exception as e:
            print(f"❌ Ошибка при обновлении векторной БД: {e}")
    
    def search(self, query: str, 
               filters: Optional[Dict[str, Any]] = None, 
               limit: int = 3) -> List[SearchResult]:
        """Ищет релевантные чанки в базе знаний"""
        try:
            # Создаем вектор запроса
            query_vector = self.model.encode(query).tolist()
            
            # Подготавливаем фильтры если они есть
            search_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        for v in value:
                            conditions.append(
                                FieldCondition(key=key, match=MatchValue(value=v))
                            )
                    else:
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                
                if conditions:
                    search_filter = Filter(should=conditions)
            
            # Выполняем поиск
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit
            )
            
            # Преобразуем результаты
            search_results = []
            for hit in results:
                chunk = KnowledgeChunk(
                    product=hit.payload["product"],
                    chunk_type=hit.payload["chunk_type"],
                    text=hit.payload["text"],
                    metadata={k: v for k, v in hit.payload.items() 
                             if k not in ["product", "chunk_type", "text", "full_text"]}
                )
                
                search_results.append(SearchResult(
                    chunk=chunk,
                    score=hit.score,
                    source=hit.payload.get("source", "unknown")
                ))
            
            return search_results
            
        except Exception as e:
            print(f"❌ Ошибка при поиске: {e}")
            return []
    
    def search_by_product(self, product_name: str, limit: int = 5) -> List[SearchResult]:
        """Ищет информацию по конкретному продукту"""
        filters = {"product": product_name}
        return self.search("", filters=filters, limit=limit)
    
    def search_by_use_case(self, use_case: str, limit: int = 3) -> List[SearchResult]:
        """Ищет продукты по случаю применения"""
        # Нормализуем запрос для поиска
        normalized_query = text_preprocessor.normalize_for_search(use_case)
        
        # Ищем в чанках benefits и description
        results_benefits = self.search(normalized_query, filters={"chunk_type": "benefits"}, limit=limit)
        results_desc = self.search(normalized_query, filters={"chunk_type": "description"}, limit=limit)
        
        # Объединяем и сортируем по релевантности
        all_results = results_benefits + results_desc
        all_results.sort(key=lambda x: x.score, reverse=True)
        
        return all_results[:limit]
    
    def get_cached_response(self, query: str) -> Optional[str]:
        """Получает закэшированный ответ"""
        # Улучшенная нормализация запроса для кэширования
        normalized_query = self._normalize_query_for_cache(query)
        cache_key = hashlib.md5(normalized_query.encode()).hexdigest()
        return self.response_cache.get(cache_key)
    
    def _normalize_query_for_cache(self, query: str) -> str:
        """Нормализует запрос для более эффективного кэширования"""
        # Приводим к нижнему регистру
        normalized = query.lower().strip()
        
        # Убираем пунктуацию
        import re
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Синонимы для иммунитета
        immunity_synonyms = [
            'для укрепления иммунитета', 'укрепления иммунитета', 'иммунитет', 
            'для иммунитета', 'укрепить иммунитет', 'повысить иммунитет',
            'поддержать иммунитет', 'поддержка иммунитета'
        ]
        
        # Заменяем все синонимы на стандартный термин
        for synonym in immunity_synonyms:
            if synonym in normalized:
                normalized = 'иммунитет'
                break
        
        # Убираем лишние пробелы
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def cache_response(self, query: str, response: str):
        """Кэширует ответ"""
        # Используем ту же нормализацию что и для получения кэша
        normalized_query = self._normalize_query_for_cache(query)
        cache_key = hashlib.md5(normalized_query.encode()).hexdigest()
        self.response_cache.set(cache_key, response)
    
    def start_auto_update(self):
        """Запускает автоматическое обновление базы"""
        def auto_update():
            while True:
                time.sleep(10)  # Проверяем каждые 10 секунд
                try:
                    self.index_knowledge()
                except Exception as e:
                    print(f"Ошибка при автообновлении: {e}")
        
        import threading
        thread = threading.Thread(target=auto_update, daemon=True)
        thread.start()
        print("🔄 Автообновление векторной БД запущено")

# Создаем глобальный экземпляр
enhanced_vector_db = EnhancedVectorDB()
