# app/rag/validators.py
from typing import Dict, Any

def _dupe_names_in_day(day: Dict[str, Any]) -> list[str]:
    meals = day.get("meals", {})
    names = [str(v).strip().lower() for v in meals.values() if isinstance(v, str)]
    dups = []
    seen = set()
    for n in names:
        if n in seen and n not in dups:
            dups.append(n)
        seen.add(n)
    return dups

def validate_plan(plan_json: Dict[str, Any]) -> None:
    """
    Raises ValueError if any rule is violated.
    Rules:
      - plan.days[*].meals keys are strings
      - No duplicate dish names in the same day
      - All required keys exist
    """
    if "plan" not in plan_json or "days" not in plan_json["plan"]:
        raise ValueError("Missing plan.days")
    days = plan_json["plan"]["days"]
    if not isinstance(days, list) or not days:
        raise ValueError("plan.days must be a non-empty list")

    for day in days:
        if "meals" not in day or "workout" not in day:
            raise ValueError("Each day must include meals and workout")
        meals = day["meals"]
        for slot in ("breakfast", "lunch", "dinner"):
            if slot not in meals or not isinstance(meals[slot], str) or not meals[slot].strip():
                raise ValueError(f"Missing or invalid meals.{slot}")
        dups = _dupe_names_in_day(day)
        if dups:
            raise ValueError(f"Duplicate dish names in {day.get('day')}: {dups}")
