#!/usr/bin/env python
"""Seed ModelCatalog costs from LiteLLM snapshot.
Only updates EXISTING models — never adds new ones."""
import json
import re
from decimal import Decimal
from pathlib import Path

from sqlmodel import Session, select

from src.db import _get_engine
from src.models import ModelCatalog

SEED_FILE = Path(__file__).parent.parent / "src" / "llm" / "seed_data" / "model_prices.json"

# Map LiteLLM provider -> our provider name
PROVIDER_MAP = {
    "openai": "openai",
    "anthropic": "anthropic",
    "gemini": "google",
    "vertex_ai": "google",
    "ollama": "ollama",
    # Add more as needed
}

def load_seed_data() -> dict:
    with open(SEED_FILE) as f:
        return json.load(f)


def normalize_seed_model_id(raw_id: str, litellm_provider: str) -> str:
    """Convert LiteLLM model ID to match our catalog's model_id."""
    # Remove provider prefix: "gemini/gemini-2.5-flash" -> "gemini-2.5-flash"
    # "vertex_ai/gemini-2.5-flash" -> "gemini-2.5-flash"
    if "/" in raw_id:
        return raw_id.split("/", 1)[1]
    return raw_id


def seed():
    data = load_seed_data()
    engine = _get_engine()

    # Build lookup: (our_provider, normalized_model_id) -> price_info
    price_lookup = {}
    for raw_id, info in data.items():
        provider = PROVIDER_MAP.get(info.get("litellm_provider"))
        if not provider:
            continue
        model_id = normalize_seed_model_id(raw_id, info.get("litellm_provider"))
        in_price = info.get("input_cost_per_token")
        out_price = info.get("output_cost_per_token")
        max_toks = info.get("max_tokens") or info.get("max_input_tokens")
        if in_price is not None and out_price is not None:
            price_lookup[(provider, model_id)] = {
                "in_per_1m": Decimal(str(in_price * 1_000_000)).quantize(Decimal("0.000001")),
                "out_per_1m": Decimal(str(out_price * 1_000_000)).quantize(Decimal("0.000001")),
                "max_tokens": max_toks,
            }

    print(f"Loaded {len(price_lookup)} price entries from seed data")

    with Session(engine) as session:
        # Get all EXISTING models from catalog
        catalog_models = session.exec(select(ModelCatalog)).all()
        print(f"Found {len(catalog_models)} models in catalog")

        updated = 0
        matched = 0
        for model in catalog_models:
            key = (model.provider, model.model_id)
            if key in price_lookup:
                matched += 1
                prices = price_lookup[key]
                changed = False
                if model.input_cost_per_1m is None:
                    model.input_cost_per_1m = prices["in_per_1m"]
                    changed = True
                if model.output_cost_per_1m is None:
                    model.output_cost_per_1m = prices["out_per_1m"]
                    changed = True
                if model.max_tokens is None and prices["max_tokens"]:
                    model.max_tokens = prices["max_tokens"]
                    changed = True
                if changed:
                    session.add(model)
                    updated += 1

        session.commit()
        print(f"Matched: {matched}, Updated: {updated}")


if __name__ == "__main__":
    seed()
