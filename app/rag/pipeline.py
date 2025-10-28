import json, time
from typing import List, Dict, Any
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from app.config import CHROMA_PERSIST_DIR, EMBED_MODEL, CHAT_MODEL, TOP_K, OPENAI_API_KEY

import re
import os, random

RECIPES_JSON = os.path.join(os.path.dirname(__file__), "..", "data", "recipes.json")

def _load_recipes(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _group_by_meal(recipes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = {"breakfast": [], "lunch": [], "dinner": []}
    for r in recipes:
        for m in (r.get("meal") or []):
            if m in groups:
                groups[m].append(r)
    return groups

def select_meal_skeleton(days: int = 3, seed: int | None = None, dietary_restrictions: str | None = None) -> List[Dict[str, Dict[str, Any]]]:
    """Pick meals directly from recipes.json without any diversify module.
    
    Args:
        days: Number of days to plan
        seed: Random seed for reproducible selection
        dietary_restrictions: String containing dietary restrictions (e.g., "vegan", "vegetarian", "gluten-free")
    
    Returns a list of day dicts like:
    [{"breakfast": recipe, "lunch": recipe, "dinner": recipe}, ...]
    """
    rng = random.Random(seed or random.randint(0, 10_000))
    recipes = _load_recipes(RECIPES_JSON)
    
    # Filter recipes based on dietary restrictions
    if dietary_restrictions:
        restrictions_lower = dietary_restrictions.lower()
        filtered_recipes = []
        
        for recipe in recipes:
            recipe_diets = [d.lower() for d in recipe.get("diet", [])]
            
            # Check if recipe matches dietary restrictions
            if "vegan" in restrictions_lower:
                if "vegan" in recipe_diets:
                    filtered_recipes.append(recipe)
            elif "vegetarian" in restrictions_lower:
                if "vegetarian" in recipe_diets or "vegan" in recipe_diets:
                    filtered_recipes.append(recipe)
            elif "gluten-free" in restrictions_lower:
                if "gluten-free" in recipe_diets:
                    filtered_recipes.append(recipe)
            elif "dairy-free" in restrictions_lower:
                if "dairy-free" in recipe_diets:
                    filtered_recipes.append(recipe)
            elif "low-carb" in restrictions_lower:
                if "low-carb" in recipe_diets:
                    filtered_recipes.append(recipe)
            elif "keto" in restrictions_lower:
                if "keto" in recipe_diets:
                    filtered_recipes.append(recipe)
            elif "paleo" in restrictions_lower:
                if "paleo" in recipe_diets:
                    filtered_recipes.append(recipe)
            else:
                # If no specific diet match, include the recipe
                filtered_recipes.append(recipe)
        
        recipes = filtered_recipes if filtered_recipes else recipes  # Fallback to all if no matches
    
    groups = _group_by_meal(recipes)

    # fallback if any bucket is empty
    breakfasts = groups.get("breakfast") or recipes
    lunches = groups.get("lunch") or recipes
    dinners = groups.get("dinner") or recipes

    # avoid duplicates within the plan when possible
    used_names = set()
    out: List[Dict[str, Dict[str, Any]]] = []
    for _ in range(days):
        def pick(bucket: List[Dict[str, Any]]) -> Dict[str, Any]:
            candidates = [r for r in bucket if r.get("name") not in used_names] or bucket
            choice = rng.choice(candidates)
            used_names.add(choice.get("name"))
            return choice

        out.append({
            "breakfast": pick(breakfasts),
            "lunch": pick(lunches),
            "dinner": pick(dinners),
        })
    return out

_SENT_END = re.compile(r'([.!?])\s+')
CASE_TOKENS = (
    "year-old", "case study", "scenario:", "profile:", "pregnan",  # pregnancy/pregnant
    "he ", "she ", "his ", "her ", "their ", "jessica", "ines", "madison"
)

def _clip_to_sentences(text: str, max_chars: int = 900) -> str:
    """Trim leading/trailing partial sentences and cap length."""
    t = (text or "").strip()
    if not t:
        return t
    # Snap start: drop up to first full stop if first sentence seems mid-way
    first_dot = t.find(". ")
    if 0 <= first_dot <= 80:  # early fragment → start after first complete sentence
        t = t[first_dot+2:].lstrip()
    # Snap end: cut at nearest sentence end under max_chars
    if len(t) > max_chars:
        cut = t.rfind(". ", 0, max_chars)
        if cut == -1:
            cut = t.rfind("? ", 0, max_chars)
        if cut == -1:
            cut = t.rfind("! ", 0, max_chars)
        t = (t[: cut+1] if cut != -1 else t[: max_chars]).strip()
    return t

CASE_TOKENS = (
    "year-old", "case study", "scenario:", "example:", "for example",
    "patient", "subject", "participant", "individual", "client",
    "male,", "female,", "he was", "she was", "they were", "his ", "her ",
    "their ", "doctor", "physician", "nurse", "trainer"
)

def _looks_case_study(text: str) -> bool:
    """
    Detects text that looks like an anecdote, profile, or case study.
    """
    low = (text or "").lower()
    # flag snippets that mention a personal narrative or singular subject
    return any(tok in low for tok in CASE_TOKENS)



SYSTEM_PROMPT = (
    "You are LifeSync, an evidence-aware wellness assistant. "
    "Create a structured 3-day plan (meals and workouts) tailored to the goal. "
    "Use only substantive guideline content from the provided retrieval snippets. "
    "Ignore navigation, promotional copy, 'Available at'/'MyPlate' callouts, cookie banners, and footers. "
    "For workouts, provide specific, detailed exercise descriptions (e.g., '30 minutes of strength training focusing on upper body: 3 sets of 10 push-ups, 3 sets of 12 dumbbell rows, 3 sets of 8 shoulder presses'). "
    "Return strict JSON matching the schema with keys: plan.days (array of 3 days with breakfast, lunch, dinner, workout), "
    "plan.tips (array of 2–5 tips), plan.caution (string)."
)

class RagPlanner:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.emb = OpenAIEmbeddings(model=EMBED_MODEL)
        self.vs = Chroma(embedding_function=self.emb, persist_directory=CHROMA_PERSIST_DIR)

    def retrieve(self, query: str, k: int = TOP_K) -> List[Dict[str, Any]]:
        docs = self.vs.max_marginal_relevance_search(
            query, k=k, fetch_k=max(16, k * 4), lambda_mult=0.5
        )
        strong, weak = [], []  # strong = generalizable, weak = case-study-ish
        seen = set()

        for d in docs:
            m = d.metadata or {}
            raw = (d.page_content or "").strip()
            low = raw.lower()

            # Drop boilerplate
            if any(tok in low for tok in (
                "available at", "myplate.gov", "subscribe", "sign up", "privacy policy",
                "newsletter", "back to top"
            )):
                continue

            # Clip to sentence boundaries
            txt = _clip_to_sentences(raw)

            # Dedup by (source, page, head)
            sig = (m.get("source"), m.get("page"), txt[:220].lower())
            if sig in seen or not txt:
                continue
            seen.add(sig)

            item = {"text": txt, "source": m.get("source"), "page": m.get("page")}
            if _looks_case_study(txt):
                weak.append(item)
            else:
                strong.append(item)

        # Prefer generalizable evidence first, then fill with case-studies if needed
        merged = strong + weak
        return merged[:k]

    def summarize_evidence(self, goal: str, snippets: List[Dict[str, Any]]) -> str:
        """Ask the model to generalize case-like snippets into universal guidance with bracket citations."""
        if not snippets:
            return ""
        bullet_context = "\n\n".join(
            f"- {s['text']}\n  [Source: {s.get('source')} p.{s.get('page')}]"
            for s in snippets
        )
        messages = [
            {"role": "system", "content":
                "You are an evidence summarizer. Turn excerpts into concise, universally applicable guidance. "
                "Strip anecdotes/names; keep the general rule. Output 4–8 bullets. "
                "KEEP the bracketed citations exactly as provided at the end of each bullet."
            },
            {"role": "user", "content":
                f"GOAL: {goal}\n\nEXCERPTS WITH CITATIONS:\n{bullet_context}\n\n"
                "Write general guidance bullets (no anecdotes), each ending with the supplied [Source: ...] citation."
            }
        ]
        resp = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.2
        )
        return resp.choices[0].message.content.strip()


    def _to_messages(self, goal: str, retrieved: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        evidence = self.summarize_evidence(goal, retrieved)
        user = (
            f"GOAL: {goal}\n\n"
            "EVIDENCE (generalized, cite-aware bullets):\n"
            f"{evidence}\n\n"
            "Now produce STRICT JSON (we will fill meals programmatically):\n"
            "IMPORTANT: Provide detailed, specific workout descriptions for each day. Include exercise types, duration, sets/reps where applicable, and focus areas.\n"
            "{\n"
            '  "plan": {\n'
            '    "days": [\n'
            '      {"day":"Day 1","meals":{"breakfast":"","lunch":"","dinner":""},"workout":"Specific workout with exercises, duration, and focus"},\n'
            '      {"day":"Day 2","meals":{"breakfast":"","lunch":"","dinner":""},"workout":"Specific workout with exercises, duration, and focus"},\n'
            '      {"day":"Day 3","meals":{"breakfast":"","lunch":"","dinner":""},"workout":"Specific workout with exercises, duration, and focus"}\n'
            "    ],\n"
            '    "tips": ["Specific tip 1","Specific tip 2","Specific tip 3"],\n'
            '    "caution": "Specific cautionary advice"\n'
            "  }\n"
            "}\n"
        )
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ]


    def plan(self, goal: str, profile: Dict[str, Any] = None) -> Dict[str, Any]:
        t0 = time.time()
        retrieved = self.retrieve(goal, k=TOP_K)
        evidence_bullets = self.summarize_evidence(goal, retrieved)
        messages = self._to_messages(goal, retrieved)

        resp = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw_content = resp.choices[0].message.content or "{}"
        try:
            out = json.loads(raw_content)
        except Exception:
            out = {"plan": {"raw": raw_content}}

        # Extract dietary restrictions from profile
        dietary_restrictions = None
        if profile and profile.get("restrictions"):
            dietary_restrictions = profile["restrictions"]
        
        # Fill meals from recipes.json with full details
        picks = select_meal_skeleton(days=3, dietary_restrictions=dietary_restrictions)
        for i, day in enumerate(out.get("plan", {}).get("days", [])):
            if i < len(picks):
                sel = picks[i]
                day_meals = day.get("meals") or {}
                # Include full meal details instead of just names
                day_meals["breakfast"] = sel["breakfast"]
                day_meals["lunch"] = sel["lunch"]
                day_meals["dinner"] = sel["dinner"]
                day["meals"] = day_meals

        latency_ms = int((time.time() - t0) * 1000)
        return {
            "goal": goal,
            **out,
            "retrieved": retrieved,
            "evidence_summary": evidence_bullets,
            "latency_ms": latency_ms,
        }


# Singleton
planner = RagPlanner()
