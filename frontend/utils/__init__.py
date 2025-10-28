"""
Utils package - Utility functions and helpers
"""
from .synonyms import (
    expand_query_with_synonyms,
    detect_category,
    get_category_synonyms,
    OMEGA_SYNONYMS,
    MAGNESIUM_SYNONYMS,
    VITAMIN_C_SYNONYMS,
    COLLAGEN_SYNONYMS,
    PROBIOTICS_SYNONYMS,
    IMMUNITY_SYNONYMS,
)

from .special_handlers import (
    is_immunity_query,
    is_small_talk,
    is_all_options_request,
    detect_special_product_category,
    get_special_category_instructions,
    enhance_context_with_special_instructions,
)

__all__ = [
    # Synonyms
    "expand_query_with_synonyms",
    "detect_category",
    "get_category_synonyms",
    "OMEGA_SYNONYMS",
    "MAGNESIUM_SYNONYMS",
    "VITAMIN_C_SYNONYMS",
    "COLLAGEN_SYNONYMS",
    "PROBIOTICS_SYNONYMS",
    "IMMUNITY_SYNONYMS",
    
    # Special Handlers
    "is_immunity_query",
    "is_small_talk",
    "is_all_options_request",
    "detect_special_product_category",
    "get_special_category_instructions",
    "enhance_context_with_special_instructions",
]