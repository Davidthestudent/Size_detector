import time
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
import main
import webcolors
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Dict, Optional, List, Literal, Any
from database import upsert_user, list_users, delete_user, get_user_by_public_id
from datetime import date

app = FastAPI()


# ---------------- Models ----------------
class SizeInput(BaseModel):
    values: Dict[str, float]  # e.g. {"bust": 92, "waist": 76, "hips": 98}
    unit_system: Literal["EU", "US"] = "EU"  # what units the user entered (EU=cm, US=in)


class UserIn(BaseModel):
    name: str
    email: EmailStr
    height: int | None = None
    weight: float | None = None
    gender: str | None = None
    birthdate: date | None = None


class SizeDetectionRequest(BaseModel):
    link: HttpUrl | str
    size_type: Literal["EU", "US"] = "EU"
    brand: Optional[str] = None


class SizeDetectionResponse(BaseModel):
    token: str
    unit_system: Literal["EU", "US"]
    needed_measurements: List[str]
    short_instructions: List[str]


class GetParamsRequest(BaseModel):
    token: str
    unit_system: Literal["EU", "US"]
    values: Dict[str, float]


class BestSizeResponse(BaseModel):
    best_size: Any
    echo: Dict[str, float]
    unit_system: Literal["EU", "US"]


@app.post('/users')
def create_or_update_user(body: UserIn):
    return upsert_user(name=body.name,
                       email=body.email,
                       height=body.height,
                       weight=body.weight,
                       gender=body.gender,
                       date_of_birth=body.birthdate)


@app.post('/get_image_and_description')
async def get_image_and_description(client_id: str = Form(),
                                    height: int = Form(),
                                    weight: float = Form(),
                                    gender: str = Form(),
                                    file: UploadFile = File(...)):
    if not file or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='File type not supported')

    data = get_user_by_public_id(client_id)
    if not data:
        raise HTTPException(status_code=404, detail='Client not found. Call /get_info first.')

    raw = await file.read()
    caption = main.image_description(raw)

    type_fig = main.calculate_type_fig(
        caption, height, weight, gender
    )
    return {"caption": caption, "Type_fig": read_advice(type_fig)}


# --------Help_functions--------
def hex_to_color(hex: str):
    try:
        return webcolors.hex_to_name(hex)
    except ValueError:
        return hex


def read_advice(d):
    body = "".join(d.get("body_type", []))
    vibes = ", ".join(d.get("style_vibes", []))
    clothes = "\n".join(f"• {x}" for x in d.get("recommended_clothes", []))
    combos = "\n".join(f"{i}) " + " + ".join(c) for i, c in enumerate(d.get("combinations", []), 1))
    palettes = "\n".join(f"{i}) " + " / ".join(p) for i, p in enumerate(d.get("color_palette", []), 1))
    return (
        f"👉 Figure type:\n{body}\n\n"
        f"✨ Vibes & inspirations: {vibes}\n\n"
        f"🛍️ Recommended clothes:\n{clothes}\n\n"
        f"🎯 Ready-to-wear combos:\n{combos}\n\n"
        f"🎨 Color palettes (HEX):\n{palettes}"
    )


def _convert_units(vals: Dict[str, float], from_sys: str, to_sys: str) -> Dict[str, float]:
    if from_sys == to_sys:
        return vals
    if from_sys == "US" and to_sys == "EU":  # inches -> cm
        return {k: v * 2.54 for k, v in vals.items()}
    if from_sys == "EU" and to_sys == "US":  # cm -> inches
        return {k: v / 2.54 for k, v in vals.items()}
    return vals


TTL_SECONDS = 3600
_STORE: Dict[str, Dict[str, Any]] = {}  # token -> {"plan": ..., "expires_at": ...}


def _now() -> float:
    return time.time()


def _save_plan(plan: Dict[str, Any]) -> str:
    token = uuid.uuid4().hex
    _STORE[token] = {"plan": plan, "expires_at": _now() + TTL_SECONDS}
    return token


def _load_plan(token: str) -> Dict[str, Any]:
    item = _STORE.get(token)
    if not item:
        raise HTTPException(status_code=404, detail="Token not found or expired")
    if item["expires_at"] < _now():
        _STORE.pop(token, None)
        raise HTTPException(status_code=410, detail="Token expired")
    return item["plan"]


def _norm_key(s: str) -> str:
    return s.strip().lower().replace(" ", "_")


def _get_any(d: Dict[str, Any], *candidates: str, default=None):
    """Достать поле по любому из возможных ключей (учёт регистров/вариаций)."""
    keys = list(d.keys())
    mapping = {_norm_key(k): k for k in keys}
    for cand in candidates:
        k = mapping.get(_norm_key(cand))
        if k in d:
            return d[k]
    return default


def _normalize_plan(ai_res: Dict[str, Any], unit_system: Literal["EU", "US"]) -> Dict[str, Any]:
    """
    Приводим результат LLM к канонической схеме:
    {
      "needed_measurements": [str, ...],
      "short_instructions": [str, ...],
      "size_table": {...},     # канон. ед.: US->in, EU->cm
      "unit_system": "EU"|"US"
    }
    """
    needed = _get_any(ai_res, "needed_measurements", "Needed_measurements", "measures_needed", default=[])
    instr = _get_any(ai_res, "short_instructions", "Short_instructions", default=[])
    table = _get_any(ai_res, "size_table", "Size_table", default=None)

    if not isinstance(needed, list) or not needed:
        raise HTTPException(500, "Model did not return 'needed_measurements' list")
    if table is None or not isinstance(table, dict):
        raise HTTPException(500, "Model did not return 'size_table' object")

    # Нормализуем имена мерок
    needed = [_norm_key(x) for x in needed]
    # Обрезаем инструкции до той же длины (если пришло больше/меньше)
    if isinstance(instr, list):
        instr = [str(x) for x in instr][:len(needed)]
        while len(instr) < len(needed):
            instr.append("")
    else:
        instr = [""] * len(needed)

    return {
        "needed_measurements": needed,
        "short_instructions": instr,
        "size_table": table,
        "unit_system": unit_system,
    }


def _unit_symbol(sys: Literal["EU", "US"]) -> str:
    """Преобразуем систему в символ единиц для find_best_size."""
    return "in" if sys == "US" else "cm"


# ---------------- Endpoints ----------------
@app.post("/size_detection", response_model=SizeDetectionResponse)
def size_detection(payload: SizeDetectionRequest):
    """
    Шаг 1: получаем план от LLM, нормализуем, сохраняем по token и возвращаем,
    что именно нужно ввести пользователю.
    """
    ai_result = main.ai_size_detector(payload.link, payload.size_type, payload.brand)

    plan = _normalize_plan(ai_result, payload.size_type)
    token = _save_plan(plan)

    return SizeDetectionResponse(
        token=token,
        unit_system=plan["unit_system"],
        needed_measurements=plan["needed_measurements"],
        short_instructions=plan["short_instructions"],
    )


@app.post("/get_params", response_model=BestSizeResponse)
def get_params(body: GetParamsRequest):
    """
    Шаг 2: принимаем значения от пользователя, поднимаем план по token,
    валидируем, при необходимости конвертируем единицы и считаем лучший размер.
    """
    plan = _load_plan(body.token)

    needed = plan["needed_measurements"]
    incoming = {_norm_key(k): float(v) for k, v in body.values.items()}
    missing = [m for m in needed if m not in incoming]
    if missing:
        raise HTTPException(400, detail=f"Missing measurements: {', '.join(missing)}")

    ordered_vals = {m: incoming[m] for m in needed}

    values_canon = _convert_units(ordered_vals, body.unit_system, plan["unit_system"])

    unit_symbol = _unit_symbol(plan["unit_system"])

    best = main.find_best_size(plan["size_table"], values_canon, unit_symbol)

    return BestSizeResponse(
        best_size=best,
        echo=values_canon,
        unit_system=plan["unit_system"]
    )
