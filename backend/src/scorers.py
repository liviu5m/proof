import json
import re

def check_json(response_text: str) -> bool:
    try:
        json.loads(response_text)
        return True
    except (json.JSONDecodeError, TypeError):
        return False

def check_regex(response_text: str, pattern: str) -> bool:
    if not pattern:
        return True
    return bool(re.search(pattern, response_text))

def check_word_count(response_text: str, min_words: int = 0, max_words: int = 10000) -> bool:
    words = response_text.split()
    return min_words <= len(words) <= max_words

def check_keywords(response_text: str, required: list[str] = None, forbidden: list[str] = None) -> bool:
    required = required or []
    forbidden = forbidden or []
    text_lower = response_text.lower()
    
    for req in required:
        if req.lower() not in text_lower:
            return False
            
    for forb in forbidden:
        if forb.lower() in text_lower:
            return False
            
    return True


    
