import os
import re
import json
import glob
from typing import List, Dict, Any

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents")

class DocumentChunk:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        title: str,
        section: str,
        content: str,
        equipment_model: str,
        document_type: str,
        revision_date: str = "N/A"
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.title = title
        self.section = section
        self.content = content
        self.equipment_model = equipment_model
        self.document_type = document_type
        self.revision_date = revision_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "title": self.title,
            "section": self.section,
            "content": self.content,
            "equipment_model": self.equipment_model,
            "document_type": self.document_type,
            "revision_date": self.revision_date
        }

class DocumentParser:
    """Parses engineering manuals, SOPs, and incident records into section-grounded chunks."""
    
    @staticmethod
    def parse_markdown_manual(file_path: str) -> List[DocumentChunk]:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Extract frontmatter / metadata lines
        doc_id_match = re.search(r"\*\*Document ID\*\*:\s*([^\n\r]+)", text)
        doc_id = doc_id_match.group(1).strip() if doc_id_match else os.path.basename(file_path)
        
        equip_match = re.search(r"\*\*Asset Applicability\*\*:\s*([^\n\r]+)", text)
        equipment_model = equip_match.group(1).strip() if equip_match else "General Rotating Machinery"
        
        rev_match = re.search(r"\*\*Revision Date\*\*:\s*([^\n\r]+)", text)
        rev_date = rev_match.group(1).strip() if rev_match else "N/A"

        # First line usually main title
        lines = text.strip().split("\n")
        title = lines[0].replace("#", "").strip() if lines else "Manual"

        # Split into sections by markdown heading 2 (## )
        sections = re.split(r"\n##\s+", text)
        chunks = []
        
        for idx, sec in enumerate(sections):
            if idx == 0:
                # Header intro chunk
                content = sec.strip()
                if len(content) > 30:
                    chunks.append(DocumentChunk(
                        chunk_id=f"{doc_id}-SEC0",
                        document_id=doc_id,
                        title=title,
                        section="Header & Overview",
                        content=content,
                        equipment_model=equipment_model,
                        document_type="manual",
                        revision_date=rev_date
                    ))
            else:
                sec_lines = sec.strip().split("\n")
                section_title = sec_lines[0].strip()
                body = "\n".join(sec_lines[1:]).strip()
                if body:
                    chunks.append(DocumentChunk(
                        chunk_id=f"{doc_id}-SEC{idx}",
                        document_id=doc_id,
                        title=title,
                        section=section_title,
                        content=f"Section: {section_title}\n{body}",
                        equipment_model=equipment_model,
                        document_type="manual",
                        revision_date=rev_date
                    ))
        return chunks

    @staticmethod
    def parse_incident_json(file_path: str) -> List[DocumentChunk]:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        doc_id = data.get("document_id", os.path.basename(file_path))
        title = data.get("title", "Incident Record")
        equip = data.get("asset_model", data.get("asset_id", "General Equipment"))
        date = data.get("date", "N/A")

        symptoms = "\n- ".join(data.get("reported_symptoms", []))
        telemetry = json.dumps(data.get("sensor_telemetry_findings", {}), indent=2)
        actions = "\n- ".join(data.get("corrective_actions_taken", []))
        root_cause = data.get("root_cause_diagnosis", "")
        lessons = data.get("lessons_learned", "")

        content = (
            f"Title: {title}\n"
            f"Asset ID: {data.get('asset_id')}\n"
            f"Reported Symptoms:\n- {symptoms}\n\n"
            f"Sensor Telemetry Findings:\n{telemetry}\n\n"
            f"Root Cause Diagnosis:\n{root_cause}\n\n"
            f"Corrective Actions Taken:\n- {actions}\n\n"
            f"Lessons Learned:\n{lessons}"
        )

        return [DocumentChunk(
            chunk_id=f"{doc_id}-FULL",
            document_id=doc_id,
            title=title,
            section="Incident Report & Corrective History",
            content=content,
            equipment_model=equip,
            document_type="incident_record",
            revision_date=date
        )]

def load_all_industrial_documents(docs_dir: str) -> List[DocumentChunk]:
    """Scans and parses all markdown manuals, SOPs, and JSON incident reports."""
    all_chunks = []
    
    # Parse manuals & SOPs (.md)
    md_files = glob.glob(os.path.join(docs_dir, "**", "*.md"), recursive=True)
    for md_path in md_files:
        all_chunks.extend(DocumentParser.parse_markdown_manual(md_path))
        
    # Parse incident records (.json)
    json_files = glob.glob(os.path.join(docs_dir, "**", "*.json"), recursive=True)
    for json_path in json_files:
        all_chunks.extend(DocumentParser.parse_incident_json(json_path))
        
    return all_chunks
