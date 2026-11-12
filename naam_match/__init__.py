"""naam-match: transparent name matching for Indian records (Hindi, other Indian scripts and English)."""
from .core import (Result, fold, jaro_winkler, key, match, script_names, similarity, split_relation, to_devanagari,
                   translit)
from .batch import dedupe, link, match_rows

__all__ = ["match", "Result", "key", "split_relation", "translit", "to_devanagari", "script_names", "fold",
           "jaro_winkler", "similarity", "match_rows", "link", "dedupe"]
__version__ = "0.2.0"
