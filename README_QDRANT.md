# Feeding Tenant Law Knowledge into Qdrant

This guide shows how to ingest the unified tenant law knowledge base into Qdrant for semantic search.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Qdrant (Local)

Using Docker (recommended):
```bash
docker run -p 6333:6333 qdrant/qdrant
```

Or download from: https://github.com/qdrant/qdrant/releases

### 3. Run the Ingestion Script

```bash
python qdrant_ingestion.py
```

This will:
- Create a collection named `tenant_law`
- Generate embeddings for all 56 knowledge chunks
- Upload the data to Qdrant
- Run example searches

## Configuration Options

### Local vs Cloud Qdrant

**Local (default):**
```python
qdrant = TenantLawQdrant()
```

**Cloud:**
Create a `.env` file:
```
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key
```

Then update the script:
```python
qdrant = TenantLawQdrant(
    qdrant_url=os.getenv("QDRANT_URL"),
    qdrant_api_key=os.getenv("QDRANT_API_KEY")
)
```

### Embedding Models

**Default (free, local):**
- `all-MiniLM-L6-v2` - 384 dimensions, fast, good for English

**Alternative models:**
```python
# For better quality (larger, slower)
qdrant = TenantLawQdrant(embedding_model="all-mpnet-base-v2")

# For multilingual support
qdrant = TenantLawQdrant(embedding_model="paraphrase-multilingual-MiniLM-L12-v2")
```

**OpenAI embeddings:**
Modify the script to use OpenAI's API:
```python
# pip install openai
from openai import OpenAI

client = OpenAI()
embedding = client.embeddings.create(
    input="text",
    model="text-embedding-3-small"
)
```

## Usage Examples

### Basic Search
```python
results = qdrant.search("How much deposit can landlord charge?")
```

### Filtered Search
```python
# By category
results = qdrant.search(
    "notice period",
    category_filter="Notice Periods"
)

# By risk level
results = qdrant.search(
    "problems for expats",
    risk_filter="red flag"
)

# Combined filters
results = qdrant.search(
    "repairs",
    category_filter="Repairs & Maintenance",
    risk_filter="caution"
)
```

### Integration in Your App

```python
from qdrant_ingestion import TenantLawQdrant

# Initialize
qdrant = TenantLawQdrant()

# Search function
def get_tenant_advice(query: str, max_results: int = 3):
    results = qdrant.search(query, limit=max_results)
    
    advice = []
    for r in results:
        advice.append({
            'title': r['title'],
            'rule': r['key_rule'],
            'implication': r['expat_implication'],
            'risk': r['risk_level']
        })
    
    return advice
```

## Data Structure

Each chunk in Qdrant contains:
- `vector`: The embedding (384 dimensions)
- `payload`: 
  - `title`: Topic title
  - `category`: One of 8 standardized categories
  - `key_rule`: Main legal rule in plain language
  - `expat_implication`: Specific advice for expats
  - `risk_level`: normal / caution / red flag
  - `source_document`: Original PDF source
  - `text_for_search`: Combined text for embedding

## Performance

- **56 chunks**: Small enough for instant search
- **384 dimensions**: Efficient storage and fast queries
- **Cosine similarity**: Good for semantic matching
- **Local setup**: No API costs, full privacy

## Next Steps

1. Add more web content from `places_to_summarize.txt`
2. Implement a simple web interface
3. Add caching for frequent queries
4. Consider adding German language support

## Troubleshooting

**Connection Error:**
- Make sure Qdrant is running on localhost:6333
- Check if Docker container is up: `docker ps`

**Memory Issues:**
- Use smaller batch sizes in `upload_knowledge_base()`
- Consider cloud Qdrant for larger datasets

**Poor Search Results:**
- Try different embedding models
- Improve text combination in `prepare_text_for_embedding()`
- Add more relevant content to the knowledge base
