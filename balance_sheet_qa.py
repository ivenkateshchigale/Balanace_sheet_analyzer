"""
Balance Sheet QA System (OpenRouter version)
=============================================
Uses OpenRouter API — supports Claude, GPT-4, Gemini, Llama, and more.

Pipeline:
  1. Parse  → extract text from PDF/text
  2. Chunk  → split into overlapping segments
  3. Embed  → encode chunks with sentence-transformers
  4. Index  → store in FAISS vector index
  5. Query  → embed question, retrieve top-k chunks
  6. Answer → send context + question to LLM via OpenRouter
"""

import os
import textwrap
import numpy as np
import pdfplumber
from openai import OpenAI

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠  FAISS not available – falling back to cosine similarity search.")

from sentence_transformers import SentenceTransformer

# ── Constants ──────────────────────────────────────────────────────────────────
EMBED_MODEL      = "all-MiniLM-L6-v2"
MAX_TOKENS       = 1024
TOP_K            = 5
CHUNK_SIZE       = 300
CHUNK_OVERLAP    = 50

# ── Pick your model from https://openrouter.ai/models ─────────────────────────
OPENROUTER_MODEL = os.environ.get(
    "OPENROUTER_MODEL",
    "meta-llama/llama-3-70b-instruct"
)
# OPENROUTER_MODEL = "openai/gpt-4o-mini"            # GPT-4o Mini
# OPENROUTER_MODEL = "google/gemini-pro-1.5"        # Gemini Pro
# OPENROUTER_MODEL = "mistralai/mixtral-8x7b-instruct"  # Mixtral

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"


# ══════════════════════════════════════════════════════════════════════════════
# 1. DOCUMENT PARSING
# ══════════════════════════════════════════════════════════════════════════════

def parse_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    clean = [str(cell).strip() if cell else "" for cell in row]
                    text_parts.append("  |  ".join(clean))
            raw = page.extract_text()
            if raw:
                text_parts.append(raw)
    return "\n".join(text_parts)


def parse_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_document(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        print(f"📄 Parsing PDF: {path}")
        return parse_pdf(path)
    else:
        print(f"📄 Reading text file: {path}")
        return parse_text(path)


# ══════════════════════════════════════════════════════════════════════════════
# 2. CHUNKING
# ══════════════════════════════════════════════════════════════════════════════

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        end   = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk.strip())
        if end == len(words):
            break
        start += chunk_size - overlap
    print(f"✂  Created {len(chunks)} chunks")
    return chunks


# ══════════════════════════════════════════════════════════════════════════════
# 3 & 4. EMBEDDING + INDEXING
# ══════════════════════════════════════════════════════════════════════════════

class VectorStore:
    def __init__(self):
        print(f"🔢 Loading embedding model: {EMBED_MODEL}")
        self.model  = SentenceTransformer(EMBED_MODEL)
        self.chunks : list[str] = []
        self.index  = None
        self.matrix = None

    def build(self, chunks: list[str]):
        self.chunks = chunks
        print("⚙  Embedding chunks …")
        embeddings = self.model.encode(chunks, show_progress_bar=True,
                                       normalize_embeddings=True)
        if FAISS_AVAILABLE:
            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dim)
            self.index.add(embeddings.astype("float32"))
            print(f"✅ FAISS index built — {self.index.ntotal} vectors")
        else:
            self.matrix = embeddings
            print(f"✅ Numpy index built — {len(chunks)} vectors")

    def search(self, query: str, top_k: int = TOP_K) -> list[str]:
        q_vec = self.model.encode([query], normalize_embeddings=True)
        if FAISS_AVAILABLE:
            _, indices = self.index.search(q_vec.astype("float32"), top_k)
            return [self.chunks[i] for i in indices[0] if i < len(self.chunks)]
        else:
            scores  = (self.matrix @ q_vec.T).flatten()
            top_idx = np.argsort(scores)[::-1][:top_k]
            return [self.chunks[i] for i in top_idx]


# ══════════════════════════════════════════════════════════════════════════════
# 5 & 6. RETRIEVAL + ANSWER GENERATION
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """\
You are an expert financial analyst specializing in reading and interpreting
corporate balance sheets. You will be given relevant excerpts from a balance
sheet and must answer the user's question accurately.

Guidelines:
- Use only the provided context. Do NOT hallucinate figures.
- Cite specific line items or numbers when relevant.
- If the context is insufficient, say so clearly.
- Format currency values clearly (e.g., ₹ 1,234.56 Cr or $1.2M).
- Keep answers concise but complete.
"""


class BalanceSheetQA:
    def __init__(self):
        self.store  = VectorStore()

        if not OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required. "
                "Set it to your OpenRouter API key before running the script."
            )

        # ── OpenRouter client (OpenAI-compatible) ──────────────────────────
        self.client = OpenAI(
            base_url    = OPENROUTER_API_BASE,
            api_key     = OPENROUTER_API_KEY,
            max_retries = 3,
        )

        self.history: list[dict] = []   # conversation memory

    def load(self, path: str):
        raw_text = load_document(path)
        chunks   = chunk_text(raw_text)
        self.store.build(chunks)
        print("🚀 System ready. Ask questions about the balance sheet!\n")

    def load_from_text(self, text: str):
        chunks = chunk_text(text)
        self.store.build(chunks)
        print("🚀 System ready. Ask questions about the balance sheet!\n")

    def ask(self, question: str, top_k: int = TOP_K) -> str:
        # Retrieve relevant chunks
        relevant_chunks = self.store.search(question, top_k=top_k)
        context = "\n\n---\n\n".join(relevant_chunks)

        user_message = f"""Balance Sheet Excerpts:
<context>
{context}
</context>

Question: {question}"""

        self.history.append({"role": "user", "content": user_message})

        # ── OpenRouter API call (OpenAI chat completions format) ───────────
        try:
            response = self.client.chat.completions.create(
                model       = OPENROUTER_MODEL,
                max_tokens  = MAX_TOKENS,
                messages    = [{"role": "system", "content": SYSTEM_PROMPT}] + self.history,
                # Optional: show your app name on openrouter.ai/activity
                extra_headers = {
                    "HTTP-Referer": "https://my-balance-sheet-qa.app",
                    "X-Title":      "Balance Sheet QA",
                }
            )
        except Exception as exc:
            raise RuntimeError(f"OpenRouter API call failed: {exc}") from exc

        if response is None:
            raise RuntimeError("OpenRouter API returned no response.")

        response_error = getattr(response, "error", None)
        if response_error:
            if isinstance(response_error, dict):
                message = response_error.get("message", str(response_error))
                code = response_error.get("code")
                raise RuntimeError(
                    f"OpenRouter API returned an error: {message} "
                    f"(code={code}). Full response: {response}"
                )
            raise RuntimeError(
                f"OpenRouter API returned an error: {response_error}. "
                f"Full response: {response}"
            )

        choices = getattr(response, "choices", None)
        if not choices or len(choices) == 0:
            raise RuntimeError(
                "OpenRouter API returned an empty choices list. "
                f"Full response: {response}"
            )

        choice = choices[0]
        answer = None

        if hasattr(choice, "message") and choice.message is not None:
            answer = getattr(choice.message, "content", None)
            if answer is None and isinstance(choice.message, dict):
                answer = choice.message.get("content")

        if answer is None and isinstance(choice, dict):
            answer = choice.get("message", {}).get("content") or choice.get("text")

        if not answer:
            answer = getattr(response, "output_text", None) or getattr(response, "text", None)

        if not answer:
            raise RuntimeError(
                "Unable to parse assistant text from OpenRouter response. "
                f"Full response: {response}"
            )

        self.history.append({"role": "assistant", "content": answer})
        return answer

    def reset_history(self):
        self.history = []
        print("🔄 Conversation history cleared.")


# ══════════════════════════════════════════════════════════════════════════════
# SAMPLE BALANCE SHEET
# ══════════════════════════════════════════════════════════════════════════════

SAMPLE_BALANCE_SHEET = """
INFOSYS LIMITED
Consolidated Balance Sheet as at March 31, 2024
(in ₹ crore)

ASSETS
Non-current assets
  Property, plant and equipment          4,846
  Right-of-use assets                    7,623
  Goodwill                               8,072
  Other intangible assets                  412
  Financial assets
    Investments                         19,847
    Loans                                  143
    Other financial assets               1,284
  Deferred tax assets (net)              2,491
  Income tax assets (net)                8,173
  Other non-current assets               2,006
  Total non-current assets              54,897

Current assets
  Financial assets
    Investments                         15,064
    Trade receivables                   26,248
    Cash and cash equivalents           12,314
    Loans                                  157
    Other financial assets               5,423
  Income tax assets (net)                  982
  Other current assets                   5,876
  Total current assets                  66,064

TOTAL ASSETS                           120,961

EQUITY AND LIABILITIES
Equity
  Equity share capital                     207
  Other equity                           86,743
  Total equity                           86,950
  Non-controlling interests                 641
  Total equity (including NCI)           87,591

Non-current liabilities
  Financial liabilities
    Lease liabilities                    6,481
    Other financial liabilities            302
  Deferred tax liabilities (net)           412
  Other non-current liabilities          1,048
  Total non-current liabilities          8,243

Current liabilities
  Financial liabilities
    Lease liabilities                    1,934
    Trade payables                       1,204
    Other financial liabilities         14,267
  Other current liabilities              5,481
  Income tax liabilities (net)           1,823
  Provisions                               418
  Total current liabilities             25,127

TOTAL EQUITY AND LIABILITIES           120,961

Key Financial Ratios:
  Current Ratio         = 2.63
  Debt-to-Equity Ratio  = 0.10
  Return on Equity      = 30.2%
  Book Value per Share  = ₹ 418.60
"""


# ══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE CLI
# ══════════════════════════════════════════════════════════════════════════════

def run_cli(path: str = None):
    qa = BalanceSheetQA()
    if path:
        qa.load(path)
    else:
        print("ℹ  No file provided — loading sample balance sheet.\n")
        qa.load_from_text(SAMPLE_BALANCE_SHEET)

    print(f"🤖 Using model: {OPENROUTER_MODEL}")
    print("Commands: ask your question | 'reset' to clear history | 'quit' to exit\n")
    print("─" * 60)

    while True:
        try:
            question = input("\n❓ Your question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break

        if not question:
            continue
        if question.lower() == "quit":
            print("👋 Goodbye!")
            break
        if question.lower() == "reset":
            qa.reset_history()
            continue

        print("\n🤔 Thinking …")
        answer = qa.ask(question)
        print(f"\n💡 Answer:\n{textwrap.fill(answer, width=72)}\n")
        print("─" * 60)


if __name__ == "__main__":
    import sys
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_cli(file_path)
