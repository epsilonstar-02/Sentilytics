"""
Shared constants for the YouTube Analytics chatbot tools.
"""

# Product name normalization mapping
# Maps various user inputs to the exact folder names used in the data structure
PRODUCT_MAP = {
    "iphone 17": "iPhone_17",
    "iphone17": "iPhone_17",
    "iphone_17": "iPhone_17",
    "iphone 17 pro": "iPhone_17_Pro",
    "iphone17pro": "iPhone_17_Pro",
    "iphone_17_pro": "iPhone_17_Pro",
    "iphone 17 pro max": "iPhone_17_Pro",
    "macbook": "MacBook_Pro_14-inch_M5",
    "macbook pro": "MacBook_Pro_14-inch_M5",
    "macbook_pro_14-inch_m5": "MacBook_Pro_14-inch_M5",
    "macbook pro m5": "MacBook_Pro_14-inch_M5",
    "chatgpt": "ChatGPT_GPT-5",
    "gpt-5": "ChatGPT_GPT-5",
    "gpt5": "ChatGPT_GPT-5",
    "chatgpt_gpt-5": "ChatGPT_GPT-5",
}

# List of all available products (exact folder names)
AVAILABLE_PRODUCTS = [
    "iPhone_17_Pro",
    "MacBook_Pro_14-inch_M5", 
    "ChatGPT_GPT-5",
]

# Products with sentiment data available
PRODUCTS_WITH_SENTIMENT = [
    "iPhone_17_Pro",
    "ChatGPT_GPT-5",
]


def normalize_product_name(product: str) -> str:
    """Normalize product name to match folder structure."""
    if not product:
        return None
    product_lower = product.lower().strip()
    return PRODUCT_MAP.get(product_lower, product.replace(" ", "_"))
