"""
Seed the ChromaDB vector store with food data.
Called automatically on app startup via main.py lifespan.
Can also be run manually: python -m backend.data.seed
"""

from pathlib import Path

from backend.core.vector_store import get_vector_store

DATA_FILE = Path(__file__).parent / "FoodDataSet.json"


def seed_vector_store():
    if not DATA_FILE.exists():
        print(f"⚠️  FoodDataSet.json not found at {DATA_FILE}")
        print("   Place your FoodDataSet.json in backend/data/ and restart.")
        return 0

    vector_store = get_vector_store()
    count = vector_store.load_and_seed(str(DATA_FILE))
    return count


if __name__ == "__main__":
    count = seed_vector_store()
    print(f"✅ Vector store seeded with {count} food items")
