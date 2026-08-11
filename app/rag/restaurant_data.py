"""
RestaurantOS — Restaurant Data for RAG
Menu items, FAQs, policies, and delivery info to seed into ChromaDB.
"""

from __future__ import annotations

# ── Menu Items ───────────────────────────────────────────────────────────────

MENU_ITEMS = [
    # ── Chicken Flavours (Pizzas) ────────────────────────────────────────────────
    {"id": "pm_001", "category": "Chicken Flavours", "name": "Ranch Pizza", "price": 1590, "description": "Ranch sauce with tender chicken chunks, onions, and cheese. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_002", "category": "Chicken Flavours", "name": "Sriracha Pizza", "price": 1590, "description": "Spicy Sriracha sauce topped with savory chicken and mozzarella. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_003", "category": "Chicken Flavours", "name": "Royal Crown Pizza", "price": 1590, "description": "Royal blend of chicken tikka, veggies, and cream cheese crust. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_004", "category": "Chicken Flavours", "name": "Creamy Super Max", "price": 1590, "description": "Rich creamy base with grilled chicken, mushrooms, and cheese. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_005", "category": "Chicken Flavours", "name": "Creamy Super Kabab", "price": 1590, "description": "Chicken kebab pieces layered on a rich creamy sauce. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_006", "category": "Chicken Flavours", "name": "Peri Max Pizza", "price": 1590, "description": "Fiery Peri-Peri sauce with spiced chicken, capsicum, and onions. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_007", "category": "Chicken Flavours", "name": "Chicken Max Pizza", "price": 1590, "description": "Loaded with double chicken tikka, fajita, and mozzarella. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_008", "category": "Chicken Flavours", "name": "Malai Boti Pizza", "price": 1590, "description": "Tender chicken malai boti with creamy white sauce and herbs. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_009", "category": "Chicken Flavours", "name": "Creamy Tikka Pizza", "price": 1590, "description": "Local chicken tikka chunks with a smooth creamy twist. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_010", "category": "Chicken Flavours", "name": "Afghani Tikka Pizza", "price": 1590, "description": "Mildly seasoned Afghani style chicken tikka with onions. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_011", "category": "Chicken Flavours", "name": "BBQ Tikka Pizza", "price": 1590, "description": "Smoky BBQ chicken tikka with onions and melted cheese. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_012", "category": "Chicken Flavours", "name": "Chicken Fajita Pizza", "price": 1590, "description": "Traditional Mexican style fajita chicken, onions, and capsicum. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_013", "category": "Chicken Flavours", "name": "Fajita Sensation Pizza", "price": 1590, "description": "Spicy chicken fajita, jalapenos, onions, and bell peppers. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_014", "category": "Chicken Flavours", "name": "Spicy Italian Pizza", "price": 1590, "description": "Hot herbs, spicy chicken, green chilies, and Italian sauce. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_015", "category": "Chicken Flavours", "name": "Italian Light Pizza", "price": 1590, "description": "Light herbs, diced chicken, black olives, and tomatoes. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_016", "category": "Chicken Flavours", "name": "Tandoori Hot Pizza", "price": 1590, "description": "Spicy tandoori chicken, hot peppers, and red onions. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_017", "category": "Chicken Flavours", "name": "Kabab Super Max Pizza", "price": 1590, "description": "Stuffed kabab rim with juicy chicken kebabs on top. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},

    # ── Beef & Veggie Flavours (Pizzas) ──────────────────────────────────────────
    {"id": "pm_018", "category": "Beef & Veggie Flavours", "name": "Pepperoni & Chicken Pizza", "price": 1590, "description": "Classic beef pepperoni paired with grilled chicken. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_019", "category": "Beef & Veggie Flavours", "name": "Hot & Spicy Beef Pizza", "price": 1590, "description": "Minced beef, jalapenos, onions, and spicy tomato sauce. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_020", "category": "Beef & Veggie Flavours", "name": "Beef Super Max Pizza", "price": 1590, "description": "Loaded with seasoned beef, pepperoni, mushrooms, and olives. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_021", "category": "Beef & Veggie Flavours", "name": "Pepperoni & Cheese Pizza", "price": 1590, "description": "Generous beef pepperoni slices over 100% real mozzarella. Small: 790, Medium: 1590, Large: 2290, XL: 2790, Party: 3290", "available": True},
    {"id": "pm_022", "category": "Beef & Veggie Flavours", "name": "Veggie Max Pizza", "price": 1390, "description": "Mushrooms, onions, capsicum, tomatoes, and black olives. Small: 690, Medium: 1390, Large: 1990", "available": True},
    {"id": "pm_023", "category": "Beef & Veggie Flavours", "name": "Cheese Max Pizza", "price": 1390, "description": "Classic double layer of melted mozzarella cheese. Small: 690, Medium: 1390, Large: 1990", "available": True},

    # ── Appetizers & Sides ────────────────────────────────────────────────────────
    {"id": "pm_024", "category": "Appetizers & Sides", "name": "Tangy Wings", "price": 490, "description": "Tossed in tangy hot sauce, 6 pieces.", "available": True},
    {"id": "pm_025", "category": "Appetizers & Sides", "name": "Mozzarella Sticks", "price": 550, "description": "Crispy golden fried mozzarella cheese sticks, 4 pieces.", "available": True},
    {"id": "pm_026", "category": "Appetizers & Sides", "name": "Potato Skins", "price": 390, "description": "Baked potato skins stuffed with cheese and herbs.", "available": True},
    {"id": "pm_027", "category": "Appetizers & Sides", "name": "Finger Chicken Kebab", "price": 450, "description": "Crispy seasoned chicken kebab fingers.", "available": True},
    {"id": "pm_028", "category": "Appetizers & Sides", "name": "Max Platter", "price": 990, "description": "Sampler platter with wings, mozzarella sticks, nuggets, and garlic bread.", "available": True},
    {"id": "pm_029", "category": "Appetizers & Sides", "name": "Meaty Garlic Bread", "price": 390, "description": "Garlic bread topped with minced meat and melted cheese, 4 pieces.", "available": True},
    {"id": "pm_030", "category": "Appetizers & Sides", "name": "Chicken Nuggets", "price": 390, "description": "Golden fried crispy chicken nuggets, 6 pieces.", "available": True},
    {"id": "pm_031", "category": "Appetizers & Sides", "name": "Stick-o-Sandwich", "price": 490, "description": "Special chicken stuffed stick sandwich with sauce.", "available": True},

    # ── Pasta & Lasagne ────────────────────────────────────────────────────────────
    {"id": "pm_032", "category": "Pasta & Lasagne", "name": "Creamy Chicken Lasagne", "price": 790, "description": "Layers of pasta, chicken, creamy sauce, and cheese.", "available": True},
    {"id": "pm_033", "category": "Pasta & Lasagne", "name": "Beef Lasagne", "price": 850, "description": "Layers of pasta with minced beef, marinara, and cheese.", "available": True},
    {"id": "pm_034", "category": "Pasta & Lasagne", "name": "Creamy Chicken Pasta", "price": 690, "description": "Penne pasta in rich garlic cream sauce with grilled chicken.", "available": True},
    {"id": "pm_035", "category": "Pasta & Lasagne", "name": "Promo Lasagna", "price": 650, "description": "Special single-serving lasagna deal.", "available": True},

    # ── Deals ─────────────────────────────────────────────────────────────────────
    {"id": "pm_036", "category": "Deals", "name": "Max Deal", "price": 2300, "description": "2 Medium Pizzas + 4pcs Cheese Garlic Bread + Sauce + 1.5Ltr Drink.", "available": True},
    {"id": "pm_037", "category": "Deals", "name": "2 Big 2 Better Deal", "price": 2990, "description": "2 Large Pizzas of any flavour.", "available": True},
    {"id": "pm_038", "category": "Deals", "name": "Midnight Deal", "price": 1490, "description": "1 Medium Pizza + 2 Soft Drinks (Valid after 11 PM).", "available": True},
    {"id": "pm_039", "category": "Deals", "name": "Gathering Deal", "price": 4500, "description": "3 Large Pizzas + 2 Max Platters + 2.25L Drink.", "available": True},
]

# ── FAQs ─────────────────────────────────────────────────────────────────────

FAQS = [
    {
        "id": "faq_001",
        "question": "What are your operating hours?",
        "answer": "We are open daily from 10:00 AM to 11:00 PM (23:00).",
    },
    {
        "id": "faq_002",
        "question": "Do you offer delivery?",
        "answer": "Yes, we deliver within a 10 km radius. Delivery fee is PKR 150 for orders under PKR 1000. Free delivery for orders above PKR 1000.",
    },
    {
        "id": "faq_003",
        "question": "What payment methods do you accept?",
        "answer": "We accept Cash on Delivery (COD), JazzCash, and EasyPaisa.",
    },
    {
        "id": "faq_004",
        "question": "How long does delivery take?",
        "answer": "Typical delivery time is 30-45 minutes depending on your location and order size.",
    },
    {
        "id": "faq_005",
        "question": "Can I customize my order?",
        "answer": "Yes! You can add special instructions to any item. Common requests include extra spicy, no onions, less oil, etc.",
    },
    {
        "id": "faq_006",
        "question": "Do you have a minimum order for delivery?",
        "answer": "Yes, the minimum order for delivery is PKR 300.",
    },
    {
        "id": "faq_007",
        "question": "Can I cancel my order?",
        "answer": "You can cancel within 5 minutes of placing your order. After that, cancellation may not be possible if preparation has started.",
    },
    {
        "id": "faq_008",
        "question": "Do you offer dine-in?",
        "answer": "Yes, we have both dine-in and takeaway options available at our restaurant.",
    },
]

# ── Policies ─────────────────────────────────────────────────────────────────

POLICIES = [
    {
        "id": "policy_001",
        "title": "Delivery Policy",
        "content": "Delivery is available within a 10 km radius. Orders under PKR 1000 have a delivery fee of PKR 150. Orders above PKR 1000 get free delivery. Minimum order for delivery is PKR 300.",
    },
    {
        "id": "policy_002",
        "title": "Refund Policy",
        "content": "If you receive a wrong or damaged order, we will replace it free of charge. Refunds are processed within 3-5 business days.",
    },
    {
        "id": "policy_003",
        "title": "Order Modification",
        "content": "Orders can be modified within 5 minutes of placement. After that, modifications depend on preparation status.",
    },
    {
        "id": "policy_004",
        "title": "Maximum Order Quantity",
        "content": "Single item quantity is limited to 50 units per order. For bulk orders (above 50), please contact us directly.",
    },
    {
        "id": "policy_005",
        "title": "Operating Hours",
        "content": "The restaurant operates from 10:00 AM to 11:00 PM daily. Last order accepted at 10:30 PM.",
    },
]

# ── Delivery Information ─────────────────────────────────────────────────────

DELIVERY_INFO = [
    {
        "id": "delivery_001",
        "title": "Delivery Zones",
        "content": "Zone A (0-3 km): 20-30 minutes. Zone B (3-7 km): 30-40 minutes. Zone C (7-10 km): 40-50 minutes.",
    },
    {
        "id": "delivery_002",
        "title": "Delivery Fees",
        "content": "Orders under PKR 1000: PKR 150 delivery fee. Orders PKR 1000+: FREE delivery.",
    },
    {
        "id": "delivery_003",
        "title": "Delivery Partners",
        "content": "We use our own riders for fast and reliable delivery. All riders are trained in food safety and hygiene.",
    },
]


def get_all_documents() -> list[dict]:
    """
    Combine all restaurant knowledge into a flat list of documents
    ready for ChromaDB ingestion.

    Returns:
        List of dicts with 'id', 'text', and 'metadata' keys.
    """
    documents = []

    # Menu items
    for item in MENU_ITEMS:
        text = (
            f"Menu Item: {item['name']} | Category: {item['category']} | "
            f"Price: PKR {item['price']} | {item['description']} | "
            f"Available: {'Yes' if item['available'] else 'No'}"
        )
        documents.append({
            "id": item["id"],
            "text": text,
            "metadata": {"type": "menu", "category": item["category"], "name": item["name"], "price": item["price"]},
        })

    # FAQs
    for faq in FAQS:
        text = f"FAQ: {faq['question']} Answer: {faq['answer']}"
        documents.append({
            "id": faq["id"],
            "text": text,
            "metadata": {"type": "faq"},
        })

    # Policies
    for policy in POLICIES:
        text = f"Policy — {policy['title']}: {policy['content']}"
        documents.append({
            "id": policy["id"],
            "text": text,
            "metadata": {"type": "policy"},
        })

    # Delivery info
    for info in DELIVERY_INFO:
        text = f"Delivery — {info['title']}: {info['content']}"
        documents.append({
            "id": info["id"],
            "text": text,
            "metadata": {"type": "delivery"},
        })

    return documents


def get_menu_lookup() -> dict[str, dict]:
    """
    Return a dict mapping lowercase menu item names to their data.
    Used by the Validation Agent for quick menu checks.
    """
    return {item["name"].lower(): item for item in MENU_ITEMS}
