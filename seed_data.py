# seed_data.py
# Realistic seed data for Vera bot demo across multiple business categories.

from datetime import datetime, timezone

UTC = timezone.utc

# ============================================================================
# Category Contexts
# ============================================================================

CATEGORIES = [
    {
        "scope": "category",
        "context_id": "dentists",
        "payload": {
            "slug": "dentists",
            "voice": {"tone": "clinical-professional", "taboos": ["guarantee", "cure", "permanent solution"]},
            "digest": [{"title": "JIDA Oct 2024: Fluoride varnish reduces caries by 38%", "source": "JIDA", "finding": "38% caries reduction with bi-annual fluoride varnish"}],
        },
    },
    {
        "scope": "category",
        "context_id": "gyms",
        "payload": {
            "slug": "gyms",
            "voice": {"tone": "motivational-energetic", "taboos": ["steroids", "extreme weight loss", "guaranteed results"]},
            "digest": [{"title": "Fitness trend: HIIT memberships up 25% in metros", "source": "IHRSA India", "finding": "25% growth in HIIT class sign-ups Q1 2026"}],
        },
    },
    {
        "scope": "category",
        "context_id": "pharmacies",
        "payload": {
            "slug": "pharmacies",
            "voice": {"tone": "trustworthy-helpful", "taboos": ["self-diagnose", "skip doctor", "guaranteed cure"]},
            "digest": [{"title": "Online pharmacy orders grew 40% YoY", "source": "PharmaBiz", "finding": "40% increase in online medicine orders in tier-2 cities"}],
        },
    },
    {
        "scope": "category",
        "context_id": "restaurants",
        "payload": {
            "slug": "restaurants",
            "voice": {"tone": "warm-appetizing", "taboos": ["cheapest", "unlimited free"]},
            "digest": [{"title": "Weekend dine-in traffic up 18% post-monsoon", "source": "NRAI", "finding": "18% dine-in spike on Fri-Sun across metros"}],
        },
    },
    {
        "scope": "category",
        "context_id": "salons",
        "payload": {
            "slug": "salons",
            "voice": {"tone": "trendy-friendly", "taboos": ["chemical-free guarantee", "permanent straightening forever"]},
            "digest": [{"title": "Keratin treatments demand up 30%", "source": "Beauty Biz India", "finding": "30% rise in keratin bookings this quarter"}],
        },
    },
]

# ============================================================================
# Merchant Contexts
# ============================================================================

MERCHANTS = [
    # --- Dentists ---
    {
        "scope": "merchant",
        "context_id": "m_dent_001",
        "payload": {
            "merchant_id": "m_dent_001",
            "category_slug": "dentists",
            "identity": {"name": "SmileCare Dental Clinic", "owner_first_name": "Dr. Meera", "language_pref": "en", "category": "dentists"},
            "performance": {"ctr": 0.018, "views_last_30d": 430, "bookings_last_30d": 12},
            "offers": [{"title": "Scaling + Polish ₹799", "status": "active"}],
            "signals": ["high_rating_4.6", "responds_within_1hr"],
        },
    },
    {
        "scope": "merchant",
        "context_id": "m_dent_002",
        "payload": {
            "merchant_id": "m_dent_002",
            "category_slug": "dentists",
            "identity": {"name": "DentAlign Studio", "owner_first_name": "Dr. Arjun", "language_pref": "hi", "category": "dentists"},
            "performance": {"ctr": 0.012, "views_last_30d": 210, "bookings_last_30d": 5},
            "offers": [{"title": "Teeth Whitening ₹2999", "status": "active"}],
            "signals": ["new_listing", "low_engagement"],
        },
    },
    # --- Gyms ---
    {
        "scope": "merchant",
        "context_id": "m_gym_001",
        "payload": {
            "merchant_id": "m_gym_001",
            "category_slug": "gyms",
            "identity": {"name": "IronPulse Fitness", "owner_first_name": "Vikram", "language_pref": "en", "category": "gyms"},
            "performance": {"ctr": 0.025, "views_last_30d": 890, "bookings_last_30d": 45},
            "offers": [{"title": "3-Month HIIT Pack ₹4999", "status": "active"}, {"title": "Free Trial Class", "status": "active"}],
            "signals": ["trending_up", "high_footfall"],
        },
    },
    {
        "scope": "merchant",
        "context_id": "m_gym_002",
        "payload": {
            "merchant_id": "m_gym_002",
            "category_slug": "gyms",
            "identity": {"name": "FlexZone Gym", "owner_first_name": "Priya", "language_pref": "hi", "category": "gyms"},
            "performance": {"ctr": 0.009, "views_last_30d": 150, "bookings_last_30d": 3},
            "offers": [],
            "signals": ["declining_views", "no_active_offers"],
        },
    },
    # --- Pharmacies ---
    {
        "scope": "merchant",
        "context_id": "m_pharma_001",
        "payload": {
            "merchant_id": "m_pharma_001",
            "category_slug": "pharmacies",
            "identity": {"name": "MedPlus Wellness", "owner_first_name": "Rajesh", "language_pref": "en", "category": "pharmacies"},
            "performance": {"ctr": 0.032, "views_last_30d": 1200, "orders_last_30d": 340},
            "offers": [{"title": "Free delivery on orders above ₹299", "status": "active"}],
            "signals": ["top_seller", "fast_delivery"],
        },
    },
    {
        "scope": "merchant",
        "context_id": "m_pharma_002",
        "payload": {
            "merchant_id": "m_pharma_002",
            "category_slug": "pharmacies",
            "identity": {"name": "HealthFirst Pharmacy", "owner_first_name": "Sunita", "language_pref": "hi", "category": "pharmacies"},
            "performance": {"ctr": 0.015, "views_last_30d": 380, "orders_last_30d": 60},
            "offers": [{"title": "BP Monitor ₹899", "status": "active"}],
            "signals": ["steady_growth"],
        },
    },
    # --- Restaurants ---
    {
        "scope": "merchant",
        "context_id": "m_rest_001",
        "payload": {
            "merchant_id": "m_rest_001",
            "category_slug": "restaurants",
            "identity": {"name": "Spice Junction", "owner_first_name": "Chef Anand", "language_pref": "en", "category": "restaurants"},
            "performance": {"ctr": 0.041, "views_last_30d": 2100, "orders_last_30d": 520, "avg_rating": 4.4},
            "offers": [{"title": "Weekend Thali ₹249", "status": "active"}, {"title": "Family Pack 20% savings", "status": "active"}],
            "signals": ["weekend_spike", "repeat_customers_high"],
        },
    },
    {
        "scope": "merchant",
        "context_id": "m_rest_002",
        "payload": {
            "merchant_id": "m_rest_002",
            "category_slug": "restaurants",
            "identity": {"name": "The Wok Box", "owner_first_name": "Lisa", "language_pref": "en", "category": "restaurants"},
            "performance": {"ctr": 0.022, "views_last_30d": 650, "orders_last_30d": 110, "avg_rating": 4.1},
            "offers": [{"title": "Combo Meal ₹199", "status": "active"}],
            "signals": ["new_menu_launch", "needs_reviews"],
        },
    },
    # --- Salons ---
    {
        "scope": "merchant",
        "context_id": "m_salon_001",
        "payload": {
            "merchant_id": "m_salon_001",
            "category_slug": "salons",
            "identity": {"name": "Glamour Studio", "owner_first_name": "Neha", "language_pref": "en", "category": "salons"},
            "performance": {"ctr": 0.029, "views_last_30d": 780, "bookings_last_30d": 95},
            "offers": [{"title": "Keratin Treatment ₹3499", "status": "active"}, {"title": "Bridal Package ₹14999", "status": "active"}],
            "signals": ["wedding_season_boost", "top_rated_4.8"],
        },
    },
    {
        "scope": "merchant",
        "context_id": "m_salon_002",
        "payload": {
            "merchant_id": "m_salon_002",
            "category_slug": "salons",
            "identity": {"name": "Urban Cuts", "owner_first_name": "Rohit", "language_pref": "hi", "category": "salons"},
            "performance": {"ctr": 0.011, "views_last_30d": 200, "bookings_last_30d": 8},
            "offers": [{"title": "Men's Grooming Combo ₹499", "status": "active"}],
            "signals": ["low_visibility", "good_reviews_but_low_traffic"],
        },
    },
]

# ============================================================================
# Customer Contexts
# ============================================================================

CUSTOMERS = [
    {
        "scope": "customer",
        "context_id": "c_001",
        "payload": {
            "customer_id": "c_001",
            "identity": {"name": "Rahul Sharma", "language_pref": "hi", "city": "Delhi"},
            "relationship": {"visits_last_90d": 3, "avg_spend": 450, "loyalty_tier": "silver"},
            "preferences": ["dentists", "restaurants"],
        },
    },
    {
        "scope": "customer",
        "context_id": "c_002",
        "payload": {
            "customer_id": "c_002",
            "identity": {"name": "Ananya Patel", "language_pref": "en", "city": "Mumbai"},
            "relationship": {"visits_last_90d": 8, "avg_spend": 1200, "loyalty_tier": "gold"},
            "preferences": ["salons", "gyms"],
        },
    },
    {
        "scope": "customer",
        "context_id": "c_003",
        "payload": {
            "customer_id": "c_003",
            "identity": {"name": "Karthik Reddy", "language_pref": "en", "city": "Hyderabad"},
            "relationship": {"visits_last_90d": 1, "avg_spend": 200, "loyalty_tier": "bronze"},
            "preferences": ["pharmacies", "restaurants"],
        },
    },
    {
        "scope": "customer",
        "context_id": "c_004",
        "payload": {
            "customer_id": "c_004",
            "identity": {"name": "Sneha Iyer", "language_pref": "en", "city": "Bangalore"},
            "relationship": {"visits_last_90d": 5, "avg_spend": 800, "loyalty_tier": "silver"},
            "preferences": ["salons", "restaurants"],
        },
    },
    {
        "scope": "customer",
        "context_id": "c_005",
        "payload": {
            "customer_id": "c_005",
            "identity": {"name": "Amit Verma", "language_pref": "hi", "city": "Jaipur"},
            "relationship": {"visits_last_90d": 12, "avg_spend": 600, "loyalty_tier": "gold"},
            "preferences": ["gyms", "pharmacies"],
        },
    },
]

# ============================================================================
# Trigger Contexts
# ============================================================================

TRIGGERS = [
    # Dentist triggers
    {"scope": "trigger", "context_id": "tr_dent_perf", "payload": {"kind": "perf_spike", "merchant_id": "m_dent_001", "suppression_key": "perf_m_dent_001", "payload": {"delta_pct": 35, "metric": "profile views", "reason": "magicpin promo boost"}}},
    {"scope": "trigger", "context_id": "tr_dent_research", "payload": {"kind": "research_digest", "merchant_id": "m_dent_001", "source": "JIDA", "suppression_key": "research_m_dent_001"}},
    {"scope": "trigger", "context_id": "tr_dent_recall", "payload": {"kind": "recall_due", "merchant_id": "m_dent_001", "scope": "customer", "customer_id": "c_001", "suppression_key": "recall_c001_dent", "payload": {"last_visit_days": 180, "service": "dental checkup"}}},

    # Gym triggers
    {"scope": "trigger", "context_id": "tr_gym_perf", "payload": {"kind": "perf_spike", "merchant_id": "m_gym_001", "suppression_key": "perf_m_gym_001", "payload": {"delta_pct": 60, "metric": "trial sign-ups", "reason": "New Year resolution wave"}}},
    {"scope": "trigger", "context_id": "tr_gym_drop", "payload": {"kind": "engagement_drop", "merchant_id": "m_gym_002", "suppression_key": "drop_m_gym_002", "payload": {"delta_pct": -25, "metric": "check-ins", "reason": "summer vacation period"}}},
    {"scope": "trigger", "context_id": "tr_gym_renewal", "payload": {"kind": "renewal_due", "merchant_id": "m_gym_001", "scope": "customer", "customer_id": "c_005", "suppression_key": "renew_c005_gym", "payload": {"membership_expiry_days": 7, "plan": "3-Month HIIT"}}},

    # Pharmacy triggers
    {"scope": "trigger", "context_id": "tr_pharma_perf", "payload": {"kind": "perf_spike", "merchant_id": "m_pharma_001", "suppression_key": "perf_m_pharma_001", "payload": {"delta_pct": 40, "metric": "online orders", "reason": "flu season demand"}}},
    {"scope": "trigger", "context_id": "tr_pharma_reorder", "payload": {"kind": "reorder_reminder", "merchant_id": "m_pharma_001", "scope": "customer", "customer_id": "c_003", "suppression_key": "reorder_c003_pharma", "payload": {"medicine": "BP tablets", "last_order_days": 28}}},

    # Restaurant triggers
    {"scope": "trigger", "context_id": "tr_rest_perf", "payload": {"kind": "perf_spike", "merchant_id": "m_rest_001", "suppression_key": "perf_m_rest_001", "payload": {"delta_pct": 45, "metric": "weekend orders", "reason": "weekend surge"}}},
    {"scope": "trigger", "context_id": "tr_rest_review", "payload": {"kind": "review_boost", "merchant_id": "m_rest_002", "suppression_key": "review_m_rest_002", "payload": {"current_reviews": 42, "target_reviews": 50, "avg_rating": 4.1}}},
    {"scope": "trigger", "context_id": "tr_rest_winback", "payload": {"kind": "winback", "merchant_id": "m_rest_001", "scope": "customer", "customer_id": "c_004", "suppression_key": "winback_c004_rest", "payload": {"days_since_last_visit": 45, "favorite_item": "Paneer Tikka Thali"}}},

    # Salon triggers
    {"scope": "trigger", "context_id": "tr_salon_perf", "payload": {"kind": "perf_spike", "merchant_id": "m_salon_001", "suppression_key": "perf_m_salon_001", "payload": {"delta_pct": 55, "metric": "bookings", "reason": "wedding season"}}},
    {"scope": "trigger", "context_id": "tr_salon_drop", "payload": {"kind": "engagement_drop", "merchant_id": "m_salon_002", "suppression_key": "drop_m_salon_002", "payload": {"delta_pct": -30, "metric": "profile views", "reason": "competition opened nearby"}}},
    {"scope": "trigger", "context_id": "tr_salon_appt", "payload": {"kind": "appointment_reminder", "merchant_id": "m_salon_001", "scope": "customer", "customer_id": "c_002", "suppression_key": "appt_c002_salon", "payload": {"service": "Keratin Treatment", "days_until": 2}}},
]


def load_seed_data(store):
    """Load all seed data into the context store."""
    import time
    version = int(time.time())
    loaded = {"categories": 0, "merchants": 0, "customers": 0, "triggers": 0}

    for cat in CATEGORIES:
        try:
            store.store_context(cat["scope"], cat["context_id"], version, cat["payload"])
            loaded["categories"] += 1
        except ValueError:
            pass

    for m in MERCHANTS:
        try:
            store.store_context(m["scope"], m["context_id"], version, m["payload"])
            loaded["merchants"] += 1
        except ValueError:
            pass

    for c in CUSTOMERS:
        try:
            store.store_context(c["scope"], c["context_id"], version, c["payload"])
            loaded["customers"] += 1
        except ValueError:
            pass

    for t in TRIGGERS:
        try:
            store.store_context(t["scope"], t["context_id"], version, t["payload"])
            loaded["triggers"] += 1
        except ValueError:
            pass

    return loaded
