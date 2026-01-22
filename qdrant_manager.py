"""
Qdrant Manager 
"""
import os
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct,
    Filter, 
    FieldCondition, 
    Range, 
    MatchValue,
    PayloadSchemaType
)
import uuid
from datetime import datetime
from dotenv import load_dotenv

class HealthcareQdrantManager:
    def __init__(self, url, api_key):
        
        """Initialize Qdrant client and setup collections"""
        
        url=os.getenv("QDRANT_URL")
        api_key=os.getenv("QDRANT_API_KEY")
        self.client = QdrantClient(
            url=url,
            api_key=api_key,
            timeout=60
        )
        print(f"Connected to Qdrant Cloud: {url}")
        self.setup_collections()
    
    def setup_collections(self):
        """Create collections with proper vector configurations"""
        collections = {
            "patient_reports": 768,  # Text embeddings (sentence-transformers-->all-mpnet-base-v2)
            "medical_images": 512,   # Image embeddings (CLIP-->clip-vit-base-patch32)
            "patient_timeline": 768  # Temporal events
        }
        
        for name, size in collections.items():
            try:
                if not self.client.collection_exists(name):
                    self.client.create_collection(
                        collection_name=name,
                        vectors_config=VectorParams(
                            size=size,
                            distance=Distance.COSINE
                        )
                    )
                    print(f"Created collection: {name}")
                else:
                    print(f"Collection exists: {name}")
                
                # Create indexes for filtering
                self.create_indexes(name)
                    
            except Exception as e:
                print(f"Error with collection {name}: {e}")
                raise
    
    def create_indexes(self, collection_name):
        """
        Payload indexes for efficient filtering
        CRITICAL: Required for filtering operations
        """
        indexes = [
            ("patient_id", PayloadSchemaType.KEYWORD),
            ("timestamp", PayloadSchemaType.FLOAT),
            ("report_type", PayloadSchemaType.KEYWORD),
            ("doctor", PayloadSchemaType.KEYWORD),
            ("diagnosis", PayloadSchemaType.KEYWORD),
        ]
        
        for field_name, field_type in indexes:
            try:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
                print(f"Index: {field_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    pass  # Index already exists, that's fine
                else:
                    print(f"Index warning for {field_name}: {str(e)[:50]}")
    
    def add_patient_report(self, patient_id, report_text, embedding, metadata):
        """Add a patient report to Qdrant"""
        point_id = str(uuid.uuid4())
        
        timestamp_unix = datetime.now().timestamp()
        
        payload = {
            "patient_id": patient_id,
            "text": report_text,
            "timestamp": timestamp_unix,
            "timestamp_iso": datetime.now().isoformat(),
            "report_type": metadata.get("report_type", "general"),
            "doctor": metadata.get("doctor", "unknown"),
            "diagnosis": metadata.get("diagnosis", ""),
            "medications": metadata.get("medications", [])
        }
        
        # Add any additional metadata
        for key, value in metadata.items():
            if key not in payload:
                payload[key] = value
        
        self.client.upsert(
            collection_name="patient_reports",
            points=[PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )]
        )
        return point_id
    
    def add_medical_image(self, patient_id, image_path, embedding, metadata):
        """Add a medical image to Qdrant"""
        point_id = str(uuid.uuid4())
        
        timestamp_unix = datetime.now().timestamp()
        
        payload = {
            "patient_id": patient_id,
            "image_path": image_path,
            "timestamp": timestamp_unix,
            "timestamp_iso": datetime.now().isoformat(),
            "modality": metadata.get("modality", "unknown"),
            "body_part": metadata.get("body_part", ""),
            "findings": metadata.get("findings", "")
        }
        
        for key, value in metadata.items():
            if key not in payload:
                payload[key] = value
        
        self.client.upsert(
            collection_name="medical_images",
            points=[PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )]
        )
        return point_id
    
    def search_patient_history(self, patient_id, query_vector, limit=5, filters=None):
        """Search patient history using vector similarity"""
        # Build filter conditions
        filter_conditions = [
            FieldCondition(
                key="patient_id",
                match=MatchValue(value=patient_id)
            )
        ]
        
        # Add date range filter if provided
        if filters and "date_range" in filters:
            filter_conditions.append(
                FieldCondition(
                    key="timestamp",
                    range=Range(
                        gte=filters["date_range"]["start"],
                        lte=filters["date_range"]["end"]
                    )
                )
            )
        
        search_filter = Filter(must=filter_conditions)
        
        # Perform search
        results = self.client.query_points(
            collection_name="patient_reports",
            query=query_vector,
            query_filter=search_filter,
            limit=limit
        )
        
        return results.points