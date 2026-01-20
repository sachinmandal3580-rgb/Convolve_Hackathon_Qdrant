from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.models import Filter, FieldCondition, Range
import uuid
from datetime import datetime

class HealthcareQdrantManager:
    def __init__(self, url="https://13a8ecee-942e-4041-896f-5665b4923c13.europe-west3-0.gcp.cloud.qdrant.io", api_key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.CTY7BW_2os8hoZyG2TEltYiq1YyU6BGX5KxvxxlK1xE'):
        self.client = QdrantClient(url=url, api_key=api_key)
        self.setup_collections()
    
    def setup_collections(self):
        collections = {
            "patient_reports": 768,  # Text embeddings
            "medical_images": 512,   # Image embeddings
            "patient_timeline": 768  # Temporal events
        }
        
        for name, size in collections.items():
            if not self.client.collection_exists(name):
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=size,
                        distance=Distance.COSINE
                    )
                )
                print(f"Created collection: {name}")
    
    def add_patient_report(self, patient_id, report_text, 
                          embedding, metadata):
        point_id = str(uuid.uuid4())
        
        payload = {
            "patient_id": patient_id,
            "text": report_text,
            "timestamp": datetime.now().isoformat(),
            "report_type": metadata.get("report_type", "general"),
            "doctor": metadata.get("doctor", "unknown"),
            **metadata
        }
        
        self.client.upsert(
            collection_name="patient_reports",
            points=[PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )]
        )
        return point_id
    
    def add_medical_image(self, patient_id, image_path, 
                         embedding, metadata):
        point_id = str(uuid.uuid4())
        
        payload = {
            "patient_id": patient_id,
            "image_path": image_path,
            "timestamp": datetime.now().isoformat(),
            "modality": metadata.get("modality", "unknown"),
            "body_part": metadata.get("body_part", ""),
            **metadata
        }
        
        self.client.upsert(
            collection_name="medical_images",
            points=[PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )]
        )
        return point_id
    
    def search_patient_history(self, patient_id, query_vector, 
                               limit=5, filters=None):
        search_filter = Filter(
            must=[FieldCondition(
                key="patient_id",
                match={"value": patient_id}
            )]
        )
        
        if filters:
            if "date_range" in filters:
                search_filter.must.append(
                    FieldCondition(
                        key="timestamp",
                        range=Range(
                            gte=filters["date_range"]["start"],
                            lte=filters["date_range"]["end"]
                        )
                    )
                )
        
        results = self.client.search(
            collection_name="patient_reports",
            query_vector=query_vector,
            query_filter=search_filter,
            limit=limit
        )
        return results