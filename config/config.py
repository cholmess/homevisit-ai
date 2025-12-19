"""
Centralized configuration for tenant law processing project.
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CONTEXT_DOCS_DIR = PROJECT_ROOT / "Context Documents"

# Output files
BASIC_SUMMARIES_FILE = PROCESSED_DATA_DIR / "tenant_law_summaries.json"
COMPREHENSIVE_SUMMARIES_FILE = PROCESSED_DATA_DIR / "comprehensive_tenant_law.json"
UNIFIED_KNOWLEDGE_FILE = PROCESSED_DATA_DIR / "unified_tenant_law_knowledge.json"
PDF_EXTRACTION_SUMMARY = PROCESSED_DATA_DIR / "pdf_extraction_summary.json"

# Source files
PLACES_TO_SUMMARIZE = PROJECT_ROOT / "places_to_summarize.txt"

# Qdrant configuration
QDRANT_CONFIG = {
    "collection_name": "tenant_law",
    "embedding_model": "all-MiniLM-L6-v2",
    "host": "localhost",
    "port": 6333,
    # For cloud setup, set these environment variables:
    # QDRANT_URL=https://your-cluster.qdrant.io
    # QDRANT_API_KEY=your-api-key
}

# Processing configuration
PROCESSING_CONFIG = {
    "batch_size": 50,
    "max_chunk_length": 1000,
    "overlap": 100,
}

# Category taxonomy
STANDARD_CATEGORIES = {
    "Contract Basics": {
        "includes": ["Contract Basics", "Contract basics"],
        "description": "Contract formation, language, terms, and structure"
    },
    "Deposits & Payments": {
        "includes": ["Deposits", "Deposits & Payments"],
        "description": "Security deposits, payment methods, and financial obligations"
    },
    "Rent & Costs": {
        "includes": ["Rent & Costs"],
        "description": "Rent amounts, increases, utilities, and cost allocations"
    },
    "Repairs & Maintenance": {
        "includes": ["Repairs & Maintenance"],
        "description": "Repair responsibilities, maintenance obligations, and property upkeep"
    },
    "Rights & Obligations": {
        "includes": ["Rights & obligations", "Rights & Obligations"],
        "description": "Tenant and landlord rights, access rules, and legal obligations"
    },
    "Notice Periods": {
        "includes": ["Notice periods", "Termination & Notice"],
        "description": "Termination notices, notice periods, and ending tenancy"
    },
    "Utility Costs": {
        "includes": ["Utility Costs"],
        "description": "Heating, water, electricity, and utility bill settlements"
    },
    "Special Situations": {
        "includes": ["Special Situations"],
        "description": "Property sale, inheritance, force majeure, and exceptional cases"
    }
}

# Ensure directories exist
def ensure_directories():
    """Create all necessary directories if they don't exist."""
    for dir_path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR]:
        dir_path.mkdir(exist_ok=True)

# Auto-create directories on import
ensure_directories()
