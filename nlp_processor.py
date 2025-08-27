# nlp_processor.py
import re
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import difflib
from text_preprocessor import text_preprocessor

class Intent(Enum):
    PRODUCT_SELECTION = "подбор_по_проблеме"
    PRODUCT_INQUIRY = "вопрос_по_применению"
    COMPOSITION_INQUIRY = "вопрос_о_составе"
    COMPLAINT = "жалоба"
    GENERAL_QUESTION = "общий_вопрос"
    DOSAGE_INQUIRY = "вопрос_о_дозировке"
    CONTRAINDICATIONS = "вопрос_о_противопоказаниях"
    STORE_LOCATION = "поиск_магазина"
    REGISTRATION = "регистрация"
    PRODUCT_LINK = "запрос_ссылки_на_продукт"
    UNKNOWN = "неизвестно"

@dataclass
class Entity:
    text: str
    label: str
    start: int
    end: int
    confidence: float = 1.0

@dataclass
class ProcessedMessage:
    text: str
    intent: Intent
    entities: List[Entity]
    sentiment: str
    normalized_text: str
    expanded_query: str
    confidence: float

class SynonymManager:
    def __init__(self):
        self.synonyms = {
            "простуда": [
                "ОРВИ", "грипп", "насморк", "кашель", "температура", "простудился", 
                "заболел", "простудные заболевания", "вирусная инфекция", "респираторная инфекция",
                "ангина", "фарингит", "ларингит", "бронхит", "трахеит"
            ],
            "усталость": [
                "нет сил", "вялость", "апатия", "хроническая усталость", "истощение",
                "слабость", "утомляемость", "недомогание", "упадок сил", "переутомление",
                "астения", "быстрая утомляемость", "снижение работоспособности"
            ],
            "иммунитет": [
                "защитные силы", "сопротивляемость", "иммунная система", "защита организма",
                "иммунная защита", "естественная защита", "резистентность", "барьерная функция"
            ],
            "пищеварение": [
                "ЖКТ", "желудочно-кишечный тракт", "пищеварительная система", "желудок",
                "кишечник", "переваривание", "усвоение пищи", "метаболизм", "обмен веществ"
            ],
            "антиоксиданты": [
                "антиоксидантная защита", "свободные радикалы", "окислительный стресс",
                "антиоксидантная система", "защита от окисления"
            ],
            "энергия": [
                "бодрость", "тонус", "активность", "жизненная сила", "работоспособность",
                "выносливость", "энергичность", "витальность"
            ],
            "стресс": [
                "нервное напряжение", "психоэмоциональное напряжение", "нервозность",
                "тревожность", "волнение", "перенапряжение", "психологическая нагрузка"
            ],
            "печень": [
                "для печени", "здоровье печени", "печеночный", "печёночный",
                "гепатопротектор", "гепатопротекторный", "гепато", "гепатит",
                "очистка печени", "поддержка печени"
            ]
        }
        
        # Создаем обратный словарь для быстрого поиска
        self.reverse_synonyms = {}
        for main_word, synonyms_list in self.synonyms.items():
            self.reverse_synonyms[main_word] = main_word
            for synonym in synonyms_list:
                self.reverse_synonyms[synonym.lower()] = main_word

class ProductEntityRecognizer:
    def __init__(self):
        # Загружаем список продуктов из базы знаний
        self.products = self._load_products()
        self.product_patterns = self._create_product_patterns()
    
    def _load_products(self) -> List[str]:
        """Загружает список продуктов из knowledge_base.json"""
        try:
            with open("knowledge_base.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                products = []
                for item in data:
                    # Основное название
                    products.append(item["product"])
                    # Альтернативные названия
                    if "Солберри" in item["product"]:
                        products.extend(["Солберри", "Solberry", "солберри-h", "солберри h"])
                    if "Битерон" in item["product"]:
                        products.extend(["Битерон", "Beeteron", "битерон-h", "битерон h"])
                return products
        except FileNotFoundError:
            return ["Солберри-H", "Битерон-H", "Солберри", "Битерон"]
    
    def _create_product_patterns(self) -> List[Tuple[str, re.Pattern]]:
        """Создает паттерны для поиска продуктов в тексте"""
        patterns = []
        for product in self.products:
            # Создаем гибкий паттерн для каждого продукта
            escaped_product = re.escape(product)
            # Позволяем различные варианты написания
            pattern = escaped_product.replace(r"\-", r"[\-\s]*").replace(r"\ ", r"[\s\-]*")
            patterns.append((product, re.compile(pattern, re.IGNORECASE)))
        return patterns
    
    def find_products(self, text: str) -> List[Entity]:
        """Находит упоминания продуктов в тексте"""
        entities = []
        for product_name, pattern in self.product_patterns:
            for match in pattern.finditer(text):
                entity = Entity(
                    text=match.group(),
                    label="PRODUCT",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9
                )
                entities.append(entity)
        return entities

class IntentClassifier:
    def __init__(self):
        self.intent_patterns = {
            Intent.PRODUCT_SELECTION: [
                r"что.*принимать.*при",
                r"что.*помогает.*от",
                r"посоветуйте.*при",
                r"подберите.*продукт",
                r"подбери.*[а-я]+",
                r"какой.*продукт.*для",
                r"что.*пить.*при",
                r"чем.*лечить",
                r"какие.*средства.*от",
                r"помогите.*выбрать",
                r"рекомендуете.*при",
                r"посоветуй.*что.*от",
                r"посоветуй.*что.*нибудь.*от",
                r"посоветуй.*что.*для",
                r"посоветуй.*[а-я]+",
                r"подскажи.*что.*от",
                r"подскажи.*что.*нибудь.*от",
                r"подскажи.*что.*для",
                r"подскажи.*[а-я]+",
                r"подбери.*[а-я]+",
                r"весь.*[а-я]+",
                r"все.*[а-я]+",
                r"весь.*ассортимент.*[а-я]+",
                r"все.*продукты.*[а-я]+"
                r"что.*есть.*от",
                r"что.*есть.*для",
                r"от.*[а-я]+.*что",
                r"для.*[а-я]+.*что",
                r"что.*лучше.*пить",
                r"что.*лучше.*принимать",
                r"что.*лучше.*употреблять",
                r"что.*рекомендуете.*пить",
                r"что.*посоветуете.*пить",
                r"что.*посоветуете.*принимать",
                r"что.*рекомендуете.*принимать",
                r"подскажи.*что.*лучше.*пить",
                r"посоветуй.*что.*лучше.*пить",
                r"что.*пить.*по.*утрам",
                r"что.*принимать.*по.*утрам",
                r"что.*пить.*утром",
                r"что.*принимать.*утром",
                r"утренние.*напитки",
                r"что.*пить.*на.*завтрак",
                r"что.*принимать.*на.*завтрак",
                r"напитки.*для.*утра",
                r"продукты.*для.*утра",
                r"что.*пить.*для.*энергии",
                r"что.*принимать.*для.*энергии",
                r"что.*пить.*для.*бодрости",
                r"что.*принимать.*для.*бодрости",
                r"посоветуй.*от",
                r"подскажи.*от",
                r"что.*от",
                r"что.*при",
                r"что.*для",
                r"от.*простуды",
                r"от.*гриппа",
                r"от.*кашля",
                r"от.*насморка",
                r"от.*температуры",
                r"от.*ангины",
                r"для.*печени",
                r"для.*иммунитета",
                r"для.*энергии",
                r"для.*бодрости",
                r"для.*здоровья",
                r"при.*простуде",
                r"при.*гриппе",
                r"при.*кашле",
                r"при.*насморке",
                r"при.*температуре",
                r"при.*ангине"
            ],
            Intent.PRODUCT_INQUIRY: [
                r"как.*принимать",
                r"как.*пить",
                r"как.*использовать",
                r"способ.*применения",
                r"инструкция.*по.*применению",
                r"правила.*приема",
                r"схема.*приема",
                r"когда.*принимать",
                r"для.*чего.*применяют.*[а-я]",
                r"зачем.*нужен.*[а-я]",
                r"что.*лечит.*[а-я]",
                r"от.*чего.*помогает.*[а-я]",
                r"показания.*[а-я]",
                r"при.*каких.*заболеваниях.*[а-я]"
            ],
            Intent.COMPOSITION_INQUIRY: [
                r"состав.*продукта",
                r"что.*входит.*в.*состав",
                r"из.*чего.*состоит",
                r"какие.*компоненты",
                r"ингредиенты",
                r"активные.*вещества"
            ],
            Intent.DOSAGE_INQUIRY: [
                r"сколько.*принимать",
                r"какая.*дозировка",
                r"дозы",
                r"количество.*капсул",
                r"по.*сколько.*штук",
                r"норма.*приема"
            ],
            Intent.CONTRAINDICATIONS: [
                r"противопоказания",
                r"можно.*ли.*принимать",
                r"есть.*ли.*ограничения",
                r"побочные.*эффекты",
                r"вредно.*ли",
                r"безопасно.*ли"
            ],
            Intent.COMPLAINT: [
                r"не.*помогает",
                r"не.*действует",
                r"результата.*нет",
                r"бесполезно",
                r"зря.*потратил",
                r"разочарован",
                r"плохой.*продукт",
                r"некачественный"
            ],
            Intent.STORE_LOCATION: [
                r"адрес.*магазина",
                r"точки.*продаж",
                r"где.*продается.*[а-я]+.*в.*городе",
                r"магазины.*в.*городе",
                r"магазины.*в.*[а-я]+",
                r"найти.*в.*продаже.*в.*городе"
            ],
            Intent.REGISTRATION: [
                r"как.*зарегистрироваться",
                r"регистрация.*на.*сайте",
                r"как.*стать.*представителем",
                r"хочу.*зарегистрироваться",
                r"регистрация.*в.*компании",
                r"как.*присоединиться",
                r"стать.*дилером",
                r"стать.*партнером",
                r"регистрация.*аврора",
                r"как.*получить.*скидку",
                r"личный.*кабинет.*регистрация"
            ],
            Intent.PRODUCT_LINK: [
                r"ссылка.*на.*продукт",
                r"ссылка.*на.*[а-я]+",
                r"дай.*ссылку",
                r"дайте.*ссылку",
                r"отправь.*ссылку",
                r"отправьте.*ссылку",
                r"где.*купить.*[а-я]+",
                r"как.*заказать.*[а-я]+",
                r"хочу.*купить.*[а-я]+",
                r"покажи.*[а-я]+",
                r"покажите.*[а-я]+",
                r"фото.*[а-я]+",
                r"картинку.*[а-я]+",
                r"изображение.*[а-я]+",
                r"пришли.*[а-я]+",
                r"пришлите.*[а-я]+",
                r"url.*[а-я]+",
                r"линк.*[а-я]+",
                r"ссылку.*[а-я]+",
                r"нужна.*ссылка",
                r"нужна.*ссылка.*на.*[а-я]+",
                r"пришли.*ссылку.*на.*[а-я]+"
            ]
        }
    
    def classify(self, text: str) -> Tuple[Intent, float]:
        """Классифицирует намерение пользователя"""
        text_lower = text.lower()
        # Быстрые хелперы ТОЛЬКО для коротких фраз (без вопросов о продуктах)
        if re.fullmatch(r"\s*(от|при)\s+\w+\s*", text_lower):
            return Intent.PRODUCT_SELECTION, 0.8
        
        # Дополнительные паттерны для кратких запросов (БЕЗ вопросов о применении)
        short_patterns = [
            r"от\s+\w+$",  # "от простуды", "от гриппа" (только короткие запросы)
            r"при\s+\w+$",  # "при простуде", "при гриппе" (только короткие запросы)
            r"для\s+\w+$",  # "для печени", "для иммунитета" (только короткие запросы)
            r"посоветуй\s+от\s+\w+",  # "посоветуй от простуды"
            r"подскажи\s+от\s+\w+",   # "подскажи от простуды"
            r"что\s+от\s+\w+",        # "что от простуды"
            r"что\s+при\s+\w+",       # "что при простуде"
            r"что\s+для\s+\w+",       # "что для печени"
        ]
        
        for pattern in short_patterns:
            if re.search(pattern, text_lower):
                return Intent.PRODUCT_SELECTION, 0.9
        best_intent = Intent.UNKNOWN
        best_score = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    matches += 1
                    score += 1.0
            
            if matches > 0:
                # Нормализуем оценку
                normalized_score = score / len(patterns)
                if normalized_score > best_score:
                    best_score = normalized_score
                    best_intent = intent
        
        # Если не нашли специфичных паттернов, проверяем на общие вопросы о здоровье
        if best_intent == Intent.UNKNOWN:
            health_patterns = [
                r"что.*лучше.*пить",
                r"что.*лучше.*принимать", 
                r"что.*рекомендуете",
                r"что.*посоветуете",
                r"подскажи.*что",
                r"посоветуй.*что",
                r"что.*пить",
                r"что.*принимать",
                r"какие.*продукты",
                r"какие.*напитки",
                r"что.*для.*здоровья",
                r"что.*для.*иммунитета",
                r"что.*для.*энергии",
                r"что.*для.*бодрости"
            ]
            
            # Паттерны для запросов "все варианты"
            all_options_patterns = [
                r"какой.*еще",
                r"еще.*есть",
                r"помимо.*этого",
                r"что.*еще",
                r"все.*варианты",
                r"все.*продукты",
                r"что.*еще.*есть",
                r"какие.*еще",
                r"другие.*варианты",
                r"еще.*варианты",
                r"полный.*обзор",
                r"весь.*ассортимент"
            ]
            
            # Проверяем на запросы "все варианты"
            for pattern in all_options_patterns:
                if re.search(pattern, text_lower):
                    best_intent = Intent.PRODUCT_SELECTION
                    best_score = 0.9
                    break
            
            for pattern in health_patterns:
                if re.search(pattern, text_lower):
                    best_intent = Intent.PRODUCT_SELECTION
                    best_score = 0.7
                    break
            
            # Если все еще не нашли, считаем общим вопросом
            if best_intent == Intent.UNKNOWN and len(text.strip()) > 10:
                best_intent = Intent.GENERAL_QUESTION
                best_score = 0.5
        
        return best_intent, best_score

class SentimentAnalyzer:
    def __init__(self):
        self.positive_words = [
            "помогает", "хорошо", "отлично", "эффективно", "результат", "улучшение",
            "рекомендую", "довольна", "доволен", "спасибо", "благодарна", "классно",
            "супер", "замечательно", "прекрасно", "работает", "действует"
        ]
        
        self.negative_words = [
            "не помогает", "плохо", "ужасно", "неэффективно", "бесполезно", "зря",
            "разочарован", "разочарована", "не советую", "не рекомендую", "обман",
            "развод", "некачественно", "не действует", "не работает", "пустышка"
        ]
    
    def analyze(self, text: str) -> str:
        """Анализирует тональность сообщения"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        
        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        else:
            return "neutral"

class NLPProcessor:
    def __init__(self):
        self.synonym_manager = SynonymManager()
        self.product_recognizer = ProductEntityRecognizer()
        self.intent_classifier = IntentClassifier()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def normalize_text(self, text: str) -> str:
        """Нормализует текст, заменяя синонимы на основные термины"""
        words = text.lower().split()
        normalized_words = []
        
        for word in words:
            # Убираем знаки препинания
            clean_word = re.sub(r'[^\w\-]', '', word)
            
            # Ищем в словаре синонимов
            if clean_word in self.synonym_manager.reverse_synonyms:
                normalized_words.append(self.synonym_manager.reverse_synonyms[clean_word])
            else:
                normalized_words.append(word)
        
        return " ".join(normalized_words)
    
    def expand_query(self, text: str) -> str:
        """Расширяет запрос синонимами для улучшения поиска"""
        words = text.lower().split()
        expanded_terms = set(words)
        
        for word in words:
            clean_word = re.sub(r'[^\w\-]', '', word)
            
            # Если слово - это основной термин, добавляем его синонимы
            if clean_word in self.synonym_manager.synonyms:
                expanded_terms.update(self.synonym_manager.synonyms[clean_word])
            
            # Если слово - это синоним, добавляем основной термин и другие синонимы
            elif clean_word in self.synonym_manager.reverse_synonyms:
                main_term = self.synonym_manager.reverse_synonyms[clean_word]
                expanded_terms.add(main_term)
                expanded_terms.update(self.synonym_manager.synonyms[main_term])
        
        return " ".join(expanded_terms)
    
    def process_message(self, text: str) -> ProcessedMessage:
        """Полная обработка сообщения пользователя"""
        # Предобработка - очистка и нормализация текста
        cleaned_text = text_preprocessor.clean_text(text)
        
        # Распознаем намерение на очищенном тексте
        intent, intent_confidence = self.intent_classifier.classify(cleaned_text)
        
        # Извлекаем сущности (продукты) из очищенного текста
        entities = self.product_recognizer.find_products(cleaned_text)
        
        # Анализируем тональность на очищенном тексте
        sentiment = self.sentiment_analyzer.analyze(cleaned_text)
        
        # Нормализуем очищенный текст
        normalized_text = self.normalize_text(cleaned_text)
        
        # Расширяем очищенный запрос синонимами 
        expanded_query = self.expand_query(cleaned_text)
        
        return ProcessedMessage(
            text=text,
            intent=intent,
            entities=entities,
            sentiment=sentiment,
            normalized_text=normalized_text,
            expanded_query=expanded_query,
            confidence=intent_confidence
        )

# Создаем глобальный экземпляр процессора
nlp_processor = NLPProcessor()
