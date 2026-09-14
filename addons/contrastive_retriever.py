"""FAISS retriever that adds contrastive (least similar) documents.

Implements the Contrastive Examples idea from Yazan, Verberne & Situmeang,
"Improving RAG for Personalization with Author Features and Contrastive
Examples" (arXiv:2504.08745), adapted to relevancy calibration: alongside the
top-k relevant documents, the least similar documents are included in the
prompt, explicitly labeled as contrast. Seeing clearly irrelevant material
helps the LLM judge whether the relevant candidates actually answer the
question, sharpening the [NO_RAG_ANSWER] abstention decision.

The index is built at startup by embedding all documents under the configured
``source`` folder (endpoints.yml ``vector_store`` block), because Rasa only
bakes a train-time index into the model for the built-in "faiss" type.
"""

import hashlib
import random
from typing import Any, Dict, List, Text, Tuple

import structlog
from rasa.core.information_retrieval import SearchResultList
from rasa.core.information_retrieval.faiss import DEFAULT_SEARCH_K, FAISS_Store
from rasa.core.information_retrieval.information_retrieval import (
    InformationRetrievalException,
)
from rasa.core.information_retrieval.models import Document
from rasa.shared.providers.embedding.embedding_utils import aembed_query
from rasa.utils.endpoints import EndpointConfig

CONTRAST_METADATA_KEY = "contrast"
DEFAULT_CONTRAST_K = 2
DEFAULT_SOURCE = "./docs"

# How contrast documents are chosen from the similarity ranking (top-k excluded):
#   bottom: the least similar documents (original design)
#   random: a per-query deterministic random sample of the non-top documents
#   next:   the documents ranked directly below the top-k cut-off (hard negatives)
CONTRAST_MODE_BOTTOM = "bottom"
CONTRAST_MODE_RANDOM = "random"
CONTRAST_MODE_NEXT = "next"
CONTRAST_MODES = (CONTRAST_MODE_BOTTOM, CONTRAST_MODE_RANDOM, CONTRAST_MODE_NEXT)
DEFAULT_CONTRAST_MODE = CONTRAST_MODE_BOTTOM
DEFAULT_CONTRAST_SEED = 0
# Number of relevant documents passed to the LLM (Rasa's default is 4).
DEFAULT_TOP_K = DEFAULT_SEARCH_K

structlogger = structlog.get_logger()


class ContrastiveFAISS(FAISS_Store):
    """In-memory FAISS store returning top-k relevant + bottom-k contrast docs."""

    def __init__(self, embeddings: Any) -> None:
        super().__init__(embeddings)
        self.contrast_k = DEFAULT_CONTRAST_K
        self.contrast_mode = DEFAULT_CONTRAST_MODE
        self.contrast_seed = DEFAULT_CONTRAST_SEED
        self.top_k = DEFAULT_TOP_K

    def connect(self, config: EndpointConfig) -> None:
        source = DEFAULT_SOURCE
        if config is not None:
            source = config.kwargs.get("source", DEFAULT_SOURCE)
            self.top_k = int(config.kwargs.get("top_k", DEFAULT_TOP_K))
            self.contrast_k = int(
                config.kwargs.get("contrast_k", DEFAULT_CONTRAST_K)
            )
            self.contrast_mode = str(
                config.kwargs.get("contrast_mode", DEFAULT_CONTRAST_MODE)
            ).lower()
            self.contrast_seed = int(
                config.kwargs.get("contrast_seed", DEFAULT_CONTRAST_SEED)
            )
        if self.contrast_mode not in CONTRAST_MODES:
            raise InformationRetrievalException(
                f"Unknown contrast_mode '{self.contrast_mode}', "
                f"expected one of {CONTRAST_MODES}."
            )
        structlogger.info(
            "contrastive_faiss.connect",
            source=source,
            top_k=self.top_k,
            contrast_k=self.contrast_k,
            contrast_mode=self.contrast_mode,
            contrast_seed=self.contrast_seed,
        )
        # The e2e runner calls connect() on the same instance for every test
        # case, and FAISS_Store._add_embeddings appends to the existing index.
        # Without a reset the index holds n copies of every document after n
        # connects and the top-k degenerates to k copies of one document
        # (observed 2026-09-14). Start from an empty index every time.
        self._index = None
        self.documents = {}
        self.index_to_docstore_id = {}
        self._build_enterprise_index(source)
        structlogger.info(
            "contrastive_faiss.index_built",
            vectors=self._index.ntotal if self._index is not None else 0,
            documents=len(self.documents),
        )

    def _select_contrast(
        self, ranked: List[Tuple[Document, float]], query: Text
    ) -> List[Tuple[Document, float]]:
        """Pick contrast_k entries from the ranking below the top-k cut-off."""
        if self.contrast_k <= 0:
            return []
        candidates = ranked[self.top_k :]
        if self.contrast_mode == CONTRAST_MODE_NEXT:
            return candidates[: self.contrast_k]
        if self.contrast_mode == CONTRAST_MODE_RANDOM:
            # Seeded by query text so the same question gets the same sample
            # across runs; the seed option lets an experiment vary the sample.
            digest = hashlib.sha256(
                f"{self.contrast_seed}:{query}".encode("utf-8")
            ).hexdigest()
            rng = random.Random(int(digest[:16], 16))
            k = min(self.contrast_k, len(candidates))
            return rng.sample(candidates, k)
        # bottom: least similar documents overall, in ranking order
        return candidates[-self.contrast_k :]

    async def search(
        self, query: Text, tracker_state: Dict[str, Any], threshold: float = 0.0
    ) -> SearchResultList:
        if self._index is None:
            raise InformationRetrievalException()
        try:
            embedding = await aembed_query(self.embeddings, query)
            ranked = self._search_by_vector(embedding, k=len(self.documents))
        except Exception as exc:
            raise InformationRetrievalException from exc

        top = [doc for doc, _ in ranked[: self.top_k]]
        top_sources = [d.metadata.get("source") for d in top]
        top_scores = [round(float(s), 4) for _, s in ranked[: self.top_k]]
        if len(set(top_sources)) < len(top_sources):
            structlogger.warning(
                "contrastive_faiss.duplicate_top_documents",
                query=query,
                top=top_sources,
                index_size=self._index.ntotal,
            )
        contrast = [
            Document(
                text=doc.text,
                metadata={**doc.metadata, CONTRAST_METADATA_KEY: True},
            )
            for doc, _ in self._select_contrast(ranked, query)
        ]
        structlogger.info(
            "contrastive_faiss.search",
            query=query,
            mode=self.contrast_mode,
            top=top_sources,
            top_scores=top_scores,
            contrast=[d.metadata.get("source") for d in contrast],
            contrast_scores=[
                round(float(s), 4) for _, s in self._select_contrast(ranked, query)
            ],
        )
        return SearchResultList.from_document_list(top + contrast)
