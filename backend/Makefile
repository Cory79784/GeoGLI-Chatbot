# UNCCD GeoGLI Chatbot Backend Makefile
# Simple commands for development and deployment

.PHONY: help install install-updated fix-deps ingest run clean test

help:
	@echo "Available commands:"
	@echo "  install         - Install Python dependencies (stable versions)"
	@echo "  install-updated - Install updated dependency versions"
	@echo "  fix-deps        - Fix huggingface_hub compatibility issue"
	@echo "  ingest          - Build/rebuild FAISS index from corpus directory"
	@echo "  run             - Start the FastAPI server"
	@echo "  clean           - Clean up generated files"
	@echo "  test            - Run basic health check test"

install:
	pip install -r requirements.txt

install-updated:
	pip install -r requirements-updated.txt

fix-deps:
	@echo "Fixing huggingface_hub compatibility issue..."
	pip install huggingface_hub==0.13.4 --force-reinstall

ingest:
	@if [ ! -d "corpus" ]; then \
		echo "Creating corpus directory..."; \
		mkdir -p corpus; \
		echo "Please add your PDF/Markdown/HTML documents to the corpus/ directory"; \
	fi
	python -m app.rag.ingest --input ./corpus --rebuild

run:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	@echo "Cleaning up..."
	rm -rf storage/faiss
	rm -rf __pycache__
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

test:
	@echo "Testing health endpoint..."
	@curl -s http://localhost:8000/health || echo "Server not running. Start with 'make run'"
