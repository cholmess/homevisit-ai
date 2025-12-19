# Tenant Law Knowledge Base

A comprehensive system for processing German tenancy law documents and creating a searchable knowledge base for expats using Qdrant vector database.

## Project Structure

```
homevisit-ai/
├── config/
│   └── config.py           # Centralized configuration
├── src/
│   ├── processing/         # PDF and document processing
│   │   ├── process_tenant_law.py
│   │   └── process_all_tenant_docs.py
│   ├── knowledge/          # Knowledge base creation and merging
│   │   └── merge_tenant_knowledge.py
│   └── ingestion/          # Qdrant vector database operations
│       └── qdrant_ingestion.py
├── data/
│   ├── raw/               # Raw documents (if needed)
│   └── processed/         # Generated JSON files
├── Context Documents/      # Source PDFs
├── scripts/               # CLI entry points (if needed)
├── requirements.txt       # Python dependencies
├── Makefile              # Command shortcuts
└── README.md             # This file
```

## Quick Start

### 1. Install Dependencies
```bash
make install
# or
pip install -r requirements.txt
```

### 2. Process Documents
```bash
make process
```
This will:
- Process the basic tenant law PDF
- Process all 12 specialized PDFs from Context Documents
- Generate structured summaries

### 3. Merge Knowledge Base
```bash
make merge
```
Creates a unified knowledge base with 56 deduplicated chunks.

### 4. Start Qdrant
```bash
make qdrant-start
```

### 5. Ingest into Qdrant
```bash
make ingest
```

## Available Commands

```bash
make help          # Show all available commands
make all           # Run full pipeline
make clean         # Clean generated files
make test          # Test basic functionality
make stats         # Show knowledge base statistics
make tree          # Show project structure
```

## Data Flow

1. **PDF Processing** (`src/processing/`)
   - Extract text from PDFs
   - Create structured summaries
   - Output: `data/processed/*.json`

2. **Knowledge Merging** (`src/knowledge/`)
   - Combine multiple datasets
   - Deduplicate content
   - Standardize categories
   - Output: `data/processed/unified_tenant_law_knowledge.json`

3. **Vector Ingestion** (`src/ingestion/`)
   - Generate embeddings
   - Upload to Qdrant
   - Enable semantic search

## Categories

The knowledge base is organized into 8 standardized categories:
- Contract Basics
- Deposits & Payments
- Rent & Costs
- Repairs & Maintenance
- Rights & Obligations
- Notice Periods
- Utility Costs
- Special Situations

## Configuration

All settings are centralized in `config/config.py`:
- File paths
- Qdrant connection settings
- Processing parameters
- Category definitions

## Usage Examples

### Python API
```python
from src.ingestion.qdrant_ingestion import TenantLawQdrant

# Initialize
qdrant = TenantLawQdrant()

# Search
results = qdrant.search("How much deposit can landlord charge?")

# Filtered search
results = qdrant.search(
    "repairs",
    category_filter="Repairs & Maintenance",
    risk_filter="caution"
)
```

### Command Line
```bash
# Run specific steps
python src/processing/process_all_tenant_docs.py
python src/knowledge/merge_tenant_knowledge.py
python src/ingestion/qdrant_ingestion.py
```

## Dependencies

- `qdrant-client` - Vector database client
- `sentence-transformers` - Text embeddings
- `PyMuPDF` - PDF processing (optional)
- `python-dotenv` - Environment variables

## Contributing

1. Add new processing scripts to `src/processing/`
2. Update configuration in `config/config.py`
3. Follow the existing structure and patterns
4. Update the Makefile if adding new commands

## License

[Add your license here]
