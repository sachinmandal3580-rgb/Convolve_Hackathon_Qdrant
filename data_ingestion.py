import json
from datetime import datetime
from embeddings import EmbeddingGenerator
from qdrant_manager import HealthcareQdrantManager

class DataIngestionPipeline:
    def __init__(self, qdrant_manager):
        self.qm = qdrant_manager
        self.embedder = EmbeddingGenerator()
    
    def ingest_patient_report(self, patient_id, report_data):
        """
        report_data = {
            "text": "Patient presents with...",
            "report_type": "consultation",
            "doctor": "Dr. Smith",
            "diagnosis": "Type 2 Diabetes",
            "medications": ["Metformin", "Insulin"]
        }
        """
        # Generate embedding
        embedding = self.embedder.encode_text(report_data["text"])
        
        # Add to Qdrant
        point_id = self.qm.add_patient_report(
            patient_id=patient_id,
            report_text=report_data["text"],
            embedding=embedding,
            metadata={
                "report_type": report_data.get("report_type"),
                "doctor": report_data.get("doctor"),
                "diagnosis": report_data.get("diagnosis"),
                "medications": report_data.get("medications", [])
            }
        )
        
        print(f"Ingested report: {point_id}")
        return point_id
    
    def ingest_medical_image(self, patient_id, image_data):
        """
        image_data = {
            "path": "path/to/xray.jpg",
            "modality": "X-ray",
            "body_part": "chest",
            "findings": "No acute findings"
        }
        """
        # Generate image embedding
        embedding = self.embedder.encode_image(image_data["path"])
        
        # Add to Qdrant
        point_id = self.qm.add_medical_image(
            patient_id=patient_id,
            image_path=image_data["path"],
            embedding=embedding,
            metadata={
                "modality": image_data.get("modality"),
                "body_part": image_data.get("body_part"),
                "findings": image_data.get("findings")
            }
        )
        
        print(f"Ingested image: {point_id}")
        return point_id
    
    def batch_ingest(self, patient_id, data_file):
        """Batch ingest from JSON file"""
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        for report in data.get("reports", []):
            self.ingest_patient_report(patient_id, report)
        
        for image in data.get("images", []):
            self.ingest_medical_image(patient_id, image)

# Example usage
if __name__ == "__main__":
    qm = HealthcareQdrantManager()
    pipeline = DataIngestionPipeline(qm)
    
    # Sample report
    report = {
        "text": "Patient presents with persistent cough and fever.",
        "report_type": "consultation",
        "doctor": "Dr. Sarah Johnson",
        "diagnosis": "Upper Respiratory Infection",
        "medications": ["Amoxicillin", "Cough syrup"]
    }
    
    pipeline.ingest_patient_report("P001", report)