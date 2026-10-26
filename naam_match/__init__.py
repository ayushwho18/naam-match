"""naam-match: transparent Hindi/English name matching for Indian land records."""
from .core import Result, fold, jaro_winkler, match, similarity, translit

__all__ = ["match", "Result", "translit", "fold", "jaro_winkler", "similarity"]
__version__ = "0.1.0"
