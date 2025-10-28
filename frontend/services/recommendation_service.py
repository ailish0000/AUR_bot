"""
Recommendation Service - умные рекомендации продуктов
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """Рекомендация продукта"""
    product: Dict[str, Any]
    reason: str
    confidence: float


class RecommendationService:
    """Сервис умных рекомендаций"""
    
    def __init__(self):
        """Инициализация сервиса рекомендаций"""
        self.health_keywords = self._create_health_keywords()
        logger.info("Recommendation Service initialized")
    
    def _create_health_keywords(self) -> Dict[str, List[str]]:
        """Создание ключевых слов для категорий здоровья"""
        return {
            "immunity": [
                "иммунитет", "защита", "вирус", "простуда", "грипп",
                "противовирусное", "иммунная система", "защитные силы"
            ],
            "digestion": [
                "пищеварение", "желудок", "кишечник", "пробиотик",
                "микрофлора", "дисбактериоз", "метеоризм"
            ],
            "sleep": [
                "сон", "бессонница", "засыпание", "отдых",
                "расслабление", "магний", "успокоительное"
            ],
            "energy": [
                "энергия", "усталость", "тонус", "бодрость",
                "витамины", "силы", "работоспособность"
            ],
            "heart": [
                "сердце", "сосуды", "давление", "кардио",
                "омега", "кровообращение"
            ],
            "joints": [
                "суставы", "хрящи", "коллаген", "боль в суставах",
                "артрит", "артроз", "подвижность"
            ],
            "skin": [
                "кожа", "волосы", "ногти", "коллаген",
                "красота", "молодость", "упругость"
            ],
            "liver": [
                "печень", "детокс", "очищение", "гепа",
                "желчь", "токсины"
            ],
            "stress": [
                "стресс", "нервы", "тревога", "беспокойство",
                "успокоение", "магний", "адаптогены"
            ]
        }
    
    async def get_recommendations(
        self,
        query: str,
        products: List[Dict],
        limit: int = 3
    ) -> List[Recommendation]:
        """
        Получить рекомендации на основе запроса
        
        Args:
            query: запрос пользователя
            products: список доступных продуктов
            limit: максимальное количество рекомендаций
        
        Returns:
            Список рекомендаций
        """
        logger.info(f"Getting recommendations for query: {query[:50]}...")
        
        try:
            # Определяем категорию здоровья
            health_category = self._detect_health_category(query)
            
            # Получаем релевантные продукты
            recommendations = []
            
            for product in products[:limit]:
                reason = self._generate_reason(product, health_category)
                confidence = self._calculate_confidence(product, query)
                
                recommendations.append(
                    Recommendation(
                        product=product,
                        reason=reason,
                        confidence=confidence
                    )
                )
            
            # Сортируем по уверенности
            recommendations.sort(key=lambda x: x.confidence, reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}", exc_info=True)
            return []
    
    def _detect_health_category(self, query: str) -> str:
        """Определение категории здоровья по запросу"""
        query_lower = query.lower()
        
        for category, keywords in self.health_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return category
        
        return "general"
    
    def _generate_reason(self, product: Dict, category: str) -> str:
        """Генерация причины рекомендации"""
        reasons = {
            "immunity": "Укрепляет иммунитет и защищает от вирусов",
            "digestion": "Поддерживает здоровое пищеварение",
            "sleep": "Улучшает качество сна",
            "energy": "Повышает энергию и работоспособность",
            "heart": "Поддерживает здоровье сердца и сосудов",
            "joints": "Укрепляет суставы и хрящи",
            "skin": "Улучшает состояние кожи, волос и ногтей",
            "liver": "Поддерживает функцию печени",
            "stress": "Помогает справиться со стрессом",
            "general": "Рекомендуется на основе вашего запроса"
        }
        
        return reasons.get(category, reasons["general"])
    
    def _calculate_confidence(self, product: Dict, query: str) -> float:
        """Расчет уверенности в рекомендации"""
        query_lower = query.lower()
        score = 0.5  # Базовая уверенность
        
        # Проверяем совпадения в названии
        name = product.get('product', '').lower()
        if any(word in name for word in query_lower.split()):
            score += 0.3
        
        # Проверяем совпадения в описании
        description = product.get('description', '').lower()
        if any(word in description for word in query_lower.split()):
            score += 0.2
        
        return min(score, 1.0)
    
    async def get_complementary_products(
        self,
        product_id: str,
        limit: int = 3
    ) -> List[Recommendation]:
        """Получить дополняющие продукты"""
        # TODO: реализовать логику дополняющих продуктов
        logger.info(f"Getting complementary products for {product_id}")
        return []


# Создаем глобальный экземпляр сервиса
recommendation_service = RecommendationService()
