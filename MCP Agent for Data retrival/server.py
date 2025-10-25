import pathway as pw
from pathway.xpacks.llm.document_store import DocumentStore
from pathway.xpacks.llm.embedders import OpenAIEmbedder
from pathway.xpacks.llm.splitters import TokenCountSplitter
from pathway.xpacks.llm.parsers import ParseUnstructured
from pathway.stdlib.indexing import BruteForceKnnFactory, TantivyBM25Factory, HybridIndexFactory
from pathway.xpacks.llm.mcp_server import PathwayMcp
from pathway.engine import BruteForceKnnMetricKind
import os

# ============================================
# STEP 1: Load Data Sources
# ============================================
print("Loading data sources from 'data/' directory...")

# Read all files from the data directory
sources = pw.io.fs.read(
    path="data/",           # Path to your documents
    format="binary",        # Read as binary to support multiple formats
    with_metadata=True      # Include file metadata (filename, timestamp, etc.)
)

print("✓ Data sources loaded")


# ============================================
# STEP 2: Configure Embedder (OpenAI)
# ============================================
print("Setting up OpenAI embedder...")

# Create embedder using OpenAI's text-embedding-ada-002 model
# This converts text chunks into vector embeddings for semantic search
embedder = OpenAIEmbedder(
    model="text-embedding-ada-002",
    api_key=os.environ.get("OPENAI_API_KEY"),  # Requires OPENAI_API_KEY env variable
    cache_strategy=pw.udfs.DiskCache()          # Cache embeddings to avoid redundant API calls
)

print("✓ Embedder configured")


# ============================================
# STEP 3: Configure Text Splitter
# ============================================
print("Setting up text splitter...")

# Split documents into chunks of 250-600 tokens
# This ensures better retrieval precision by working with manageable text segments
splitter = TokenCountSplitter(
    min_tokens=250,     # Minimum chunk size
    max_tokens=600      # Maximum chunk size
)

print("✓ Splitter configured")


# ============================================
# STEP 4: Configure Parser
# ============================================
print("Setting up document parser...")

# Parser extracts readable text from various file formats
# ParseUnstructured handles txt, pdf, docx, etc.
parser = ParseUnstructured()

print("✓ Parser configured")


# ============================================
# STEP 5: Build KNN (Vector) Index
# ============================================
print("Building KNN vector index...")

# Creates a vector search index using cosine similarity
# This enables semantic search (finding documents by meaning)
knn_index = BruteForceKnnFactory(
    reserved_space=1000,                        # Pre-allocate space for 1000 documents
    embedder=embedder,                          # Use the OpenAI embedder
    metric=BruteForceKnnMetricKind.COS          # Cosine similarity metric
)

print("✓ KNN index configured")


# ============================================
# STEP 6: Build BM25 (Keyword) Index
# ============================================
print("Building BM25 keyword index...")

# Creates a traditional keyword-based search index
# This enables exact term matching (like a search engine)
bm25_index = TantivyBM25Factory()

print("✓ BM25 index configured")


# ============================================
# STEP 7: Create Hybrid Retriever
# ============================================
print("Creating hybrid retriever (combining KNN + BM25)...")

# Combines both semantic (vector) and keyword (BM25) search
# Results from both methods are merged for best accuracy
retriever_factory = HybridIndexFactory(
    retriever_factories=[knn_index, bm25_index]
)

print("✓ Hybrid retriever configured")


# ============================================
# STEP 8: Build Document Store
# ============================================
print("Building document store...")

# The central store that manages all documents
# It parses, splits, embeds, and indexes everything
document_store = DocumentStore(
    docs=sources,                       # Input: file sources
    parser=parser,                      # How to extract text
    splitter=splitter,                  # How to chunk text
    retriever_factory=retriever_factory # How to search/retrieve
)

print("✓ Document store built")


# ============================================
# STEP 9: Create and Start MCP Server
# ============================================
print("Starting Pathway MCP Server on localhost:8068...")

# Launch the MCP server over HTTP
# This exposes the document store as a queryable tool
pathway_mcp_server = PathwayMcp(
    name="Document Search MCP Server",  # Name of your server
    transport="streamable-http",        # HTTP transport protocol
    host="localhost",                   # Run on localhost
    port=8068,                          # Port number
    serve=[document_store]              # Expose the document store
)

print("✓ MCP Server started successfully!")
print("Server is running at: http://localhost:8068/mcp/")
print("Use the client to query documents.\n")

# Run the Pathway pipeline
# This keeps the server alive and processes data in real-time
pw.run(
    monitoring_level=pw.MonitoringLevel.NONE,  # Disable verbose monitoring
    terminate_on_error=False                    # Keep running even if errors occur
)
print(">>> Server has exited or finished running")

