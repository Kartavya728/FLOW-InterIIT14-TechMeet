import pathway as pw
from pathway.xpacks.llm.document_store import DocumentStore
from pathway.xpacks.llm.splitters import TokenCountSplitter
from pathway.xpacks.llm.parsers import ParseUnstructured
from pathway.stdlib.indexing import BruteForceKnnFactory, TantivyBM25Factory, HybridIndexFactory
from pathway.xpacks.llm.mcp_server import PathwayMcp
from pathway.engine import BruteForceKnnMetricKind
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np

load_dotenv() 

# ============================================
# LOCAL EMBEDDER CLASS
# ============================================
class LocalEmbedder:
    """
    Local embedding model using sentence-transformers
    This replaces OpenAIEmbedder and runs completely offline
    """
    def __init__(self, model_name='all-MiniLM-L6-v2', cache_strategy=None):
        print(f"Loading local embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.dimensions = self.model.get_sentence_embedding_dimension()
        self.cache_strategy = cache_strategy
        print(f"✓ Local model loaded ({self.dimensions} dimensions)")
    
    def __call__(self, text, **kwargs):
        """Generate embedding for a single text"""
        if isinstance(text, str):
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        return self.model.encode(text, convert_to_numpy=True).tolist()
    
    async def __wrapped__(self, text, **kwargs):
        """Async wrapper for compatibility with Pathway"""
        return self(text, **kwargs)
    
    def get_embedding_dimension(self):
        """Return embedding dimension"""
        return self.dimensions

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
# STEP 2: Configure Embedder (LOCAL)
# ============================================
print("Setting up local embedder...")

# Create embedder using local sentence-transformers model
# This runs completely offline and is FREE
embedder = LocalEmbedder(
    model_name='all-MiniLM-L6-v2',      # Fast, lightweight model (384 dimensions)
    cache_strategy=pw.udfs.DiskCache()   # Cache embeddings to avoid recomputation
)

print("✓ Embedder configured")

# ============================================
# STEP 3: Configure Text Splitter
# ============================================
print("Setting up text splitter...")

# Split documents into chunks of 250-600 tokens
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
parser = ParseUnstructured()

print("✓ Parser configured")

# ============================================
# STEP 5: Build KNN (Vector) Index
# ============================================
print("Building KNN vector index...")

# Creates a vector search index using cosine similarity
knn_index = BruteForceKnnFactory(
    reserved_space=1000,                        # Pre-allocate space for 1000 documents
    embedder=embedder,                          # Use the LOCAL embedder
    metric=BruteForceKnnMetricKind.COS          # Cosine similarity metric
)

print("✓ KNN index configured")

# ============================================
# STEP 6: Build BM25 (Keyword) Index
# ============================================
print("Building BM25 keyword index...")

# Creates a traditional keyword-based search index
bm25_index = TantivyBM25Factory()

print("✓ BM25 index configured")

# ============================================
# STEP 7: Create Hybrid Retriever
# ============================================
print("Creating hybrid retriever (combining KNN + BM25)...")

# Combines both semantic (vector) and keyword (BM25) search
retriever_factory = HybridIndexFactory(
    retriever_factories=[knn_index, bm25_index]
)

print("✓ Hybrid retriever configured")

# ============================================
# STEP 8: Build Document Store
# ============================================
print("Building document store...")

# The central store that manages all documents
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
pw.run(
    monitoring_level=pw.MonitoringLevel.NONE,  # Disable verbose monitoring
    terminate_on_error=False                    # Keep running even if errors occur
)
print(">>> Server has exited or finished running")
