# app/rag/diversify.py
import json, os, random
from collections import defaultdict
from typing import List, Dict, Set, Optional, Any

RNG = random.Random()

def load_recipe_catalog(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # normalize: ensure array fields exist
        for r in data:
            for key in ("meal", "protein", "grain", "veg", "fat", "seasonings", "diet"):
                if key in r and not isinstance(r[key], list):
                    r[key] = [r[key]]
        return data

def novelty_penalty(name: str, recent: Set[str]) -> float:
    """Soft penalty if user ate this recently (not a hard block)."""
    return 0.6 if name in recent else 0.0

def cuisine_penalty(cuisine_counts: Dict[str, int], cuisine: str, max_per_day: int) -> float:
    """Optional nudge to avoid repeating the SAME cuisine too much in one day."""
    if max_per_day <= 0:
        return 0.0
    over = max(0, cuisine_counts.get(cuisine, 0) - (max_per_day - 1))
    return over * 0.5

def _supports_meal_type(recipe: Dict[str, Any], meal_type: str) -> bool:
    # recipes may have "meal": ["lunch","dinner"] etc.
    meals = recipe.get("meal", [])
    return meal_type in meals if meals else True

def choose_diverse_meals(
    catalog: List[Dict[str, Any]],
    days: int = 3,
    recent_meals: Optional[List[str]] = None,
    meals_per_day: List[str] = ("breakfast","lunch","dinner"),
    unique_by: str = "name",            # hard-unique per day by dish name
    allow_same_protein: bool = True,    # we allow repeating protein (your new rule)
    allow_same_grain: bool = True,      # we allow repeating grain (your new rule)
    rotate_cuisines: bool = False,      # optional: nudge not to repeat cuisine within a day
    max_same_cuisine_per_day: int = 99, # only used if rotate_cuisines=True
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Returns a list of `days` items. Each item is a dict with keys in `meals_per_day`,
    whose values are the full recipe dict chosen from the catalog.
    Hard constraints:
      - No duplicate dish NAME in the same day.
      - Must match meal slot (if recipe declares "meal" tags).
    Soft constraints:
      - Small penalty for items appearing in recent_meals.
      - Optional cuisine variety per day (if rotate_cuisines True).
    Proteins/grains CAN repeat; we don't penalize them by default.
    """
    if seed is not None:
        RNG.seed(seed)

    recent = set(recent_meals or [])
    chosen_days: List[Dict[str, Any]] = []

    # Pre-bucket by meal type for faster filtering
    by_meal: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in catalog:
        # Recipes can claim multiple meal types; index under each
        meal_tags = r.get("meal", [])
        if not meal_tags:
            for mt in meals_per_day:
                by_meal[mt].append(r)
        else:
            for mt in meal_tags:
                by_meal[mt].append(r)

    for _ in range(days):
        day_plan: Dict[str, Any] = {}
        used_names: Set[str] = set()
        cuisine_counts: Dict[str, int] = defaultdict(int)

        for meal_type in meals_per_day:
            candidates = [r for r in by_meal.get(meal_type, []) if _supports_meal_type(r, meal_type)]
            if not candidates:
                continue

            scored = []
            for r in candidates:
                # Hard filter: unique dish name within a day
                name = r.get("name", "").strip()
                if not name or name in used_names:
                    continue

                score = 0.0
                # Soft novelty penalty across the whole plan history
                score += novelty_penalty(name, recent)

                # Optional cuisine diversity nudge per day
                if rotate_cuisines:
                    c = r.get("cuisine", "general")
                    score += cuisine_penalty(cuisine_counts, c, max_same_cuisine_per_day)

                # Mild randomness to break ties
                score += RNG.uniform(0, 0.25)
                scored.append((score, r))

            if not scored:
                # fallback: pick any unused-name candidate ignoring penalties
                for r in candidates:
                    if r.get("name", "") not in used_names:
                        scored.append((RNG.uniform(0, 0.25), r))
                if not scored:
                    continue

            scored.sort(key=lambda x: x[0])
            pick = scored[0][1]
            day_plan[meal_type] = pick

            # update daily uniqueness + optional cuisine counts
            nm = pick.get("name", "")
            used_names.add(nm)
            cuisine_counts[pick.get("cuisine","general")] += 1

            # update global recent set so same-day later meals prefer different dishes
            recent.add(nm)

        chosen_days.append(day_plan)

    return chosen_days
