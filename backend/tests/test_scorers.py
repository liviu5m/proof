import pytest
import re
from src.scorers import check_json, check_regex, check_word_count, check_keywords

def test_check_json_edge_cases():
    assert check_json('{"key": "value"}') is True
    assert check_json('[1, 2, 3]') is True
    assert check_json('{"nested": {"a": 1}}') is True
    
    assert check_json('Not JSON') is False
    assert check_json('') is False
    assert check_json('{"key": unquoted}') is False
    assert check_json('123') is True  
    assert check_json(None) is False

def test_check_regex_edge_cases():
    assert check_regex("Order 456 placed", r"\d+") is True
    assert check_regex("abc123xyz", r"^[a-z]+\d+[a-z]+$") is True
    
    assert check_regex("Any text", "") is True
    assert check_regex("Any text", None) is True
    
    assert check_regex("No numbers", r"\d+") is False

def test_check_word_count_edge_cases():
    text = "hello world from pytest"
    assert check_word_count(text, min_words=1, max_words=10) is True
    assert check_word_count(text, min_words=4, max_words=4) is True
    assert check_word_count(text, min_words=5, max_words=10) is False
    assert check_word_count("", min_words=0, max_words=5) is True
    assert check_word_count("", min_words=1, max_words=5) is False
    assert check_word_count("   multiple    spaces   ", min_words=2, max_words=2) is True

def test_check_keywords_edge_cases():
    text = "The Quick Brown Fox jumps over the LAZY dog!"
    
    # Required & Forbidden valid
    assert check_keywords(text, required=["quick", "fox"], forbidden=["cat", "wolf"]) is True
    
    # Missing required
    assert check_keywords(text, required=["quick", "missing"], forbidden=[]) is False
    
    # Forbidden present
    assert check_keywords(text, required=["fox"], forbidden=["lazy"]) is False
    
    # Case insensitivity check
    assert check_keywords(text, required=["QUICK", "dog!"], forbidden=[]) is True
    
    # Empty lists
    assert check_keywords(text, required=[], forbidden=[]) is True
    assert check_keywords(text, required=None, forbidden=None) is True
