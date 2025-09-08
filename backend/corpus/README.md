# Corpus Directory

This directory is where you should place your documents for ingestion into the FAISS vector index.

## Supported File Types

- **PDF files** (`.pdf`) - Text will be extracted automatically
- **Markdown files** (`.md`, `.markdown`) - Converted to text
- **HTML files** (`.html`, `.htm`) - Text content extracted

## Usage

1. **Add your documents** to this directory (you can create subdirectories)
2. **Run ingestion**: `python -m app.rag.ingest --input ./corpus --rebuild`
3. **Start the chatbot**: The indexed documents will be available for queries

## Example Structure

```
corpus/
├── land-indicators/
│   ├── global-report-2023.pdf
│   ├── methodology.md
│   └── country-profiles/
│       ├── africa.pdf
│       └── asia.pdf
├── unccd-documents/
│   ├── convention-text.html
│   └── strategic-framework.pdf
└── technical-reports/
    ├── remote-sensing.pdf
    └── field-studies.md
```

## Notes

- The ingestion process will recursively scan all subdirectories
- Metadata (country, year, etc.) can be extracted from filenames or content
- Large documents are automatically chunked for better retrieval

