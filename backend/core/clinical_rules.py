"""
Clinical nutrition rules for condition-aware food re-ranking.

Each condition defines:
  - boost_keywords: ingredients/features that make a food BETTER for this condition
  - penalty_keywords: ingredients/features that make a food WORSE
  - avoid_keywords: hard disqualifiers (food removed from results entirely)
  - calorie_cap: recommended max calories per meal (None = no cap)
  - notes: shown to the user in the response

Sources: ADA (diabetes), AHA (hypertension), NKF (kidney disease),
         PCOS Nutrition Center, Celiac Disease Foundation.
"""

from typing import Optional, TypedDict


class ConditionRule(TypedDict):
    boost_keyword: list[str]
    penalty_keywords: list[str]
    avoid_keywords: list[str]
    calorie_cap: Optional[int]
    boost_score: float
    penalty_score: float
    notes: str


CLINICAL_RULES: dict[str, ConditionRule] = {
    "diabetes_type2": {
        "boost_keywords": [
            "whole grain",
            "fibre",
            "fiber",
            "legume",
            "lentil",
            "bean",
            "vegetable",
            "leafy green",
            "spinach",
            "broccoli",
            "cauliflower",
            "nuts",
            "seeds",
            "olive oil",
            "salmon",
            "avocado",
            "low glycemic",
            "low sugar",
            "unsweetened",
            "baked",
            "steamed",
        ],
        "penalty_keywords": [
            "white rice",
            "white bread",
            "refined",
            "processed",
            "fried",
            "deep fried",
            "sugary",
            "syrup",
            "honey",
            "high calorie",
            "creamy sauce",
        ],
        "avoid_keywords": [
            "candy",
            "soda",
            "sugar-coated",
            "sweetened",
            "donut",
            "cake",
            "pastry",
            "milkshake",
        ],
        "calorie_cap": 450,
        "boost_score": 0.08,
        "penalty_score": 0.10,
        "notes": (
            "Prioritizing low-glycemic, high-fibre options to help maintain "
            "stable blood sugar levels."
        ),
    },
    "hypertension": {
        "boost_keywords": [
            "low sodium",
            "unsalted",
            "fresh",
            "steamed",
            "grilled",
            "banana",
            "potassium",
            "leafy green",
            "beet",
            "berries",
            "oat",
            "omega-3",
            "salmon",
            "sardine",
            "olive oil",
            "garlic",
            "lemon",
            "herbs",
        ],
        "penalty_keywords": [
            "salty",
            "pickled",
            "cured",
            "smoked",
            "processed meat",
            "canned",
            "soy sauce",
            "high sodium",
            "cheese sauce",
            "bacon",
            "sausage",
        ],
        "avoid_keywords": [
            "salt-heavy",
            "heavily salted",
            "preserved",
            "brine",
        ],
        "calorie_cap": 500,
        "boost_score": 0.07,
        "penalty_score": 0.09,
        "notes": (
            "Prioritizing low-sodium, potassium-rich foods to support "
            "healthy blood pressure."
        ),
    },
    "chronic_kidney_disease": {
        "boost_keywords": [
            "low potassium",
            "low phosphorus",
            "white rice",
            "pasta",
            "apple",
            "berry",
            "cabbage",
            "cauliflower",
            "egg white",
            "lean protein",
            "low sodium",
        ],
        "penalty_keywords": [
            "banana",
            "orange",
            "potato",
            "tomato",
            "dairy",
            "milk",
            "cheese",
            "yogurt",
            "whole grain",
            "nuts",
            "seeds",
            "chocolate",
            "dark green",
        ],
        "avoid_keywords": [
            "high potassium",
            "high phosphorus",
            "kidney-stressing",
        ],
        "calorie_cap": 400,
        "boost_score": 0.09,
        "penalty_score": 0.12,
        "notes": (
            "Prioritizing kidney-friendly, low-potassium and low-phosphorus "
            "options as recommended for CKD management."
        ),
    },
    "pcos": {
        "boost_keywords": [
            "anti-inflammatory",
            "omega-3",
            "salmon",
            "turmeric",
            "ginger",
            "leafy green",
            "fibre",
            "fiber",
            "whole grain",
            "legume",
            "lentil",
            "berries",
            "low glycemic",
            "olive oil",
            "nuts",
            "seeds",
            "lean protein",
            "chicken",
            "tofu",
        ],
        "penalty_keywords": [
            "processed",
            "refined sugar",
            "white bread",
            "fried",
            "trans fat",
            "high glycemic",
            "red meat",
            "dairy",
        ],
        "avoid_keywords": [
            "heavily processed",
            "artificial sweetener",
        ],
        "calorie_cap": 450,
        "boost_score": 0.07,
        "penalty_score": 0.08,
        "notes": (
            "Recommending anti-inflammatory, low-glycemic foods that support "
            "hormone balance for PCOS."
        ),
    },
    "celiac": {
        "boost_keywords": [
            "gluten-free",
            "rice",
            "corn",
            "quinoa",
            "potato",
            "naturally gluten free",
            "certified gf",
        ],
        "penalty_keywords": [
            "wheat",
            "barley",
            "rye",
            "malt",
            "soy sauce",
            "breadcrumbs",
            "flour",
            "pasta",
            "bread",
        ],
        "avoid_keywords": [
            "contains gluten",
            "wheat-based",
            "barley-based",
        ],
        "calorie_cap": None,
        "boost_score": 0.10,
        "penalty_score": 0.15,
        "notes": ("Filtering for gluten-free options safe for celiac disease."),
    },
    "lactose_intolerant": {
        "boost_keywords": [
            "dairy-free",
            "plant-based",
            "almond milk",
            "oat milk",
            "coconut milk",
            "vegan",
            "lactose-free",
        ],
        "penalty_keywords": [
            "milk",
            "cheese",
            "cream",
            "butter",
            "yogurt",
            "whey",
            "casein",
            "dairy",
        ],
        "avoid_keywords": [
            "contains dairy",
            "made with milk",
        ],
        "calorie_cap": None,
        "boost_score": 0.08,
        "penalty_score": 0.12,
        "notes": ("Highlighting dairy-free options suitable for lactose intolerance."),
    },
    "heart_disease": {
        "boost_keywords": [
            "omega-3",
            "salmon",
            "sardine",
            "olive oil",
            "avocado",
            "whole grain",
            "fibre",
            "oat",
            "nuts",
            "legume",
            "steamed",
            "grilled",
            "baked",
            "leafy green",
            "berries",
            "low cholesterol",
        ],
        "penalty_keywords": [
            "saturated fat",
            "trans fat",
            "fried",
            "deep fried",
            "red meat",
            "processed meat",
            "high sodium",
            "butter",
            "cream",
            "full fat",
        ],
        "avoid_keywords": [
            "trans fat",
            "hydrogenated",
        ],
        "calorie_cap": 450,
        "boost_score": 0.08,
        "penalty_score": 0.10,
        "notes": (
            "Prioritizing heart-healthy options low in saturated fat and sodium, "
            "rich in omega-3 and fibre."
        ),
    },
    "obesity": {
        "boost_keywords": [
            "low calorie",
            "high protein",
            "high fibre",
            "fiber",
            "salad",
            "vegetable",
            "steamed",
            "grilled",
            "lean",
            "portion-controlled",
            "light",
            "filling",
        ],
        "penalty_keywords": [
            "deep fried",
            "high calorie",
            "creamy",
            "butter",
            "large portion",
            "sugary",
            "dessert",
            "processed",
        ],
        "avoid_keywords": [
            "super-sized",
            "extra large",
        ],
        "calorie_cap": 400,
        "boost_score": 0.06,
        "penalty_score": 0.10,
        "notes": (
            "Recommending high-satiety, lower-calorie options to support "
            "healthy weight management."
        ),
    },
}


def get_rule(condition: str) -> Optional[ConditionRule]:
    """Return the clinical rule for a condition, or None if unsupported"""
    return CLINICAL_RULES.get(condition)


def get_all_conditions() -> list[str]:
    return list(CLINICAL_RULES.keys())
