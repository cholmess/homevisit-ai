#!/usr/bin/env python3
"""
Merge tenant law JSON files into unified knowledge base for Qdrant ingestion.
"""

import json
from pathlib import Path

def load_json_files():
    """Load both tenant law JSON files."""
    file1 = "/Users/christopherholmes/Documents/Projects/homevisit-ai/tenant_law_summaries.json"
    file2 = "/Users/christopherholmes/Documents/Projects/homevisit-ai/comprehensive_tenant_law.json"
    
    with open(file1, 'r', encoding='utf-8') as f:
        data1 = json.load(f)
    
    with open(file2, 'r', encoding='utf-8') as f:
        data2 = json.load(f)
    
    return data1, data2

def standardize_categories():
    """Define standardized category taxonomy."""
    return {
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

def find_duplicates(chunks):
    """Find and flag duplicate chunks based on title similarity."""
    seen_titles = set()
    duplicates = []
    unique_chunks = []
    
    for chunk in chunks:
        title = chunk.get('title', '').lower().strip()
        if title in seen_titles:
            duplicates.append(chunk)
        else:
            seen_titles.add(title)
            unique_chunks.append(chunk)
    
    return unique_chunks, duplicates

def merge_and_deduplicate(data1, data2):
    """Merge both datasets and remove duplicates."""
    all_chunks = data1['chunks'] + data2['chunks']
    
    # Find duplicates
    unique_chunks, duplicates = find_duplicates(all_chunks)
    
    print(f"Found {len(duplicates)} duplicate entries:")
    for dup in duplicates:
        print(f"  - {dup['title']} (category: {dup['category']})")
    
    # Standardize categories
    standard_cats = standardize_categories()
    standardized_chunks = []
    
    for chunk in unique_chunks:
        old_cat = chunk.get('category', '')
        new_cat = old_cat
        
        # Find standardized category
        for std_cat, info in standard_cats.items():
            if old_cat in info['includes']:
                new_cat = std_cat
                break
        
        chunk['category'] = new_cat
        chunk['original_category'] = old_cat if old_cat != new_cat else None
        standardized_chunks.append(chunk)
    
    return standardized_chunks

def create_unified_knowledge_base(chunks):
    """Create the unified knowledge base structure."""
    standard_cats = standardize_categories()
    
    # Count items per category
    category_counts = {}
    for chunk in chunks:
        cat = chunk['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    unified = {
        "metadata": {
            "source": "unified_tenant_law_knowledge_base",
            "created_for": "expat_tenant_assistant",
            "version": "1.0",
            "created_date": "2025-12-19",
            "categories": list(standard_cats.keys()),
            "category_descriptions": {k: v['description'] for k, v in standard_cats.items()},
            "total_chunks": len(chunks),
            "source_files": [
                "tenant_law_summaries.json (30 items)",
                "comprehensive_tenant_law.json (27 items)"
            ],
            "category_counts": category_counts
        },
        "chunks": chunks
    }
    
    return unified

def main():
    print("Loading JSON files...")
    data1, data2 = load_json_files()
    
    print(f"Loaded {len(data1['chunks'])} chunks from tenant_law_summaries.json")
    print(f"Loaded {len(data2['chunks'])} chunks from comprehensive_tenant_law.json")
    
    print("\nMerging and deduplicating...")
    merged_chunks = merge_and_deduplicate(data1, data2)
    
    print(f"\nAfter merging and deduplication: {len(merged_chunks)} unique chunks")
    
    # Create unified knowledge base
    unified_kb = create_unified_knowledge_base(merged_chunks)
    
    # Save unified file
    output_file = "/Users/christopherholmes/Documents/Projects/homevisit-ai/unified_tenant_law_knowledge.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unified_kb, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved unified knowledge base to: {output_file}")
    
    # Print summary
    print("\nUnified Knowledge Base Summary:")
    print("=" * 50)
    for cat, count in unified_kb['metadata']['category_counts'].items():
        print(f"{cat:20} : {count:3} items")
    print("=" * 50)
    print(f"{'TOTAL':20} : {len(merged_chunks):3} items")
    
    print("\nReady for Qdrant ingestion!")

if __name__ == "__main__":
    main()
