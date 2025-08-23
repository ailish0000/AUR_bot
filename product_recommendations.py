# product_recommendations.py
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enhanced_vector_db import enhanced_vector_db, SearchResult

@dataclass
class ProductRecommendation:
    product_id: str
    product_name: str
    url: str
    image_id: str
    description: str
    benefits: str
    dosage: str
    reason: str  # Почему этот продукт подходит

class RecommendationManager:
    def __init__(self):
        self.products_data = self._load_products_data()
    
    def _load_products_data(self) -> Dict[str, Dict[str, Any]]:
        """Загружает данные продуктов из knowledge_base.json"""
        try:
            with open("knowledge_base.json", "r", encoding="utf-8") as f:
                products = json.load(f)
            
            products_dict = {}
            for product in products:
                products_dict[product["id"]] = product
            
            return products_dict
        except Exception as e:
            print(f"Ошибка загрузки базы продуктов: {e}")
            return {}
    
    def get_recommendations(self, query: str, limit: int = 3) -> List[ProductRecommendation]:
        """Получает рекомендации продуктов на основе запроса"""
        
        # Ищем релевантные продукты в векторной базе
        search_results = enhanced_vector_db.search_by_use_case(query, limit=limit * 2)
        
        # Группируем результаты по продуктам
        products_relevance = {}
        
        for result in search_results:
            product_name = result.chunk.product
            if product_name not in products_relevance:
                products_relevance[product_name] = {
                    "max_score": result.score,
                    "benefits_chunks": [],
                    "description_chunks": []
                }
            
            if result.chunk.chunk_type == "benefits":
                products_relevance[product_name]["benefits_chunks"].append(result)
            elif result.chunk.chunk_type == "description":
                products_relevance[product_name]["description_chunks"].append(result)
            
            # Обновляем максимальный score
            if result.score > products_relevance[product_name]["max_score"]:
                products_relevance[product_name]["max_score"] = result.score
        
        # Создаем рекомендации
        recommendations = []
        
        for product_name, data in products_relevance.items():
            # Находим ID продукта в базе
            product_id = None
            product_data = None
            
            for pid, pdata in self.products_data.items():
                if pdata["product"] == product_name:
                    product_id = pid
                    product_data = pdata
                    break
            
            if not product_data:
                continue
            
            # Формируем краткое описание пользы для карточки
            short_benefits = product_data.get("short_benefits", product_data.get("benefits", []))
            benefits_text = "; ".join(short_benefits[:3])  # Берем только первые 3 пункта
            
            # Формируем причину рекомендации
            reason = self._generate_reason(data["benefits_chunks"], query)
            
            recommendation = ProductRecommendation(
                product_id=product_id,
                product_name=product_name,
                url=product_data.get("url", ""),
                image_id=product_data.get("image_id", ""),
                description=product_data.get("short_description", product_data.get("description", "")),
                benefits=benefits_text,
                dosage=f"{product_data.get('dosage', '')} в течение {product_data.get('duration', '30 дней')}",
                reason=reason
            )
            
            recommendations.append(recommendation)
        
        # Сортируем по релевантности
        recommendations.sort(key=lambda x: products_relevance[x.product_name]["max_score"], reverse=True)
        
        return recommendations[:limit]
    
    def _generate_reason(self, benefits_chunks: List[SearchResult], query: str) -> str:
        """Генерирует причину, почему продукт подходит"""
        if not benefits_chunks:
            return "Подходит для вашего запроса"
        
        # Берем наиболее релевантный чанк
        best_chunk = max(benefits_chunks, key=lambda x: x.score)
        benefits_text = best_chunk.chunk.text.replace("Показания к применению: ", "")
        
        # Ищем ключевые слова из запроса в показаниях
        query_words = query.lower().split()
        matching_benefits = []
        
        for benefit in benefits_text.split(";"):
            benefit = benefit.strip()
            if any(word in benefit.lower() for word in query_words if len(word) > 3):
                matching_benefits.append(benefit)
        
        if matching_benefits:
            return f"Эффективен {matching_benefits[0]}"
        else:
            # Берем первое показание
            first_benefit = benefits_text.split(";")[0].strip()
            return f"Рекомендован {first_benefit}"
    
    def format_recommendation_message(self, recommendation: ProductRecommendation, 
                                    current: int, total: int) -> Tuple[str, str]:
        """Форматирует сообщение с рекомендацией"""
        
        message = f"💊 {recommendation.product_name}\n\n"
        
        # Причина рекомендации
        message += f"🎯 Почему подходит: {recommendation.reason}\n\n"
        
        # Описание продукта
        message += f"📋 Описание:\n{recommendation.description}\n\n"
        
        # Способ применения
        message += f"📏 Применение: {recommendation.dosage}\n\n"
        
        # Счетчик
        if total > 1:
            message += f"📊 Рекомендация {current} из {total}"
        
        return message, recommendation.image_id
    
    def create_recommendation_keyboard(self, user_id: int, current: int, 
                                     total: int, product_url: str):
        """Создает клавиатуру для рекомендации"""
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        buttons = []
        
        # Кнопка подробнее
        if product_url:
            buttons.append([InlineKeyboardButton(
                text="📋 Подробнее на сайте", 
                url=product_url
            )])
        
        # Навигация между рекомендациями
        nav_buttons = []
        if current > 1:
            nav_buttons.append(InlineKeyboardButton(
                text="◀️ Предыдущий", 
                callback_data=f"rec_prev_{user_id}_{current-1}"
            ))
        
        if current < total:
            nav_buttons.append(InlineKeyboardButton(
                text="Дальше ▶️", 
                callback_data=f"rec_next_{user_id}_{current+1}"
            ))
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        # Дополнительные кнопки
        buttons.append([
            InlineKeyboardButton(
                text="📋 Главное меню", 
                callback_data="back_to_main"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)

# Создаем глобальный экземпляр
recommendation_manager = RecommendationManager()
