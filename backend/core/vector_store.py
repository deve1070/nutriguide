import json
from typing import Dict, List, Optional
import chromadb
from chromadb.utils import embedding_functions
from backend.config import get_settings

settings = get_settings()


class VectorStore:
    """
    Manages the ChromaDB vector store for food similarity search.
    Uses sentence-transformers for local embeddings (no API cost).
    """

    COLLECTION_NAME = "nutriguide_foods"

    def __init__(self):
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_path)
        self._ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self._collection = None

    def get_collection(self):
        """Get or create the food collection"""
        if self._collection is None:
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
                embedding_function=self._ef,
            )
        return self._collection

    def is_populated(self) -> bool:
        """Check if the collection already has data"""
        return self.get_collection().count() > 0

    def load_and_seed(self, file_path: str) -> int:
        """
        Load food data from JSON and seed the vector store.
        Safe to call multiple times — skips if already populated.
        """
        if self.is_populated():
            count = self.get_collection().count()
            print(f"✅ Vector store already seeded with {count} items")
            return count

        with open(file_path, "r", encoding="utf-8") as f:
            food_data: List[Dict] = json.load(f)

        self._normalize(food_data)
        self._insert(food_data)
        print(f"✅ Seeded vector store with {len(food_data)} food items")
        return len(food_data)

    def similarity_search(
        self,
        query: str,
        n_results: int = 5,
        cuisine_filter: Optional[str] = None,
        max_calories: Optional[int] = None,
    ) -> List[Dict]:
        """
        Semantic similarity search with optional metadata filters.
        """
        where = self._build_where(cuisine_filter, max_calories)

        try:
            results = self.get_collection().query(
                query_texts=[query],
                n_results=n_results,
                where=where,
            )
        except Exception as e:
            print(f"❌ Vector search error: {e}")
            return []

        if not results or not results["ids"] or not results["ids"][0]:
            return []

        formatted = []
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            formatted.append({
                "food_id": results["ids"][0][i],
                "food_name": meta["name"],
                "food_description": meta["description"],
                "cuisine_type": meta["cuisine_type"],
                "food_calories_per_serving": meta["calories"],
                "food_ingredients": meta.get("ingredients", ""),
                "food_health_benefits": meta.get("health_benefits", ""),
                "cooking_method": meta.get("cooking_method", ""),
                "taste_profile": meta.get("taste_profile", ""),
                "similarity_score": round(1 - results["distances"][0][i], 4),
            })
        return formatted

    def _normalize(self, food_data: List[Dict]):
        for i, item in enumerate(food_data):
            item["food_id"] = str(item.get("food_id", i + 1))
            item.setdefault("food_ingredients", [])
            item.setdefault("food_description", "")
            item.setdefault("cuisine_type", "Unknown")
            item.setdefault("food_calories_per_serving", 0)
            item.setdefault("cooking_method", "")
            item.setdefault("food_health_benefits", "")
            features = item.get("food_features", {})
            if isinstance(features, dict):
                item["taste_profile"] = ", ".join(
                    str(v) for v in features.values() if v
                )
            else:
                item["taste_profile"] = ""

    def _insert(self, food_data: List[Dict]):
        documents, metadatas, ids = [], [], []
        used_ids = set()

        for i, food in enumerate(food_data):
            text = (
                f"Name: {food['food_name']}. "
                f"Description: {food.get('food_description', '')}. "
                f"Ingredients: {', '.join(food.get('food_ingredients', []))}. "
                f"Cuisine: {food.get('cuisine_type', 'Unknown')}. "
                f"Cooking method: {food.get('cooking_method', '')}. "
                f"Taste and features: {food.get('taste_profile', '')}. "
                f"Health benefits: {food.get('food_health_benefits', '')}. "
            )

            if "food_nutritional_factors" in food:
                nutrition = food["food_nutritional_factors"]
                if isinstance(nutrition, dict):
                    nutrition_text = ", ".join(f"{k}: {v}" for k, v in nutrition.items())
                    text += f"Nutrition: {nutrition_text}."

            uid = str(food.get("food_id", i))
            counter = 1
            while uid in used_ids:
                uid = f"{food.get('food_id', i)}_{counter}"
                counter += 1
            used_ids.add(uid)

            documents.append(text)
            ids.append(uid)
            metadatas.append({
                "name": food["food_name"],
                "cuisine_type": food.get("cuisine_type", "Unknown"),
                "ingredients": ", ".join(food.get("food_ingredients", [])),
                "calories": food.get("food_calories_per_serving", 0),
                "description": food.get("food_description", ""),
                "cooking_method": food.get("cooking_method", ""),
                "health_benefits": food.get("food_health_benefits", ""),
                "taste_profile": food.get("taste_profile", ""),
            })

        self.get_collection().add(documents=documents, metadatas=metadatas, ids=ids)

    def _build_where(self, cuisine_filter, max_calories):
        filters = []
        if cuisine_filter:
            filters.append({"cuisine_type": cuisine_filter})
        if max_calories:
            filters.append({"calories": {"$lte": max_calories}})
        if len(filters) == 0:
            return None
        if len(filters) == 1:
            return filters[0]
        return {"$and": filters}


_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
