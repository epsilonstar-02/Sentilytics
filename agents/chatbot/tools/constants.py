"""
Shared constants for the YouTube Analytics chatbot tools.
"""

# Product name normalization mapping
# Maps various user inputs to the exact database product names (with spaces)
PRODUCT_MAP = {
    "iphone 17": "iPhone 17 Pro",
    "iphone17": "iPhone 17 Pro",
    "iphone_17": "iPhone 17 Pro",
    "iphone 17 pro": "iPhone 17 Pro",
    "iphone17pro": "iPhone 17 Pro",
    "iphone_17_pro": "iPhone 17 Pro",
    "iphone 17 pro max": "iPhone 17 Pro",
    "macbook": "MacBook Pro 14-inch M5",
    "macbook pro": "MacBook Pro 14-inch M5",
    "macbook_pro_14-inch_m5": "MacBook Pro 14-inch M5",
    "macbook pro m5": "MacBook Pro 14-inch M5",
    "chatgpt": "ChatGPT GPT-5",
    "gpt-5": "ChatGPT GPT-5",
    "gpt5": "ChatGPT GPT-5",
    "chatgpt_gpt-5": "ChatGPT GPT-5",
}

# List of all available products (exact database names with spaces)
AVAILABLE_PRODUCTS = [
    "iPhone 17 Pro",
    "MacBook Pro 14-inch M5", 
    "ChatGPT GPT-5",
]

# Products with sentiment data available
PRODUCTS_WITH_SENTIMENT = [
    "iPhone 17 Pro",
    "ChatGPT GPT-5",
]


def normalize_product_name(product: str) -> str:
    """Normalize product name to match database product names."""
    if not product:
        return None
    product_lower = product.lower().strip()
    # Return mapped name or original with underscores replaced by spaces
    return PRODUCT_MAP.get(product_lower, product.replace("_", " "))
