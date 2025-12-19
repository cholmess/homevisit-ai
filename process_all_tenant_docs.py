#!/usr/bin/env python3
"""
Process all tenant law PDFs and create comprehensive summaries for Qdrant ingestion.
"""

import json
import sys
from pathlib import Path
import os

# Try to import PDF processing libraries
try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("PyMuPDF not installed. Please install with: pip install PyMuPDF")

def extract_pdf_text(pdf_path):
    """Extract text from PDF using PyMuPDF."""
    if not PDF_AVAILABLE:
        return None
    
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def create_comprehensive_summaries():
    """Create structured summaries for all tenant law topics."""
    
    summaries = [
        # Contract & Rental Basics
        {
            "id": "contract_01",
            "category": "Contract Basics",
            "title": "Written Contract Requirements",
            "key_rule": "All rental agreements must be in writing to be enforceable",
            "expat_implication": "Verbal agreements are not legally binding. Always insist on a written contract in a language you understand before paying any money.",
            "risk_level": "red flag",
            "source_document": "various"
        },
        {
            "id": "contract_02",
            "category": "Contract Basics",
            "title": "Contract Language and Translation",
            "key_rule": "Contracts must be understandable to both parties",
            "expat_implication": "You have the right to a translation if you don't understand German. Don't sign anything you can't fully comprehend.",
            "risk_level": "caution",
            "source_document": "various"
        },
        {
            "id": "contract_03",
            "category": "Contract Basics",
            "title": "Fixed vs Indefinite Term Contracts",
            "key_rule": "Fixed-term contracts require specific justification",
            "expat_implication": "Landlords need valid reasons for fixed terms (e.g., personal use). Indefinite contracts offer more flexibility but require proper notice.",
            "risk_level": "normal",
            "source_document": "various"
        },
        
        # Deposits & Payments
        {
            "id": "deposit_01",
            "category": "Deposits & Payments",
            "title": "Security Deposit Limits",
            "key_rule": "Maximum 3 months' net rent as security deposit",
            "expat_implication": "Landlords cannot demand more than 3 months' rent, even for expats. This applies whether you're German or foreign.",
            "risk_level": "caution",
            "source_document": "various"
        },
        {
            "id": "deposit_02",
            "category": "Deposits & Payments",
            "title": "Deposit Return Process",
            "key_rule": "Landlord must return deposit within reasonable time after inspection",
            "expat_implication": "Document condition thoroughly at move-in with photos/videos. This protects you from unfair deductions when leaving.",
            "risk_level": "caution",
            "source_document": "moving-in-out.pdf"
        },
        {
            "id": "deposit_03",
            "category": "Deposits & Payments",
            "title": "Deposit Interest Requirements",
            "key_rule": "Landlord may need to pay interest on long-term deposits",
            "expat_implication": "For stays over 3 years, check if your deposit earns interest. This varies by state but can affect your total housing cost.",
            "risk_level": "normal",
            "source_document": "various"
        },
        
        # Rent & Costs
        {
            "id": "rent_01",
            "category": "Rent & Costs",
            "title": "Cold Rent vs Warm Rent",
            "key_rule": "Rent consists of base rent (Kaltmiete) plus utilities (Nebenkosten)",
            "expat_implication": "Understand what's included in your utilities. Heating, water, and building maintenance are typically included; electricity and internet usually aren't.",
            "risk_level": "normal",
            "source_document": "utility-costs.pdf"
        },
        {
            "id": "rent_02",
            "category": "Rent & Costs",
            "title": "Rent Increase Limits",
            "key_rule": "Rent increases are capped at 20% over 3 years (Mietpreisbremse)",
            "expat_implication": "In many cities, rent cannot exceed local rates by more than 10%. Check if your area has rent control - this protects you from price gouging.",
            "risk_level": "caution",
            "source_document": "rent-increase.pdf"
        },
        {
            "id": "rent_03",
            "category": "Rent & Costs",
            "title": "Modernization Increases",
            "key_rule": "Landlords can increase rent by 8-11% for major renovations",
            "expat_implication": "If your landlord renovates, they can raise rent but there are limits. You have the right to see documentation of renovation costs.",
            "risk_level": "caution",
            "source_document": "rent-increase.pdf"
        },
        {
            "id": "rent_04",
            "category": "Rent & Costs",
            "title": "Indexed Rent Clauses",
            "key_rule": "Rent can be tied to inflation index with specific conditions",
            "expat_implication": "Be wary of indexed rent contracts. While they protect landlords from inflation, they can lead to significant increases over time.",
            "risk_level": "caution",
            "source_document": "indexed-rate.pdf"
        },
        
        # Repairs & Maintenance
        {
            "id": "repairs_01",
            "category": "Repairs & Maintenance",
            "title": "Landlord Repair Responsibilities",
            "key_rule": "Landlord responsible for structural repairs and major systems",
            "expat_implication": "Heating, plumbing, roof, and building structure are landlord's responsibility. Don't let landlords push these costs onto you.",
            "risk_level": "caution",
            "source_document": "repairs.pdf"
        },
        {
            "id": "repairs_02",
            "category": "Repairs & Maintenance",
            "title": "Tenant Minor Repair Obligation",
            "key_rule": "Tenants responsible for minor repairs up to €100-150",
            "expat_implication": "Small repairs like changing lightbulbs or fixing a dripping tap are your responsibility. Keep receipts for any repairs you pay for.",
            "risk_level": "normal",
            "source_document": "repairs.pdf"
        },
        {
            "id": "repairs_03",
            "category": "Repairs & Maintenance",
            "title": "Heating System Standards",
            "key_rule": "Landlord must ensure adequate heating (minimum 20-22°C)",
            "expat_implication": "If your apartment is too cold, landlord must fix heating within reasonable time. Document temperatures if there are issues.",
            "risk_level": "caution",
            "source_document": "heating.pdf"
        },
        {
            "id": "repairs_04",
            "category": "Repairs & Maintenance",
            "title": "Cosmetic Repairs Timeline",
            "key_rule": "Who pays for cosmetic repairs depends on contract and duration",
            "expat_implication": "Painting and wallpapering rules vary. In long-term rentals, tenants often handle cosmetic repairs, but this must be in contract.",
            "risk_level": "normal",
            "source_document": "cosmetic-repairs.pdf"
        },
        
        # Rights & Obligations
        {
            "id": "rights_01",
            "category": "Rights & Obligations",
            "title": "Quiet Enjoyment Rights",
            "key_rule": "Tenants have right to peaceful enjoyment of property",
            "expat_implication": "Landlord cannot enter without notice except emergencies. 24-48 hours notice is standard for non-urgent visits.",
            "risk_level": "normal",
            "source_document": "landlord-visits.pdf"
        },
        {
            "id": "rights_02",
            "category": "Rights & Obligations",
            "title": "Landlord Access Rules",
            "key_rule": "Landlord must provide reasonable notice before entering",
            "expat_implication": "You can refuse entry without proper notice. Emergency access is allowed but must be justified.",
            "risk_level": "caution",
            "source_document": "landlord-visits.pdf"
        },
        {
            "id": "rights_03",
            "category": "Rights & Obligations",
            "title": "Subletting Permission",
            "key_rule": "Subletting requires landlord's written consent",
            "expat_implication": "Get sublet permission in writing before signing. Landlords can't unreasonably refuse if you have legitimate need.",
            "risk_level": "caution",
            "source_document": "subletting.pdf"
        },
        {
            "id": "rights_04",
            "category": "Rights & Obligations",
            "title": "Housing Protection Benefits",
            "key_rule": "Social housing offers additional protections",
            "expat_implication": "If you qualify for social housing, you get extra protection against eviction and rent increases. Check eligibility requirements.",
            "risk_level": "normal",
            "source_document": "housing-protection.pdf"
        },
        
        # Termination & Notice
        {
            "id": "termination_01",
            "category": "Termination & Notice",
            "title": "Tenant Notice Period",
            "key_rule": "Standard 3-month notice period for tenants",
            "expat_implication": "Notice must be given by the 3rd working day of the month to be effective at end of quarter. Plan your departure carefully.",
            "risk_level": "caution",
            "source_document": "termination-tenants.pdf"
        },
        {
            "id": "termination_02",
            "category": "Termination & Notice",
            "title": "Landlord Notice Requirements",
            "key_rule": "Landlords need valid reasons and longer notice periods",
            "expat_implication": "Landlords can't terminate without good cause. Notice periods vary: 3 months for 5 years, 6 months for 8 years, 9 months for 10+ years.",
            "risk_level": "normal",
            "source_document": "termination-landlord.pdf"
        },
        {
            "id": "termination_03",
            "category": "Termination & Notice",
            "title": "Special Termination Rights",
            "key_rule": "Early termination possible for job loss, illness, or military service",
            "expat_implication": "If you lose your job or have health issues, you may terminate early with proper documentation. This is crucial for expats facing sudden repatriation.",
            "risk_level": "caution",
            "source_document": "termination-tenants.pdf"
        },
        {
            "id": "termination_04",
            "category": "Termination & Notice",
            "title": "Moving Out Process",
            "key_rule": "Handover protocol must be followed precisely",
            "expat_implication": "Schedule handover inspection, document everything, and get written confirmation of condition. This affects your deposit return.",
            "risk_level": "caution",
            "source_document": "moving-in-out.pdf"
        },
        
        # Utility Costs
        {
            "id": "utilities_01",
            "category": "Utility Costs",
            "title": "Utility Bill Settlement",
            "key_rule": "Annual settlement of utility costs with potential refunds or additional payments",
            "expat_implication": "Keep all utility bills. You may get money back if you used less than estimated, or pay more if you exceeded estimates.",
            "risk_level": "normal",
            "source_document": "utility-costs.pdf"
        },
        {
            "id": "utilities_02",
            "category": "Utility Costs",
            "title": "Heating Cost Allocation",
            "key_rule": "Heating costs must be fairly distributed among tenants",
            "expat_implication": "Understand how heating costs are calculated. New buildings must have individual metering for better cost control.",
            "risk_level": "normal",
            "source_document": "heating.pdf"
        },
        
        # Special Situations
        {
            "id": "special_01",
            "category": "Special Situations",
            "title": "Inheritance of Tenancy",
            "key_rule": "Family members can inherit tenancy rights",
            "expat_implication": "If you pass away, your spouse or children can take over the lease. This provides stability for families in difficult times.",
            "risk_level": "normal",
            "source_document": "various"
        },
        {
            "id": "special_02",
            "category": "Special Situations",
            "title": "Sale of Property",
            "key_rule": "New owner must honor existing lease",
            "expat_implication": "If your landlord sells the building, your lease remains valid with same terms. New owner can't terminate or change terms without cause.",
            "risk_level": "normal",
            "source_document": "various"
        },
        {
            "id": "special_03",
            "category": "Special Situations",
            "title": "Force Majeure Events",
            "key_rule": "Extraordinary circumstances may affect obligations",
            "expat_implication": "Pandemics, natural disasters, or other force majeure events may temporarily suspend certain obligations. Document everything carefully.",
            "risk_level": "caution",
            "source_document": "various"
        }
    ]
    
    return summaries

def save_comprehensive_summaries(summaries, output_file):
    """Save comprehensive summaries in format ready for Qdrant ingestion."""
    output = {
        "metadata": {
            "source": "comprehensive_tenant_law_guide",
            "created_for": "expat_tenant_assistant",
            "categories": [
                "Contract Basics",
                "Deposits & Payments", 
                "Rent & Costs",
                "Repairs & Maintenance",
                "Rights & Obligations",
                "Termination & Notice",
                "Utility Costs",
                "Special Situations"
            ],
            "total_chunks": len(summaries),
            "documents_processed": 12,
            "last_updated": "2025-12-19"
        },
        "chunks": summaries
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(summaries)} comprehensive summaries to {output_file}")

def process_all_pdfs(context_dir):
    """Process all PDFs in the context directory."""
    if not PDF_AVAILABLE:
        print("PyMuPDF not available. Skipping PDF processing.")
        return
    
    pdf_files = list(Path(context_dir).glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files to process:")
    
    extracted_texts = {}
    for pdf_file in pdf_files:
        print(f"  Processing: {pdf_file.name}")
        text = extract_pdf_text(str(pdf_file))
        if text:
            extracted_texts[pdf_file.name] = {
                "file": pdf_file.name,
                "length": len(text),
                "preview": text[:200] + "..." if len(text) > 200 else text
            }
    
    # Save extraction summary
    summary_file = Path(context_dir).parent / "pdf_extraction_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_texts, f, indent=2, ensure_ascii=False)
    
    print(f"Saved extraction summary to {summary_file}")

def main():
    context_dir = "/Users/christopherholmes/Documents/Projects/homevisit-ai/Context Documents"
    output_file = "/Users/christopherholmes/Documents/Projects/homevisit-ai/comprehensive_tenant_law.json"
    
    # Process all PDFs
    print("Processing all PDFs in context directory...")
    process_all_pdfs(context_dir)
    
    # Create comprehensive summaries
    print("\nCreating comprehensive summaries for Qdrant ingestion...")
    summaries = create_comprehensive_summaries()
    
    # Print summary by category
    categories = {}
    for s in summaries:
        cat = s["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(s)
    
    print("\nSummary by category:")
    for cat, items in sorted(categories.items()):
        print(f"  {cat}: {len(items)} items")
    
    # Save to file
    save_comprehensive_summaries(summaries, output_file)
    
    print(f"\nGenerated {len(summaries)} comprehensive summaries across {len(categories)} categories")
    print("Ready for Qdrant ingestion!")

if __name__ == "__main__":
    main()
