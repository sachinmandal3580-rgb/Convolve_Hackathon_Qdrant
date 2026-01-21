"""
Data Ingestion Pipeline - Handles adding data to Qdrant
"""

import json
from datetime import datetime
from embeddings import EmbeddingGenerator
from qdrant_manager import HealthcareQdrantManager

class DataIngestionPipeline:
    def __init__(self, qdrant_manager):
        """
        Initialize ingestion pipeline
        
        Args:
            qdrant_manager: HealthcareQdrantManager instance
        """
        self.qm = qdrant_manager
        self.embedder = EmbeddingGenerator()
    
    def ingest_patient_report(self, patient_id, report_data):
        """
        Ingest a patient report
        
        Args:
            patient_id: Patient identifier (e.g., "P001")
            report_data: Dict containing report information
                {
                    "text": "Report text...",
                    "report_type": "consultation",
                    "doctor": "Dr. Smith",
                    "diagnosis": "...",
                    "medications": [...]
                }
        
        Returns:
            Point ID of the ingested record
        """
        # Generate embedding from text
        embedding = self.embedder.encode_text(report_data["text"])
        
        # Add to Qdrant
        point_id = self.qm.add_patient_report(
            patient_id=patient_id,
            report_text=report_data["text"],
            embedding=embedding,
            metadata={
                "report_type": report_data.get("report_type", "general"),
                "doctor": report_data.get("doctor", "unknown"),
                "diagnosis": report_data.get("diagnosis", ""),
                "medications": report_data.get("medications", [])
            }
        )
        
        print(f"Ingested report: {point_id[:8]}...")
        return point_id
    
    def ingest_medical_image(self, patient_id, image_data):
        """
        Ingest a medical image
        
        Args:
            patient_id: Patient identifier
            image_data: Dict containing image information
                {
                    "path": "path/to/image.jpg",
                    "modality": "X-ray",
                    "body_part": "chest",
                    "findings": "..."
                }
        
        Returns:
            Point ID of the ingested record
        """
        # Generate image embedding
        embedding = self.embedder.encode_image(image_data["path"])
        
        # Add to Qdrant
        point_id = self.qm.add_medical_image(
            patient_id=patient_id,
            image_path=image_data["path"],
            embedding=embedding,
            metadata={
                "modality": image_data.get("modality", "unknown"),
                "body_part": image_data.get("body_part", ""),
                "findings": image_data.get("findings", "")
            }
        )
        
        print(f"Ingested image: {point_id[:8]}...")
        return point_id
    
    def batch_ingest(self, patient_id, data_file):
        """
        Batch ingest from JSON file
        
        Args:
            patient_id: Patient identifier
            data_file: Path to JSON file with structure:
                {
                    "reports": [...],
                    "images": [...]
                }
        """
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        print(f"Batch ingesting data for patient {patient_id}...")
        
        # Ingest reports
        for i, report in enumerate(data.get("reports", []), 1):
            print(f"  Report {i}/{len(data.get('reports', []))}...", end=" ")
            self.ingest_patient_report(patient_id, report)
        
        # Ingest images
        for i, image in enumerate(data.get("images", []), 1):
            print(f"  Image {i}/{len(data.get('images', []))}...", end=" ")
            self.ingest_medical_image(patient_id, image)
        
        print(f"Batch ingestion complete!")