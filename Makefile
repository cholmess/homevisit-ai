# Tenant Law Knowledge Base - Makefile

.PHONY: help install process merge ingest clean test

# Default target
help:
	@echo "Tenant Law Knowledge Base Commands:"
	@echo ""
	@echo "  install     Install Python dependencies"
	@echo "  process     Process all PDFs and create summaries"
	@echo "  merge       Merge datasets into unified knowledge base"
	@echo "  ingest      Ingest knowledge into Qdrant"
	@echo "  clean       Clean generated files"
	@echo "  test        Run basic tests"
	@echo ""
	@echo "Full pipeline: install -> process -> merge -> ingest"

# Install dependencies
install:
	pip install -r requirements.txt

# Process all documents
process:
	@echo "Processing basic tenant law..."
	python src/processing/process_tenant_law.py
	@echo ""
	@echo "Processing comprehensive tenant law..."
	python src/processing/process_all_tenant_docs.py

# Merge knowledge bases
merge:
	@echo "Merging knowledge bases..."
	python src/knowledge/merge_tenant_knowledge.py

# Ingest into Qdrant
ingest:
	@echo "Ingesting into Qdrant..."
	@echo "Make sure Qdrant is running: docker run -p 6333:6333 qdrant/qdrant"
	python src/ingestion/qdrant_ingestion.py

# Full pipeline
all: install process merge ingest

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -rf data/processed/*.json
	rm -f pdf_extraction_summary.json
	@echo "Clean!"

# Test basic functionality
test:
	@echo "Testing configuration..."
	python -c "from config.config import *; print('Config OK')"
	@echo "Testing imports..."
	python -c "import sys; sys.path.append('src'); from processing.process_tenant_law import create_summaries; print('Imports OK')"

# Start Qdrant locally
qdrant-start:
	docker run -p 6333:6333 qdrant/qdrant

# Show project structure
tree:
	@echo "Project Structure:"
	@tree -I '__pycache__|*.pyc|.git' --dirsfirst

# Quick stats
stats:
	@echo "Knowledge Base Stats:"
	@if [ -f data/processed/unified_tenant_law_knowledge.json ]; then \
		python -c "import json; data=json.load(open('data/processed/unified_tenant_law_knowledge.json')); print(f'Total chunks: {data[\"metadata\"][\"total_chunks\"]}'); [print(f'{cat}: {count}') for cat, count in data['metadata']['category_counts'].items()]"; \
	else \
		echo "Run 'make process && make merge' first"; \
	fi
