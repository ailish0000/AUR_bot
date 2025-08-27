# vector_db.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import json
import os
import time
import hashlib
from dotenv import load_dotenv

# Загружаем переменные
load_dotenv()

# Подключаемся к Qdrant Cloud
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    https=True
)

# Модель для эмбеддингов
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Создаём коллекцию (если ещё не создана)
try:
    client.create_collection(
        collection_name="aurora_knowledge",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    print("✅ Коллекция 'aurora_knowledge' создана")
except:
    print("ℹ️ Коллекция уже существует")

# Хэш для отслеживания изменений
def get_file_hash():
    return hashlib.md5(open("knowledge_base.json", "rb").read()).hexdigest()

last_hash = get_file_hash()

def load_knowledge():
    with open("knowledge_base.json", "r", encoding="utf-8") as f:
        return json.load(f)

def index_knowledge():
    global last_hash
    try:
        current_hash = get_file_hash()
        if current_hash == last_hash:
            return  # Нет изменений

        print("🔄 Обнаружены изменения в knowledge_base.json — обновляем базу...")
        knowledge = load_knowledge()
        points = []

        for item in knowledge:
            text = (
                f"Продукт: {item['product']}\n"
                f"Описание: {item['description']}\n"
                f"Польза: {', '.join(item['benefits'])}\n"
                f"Состав: {item['composition']}\n"
                f"Рекомендации: {item['dosage']}\n"
                f"Противопоказания: {item['contraindications']}"
            )
            vector = model.encode(text).tolist()
            point_id = hashlib.md5(item['id'].encode()).hexdigest()

            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=item
                )
            )

        # Удаляем старые точки и добавляем новые
        client.recreate_collection(
            collection_name="aurora_knowledge",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        client.upload_points(collection_name="aurora_knowledge", points=points)
        last_hash = current_hash

        print(f"✅ База знаний обновлена: {len(points)} продуктов")
    except Exception as e:
        print(f"❌ Ошибка при обновлении Qdrant: {e}")

# Автообновление
def start_auto_update():
    def auto_update():
        while True:
            time.sleep(10)
            try:
                index_knowledge()
            except Exception as e:
                print(f"Ошибка при автообновлении: {e}")
    import threading
    thread = threading.Thread(target=auto_update, daemon=True)
    thread.start()