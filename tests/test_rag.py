import pytest
from app.rag.ingestion import load_all_industrial_documents, DOCS_DIR
from app.rag.retrieval import HybridIndustrialRetriever

def test_document_ingestion():
    chunks = load_all_industrial_documents(DOCS_DIR)
    assert len(chunks) >= 5
    
    doc_ids = {c.document_id for c in chunks}
    assert "OEM-MAN-P104-REV4" in doc_ids
    assert "SOP-042-REV5" in doc_ids
    assert "SOP-088-REV3" in doc_ids
    assert "INC-2024-03-P104" in doc_ids

def test_hybrid_retrieval():
    retriever = HybridIndustrialRetriever(DOCS_DIR)
    
    # Query for LOTO
    results = retriever.retrieve("What are the mandatory Lockout Tagout procedures?", top_k=2)
    assert len(results) > 0
    top_doc = results[0]
    assert "SOP-042" in top_doc["document_id"] or "SOP-088" in top_doc["document_id"]
    
    # Query for Pump P-104 vibration limits
    p104_results = retriever.retrieve("Pump P-104 vibration ISO limits", asset_id="P-104", top_k=2)
    assert len(p104_results) > 0
    assert "P104" in p104_results[0]["document_id"]
