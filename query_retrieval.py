"""
Query and Retrieval - Search and retrieve patient data
"""

from embeddings import EmbeddingGenerator
from qdrant_manager import HealthcareQdrantManager
from datetime import datetime, timedelta
from qdrant_client.models import Filter, FieldCondition, MatchValue

class HealthcareRetrieval:
    def __init__(self, qdrant_manager):
        """
        Initialize retrieval system
        
        Args:
            qdrant_manager: HealthcareQdrantManager instance
        """
        self.qm = qdrant_manager
        self.embedder = EmbeddingGenerator()
    
    def query_patient_history(self, patient_id, query, top_k=5, recent_months=None):
        """
        Query patient history with semantic search
        
        Args:
            patient_id: Patient identifier
            query: Natural language query
            top_k: Number of results to return
            recent_months: Optional filter for recent records
        
        Returns:
            List of formatted results
        """
        # Generate query embedding
        query_vector = self.embedder.encode_text(query)
        
        # Build date filter if specified
        filters = None
        if recent_months:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=recent_months*30)
            
            filters = {
                "date_range": {
                    "start": start_date.timestamp(),
                    "end": end_date.timestamp()
                }
            }
        
        # Search
        results = self.qm.search_patient_history(
            patient_id=patient_id,
            query_vector=query_vector,
            limit=top_k,
            filters=filters
        )
        
        return self.format_results(results)
    
    def format_results(self, results):
        """Format search results for display"""
        formatted = []
        
        if not results:
            return formatted
        
        for result in results:
            if hasattr(result, 'payload'):
                payload = result.payload
                score = getattr(result, 'score', 0.0)
            elif isinstance(result, dict):
                payload = result
                score = result.get('score', 0.0)
            else:
                continue
            
            formatted.append({
                "score": score,
                "text": payload.get("text", ""),
                "timestamp": payload.get("timestamp_iso", ""),
                "report_type": payload.get("report_type", ""),
                "doctor": payload.get("doctor", ""),
                "diagnosis": payload.get("diagnosis", ""),
                "medications": payload.get("medications", [])
            })
        
        return formatted
    
    def get_patient_timeline(self, patient_id, limit=20):
        """
        Retrieve chronological patient history
        
        Args:
            patient_id: Patient identifier
            limit: Maximum number of records
        
        Returns:
            List of records sorted by date (newest first)
        """
        try:
            points, _ = self.qm.client.scroll(
                collection_name="patient_reports",
                scroll_filter=Filter(
                    must=[FieldCondition(
                        key="patient_id",
                        match=MatchValue(value=patient_id)
                    )]
                ),
                limit=limit
            )
            
            # Sort by timestamp (newest first)
            sorted_points = sorted(
                points,
                key=lambda x: x.payload.get("timestamp", 0),
                reverse=True
            )
            
            return self.format_results(sorted_points)
            
        except Exception as e:
            print(f"Error retrieving timeline: {e}")
            return []
    
    def hybrid_search(self, patient_id, text_query, conditions=None):
        """
        Hybrid search combining semantic and metadata filtering
        
        Args:
            patient_id: Patient identifier
            text_query: Semantic query
            conditions: Dict of exact-match conditions
                {"report_type": "lab_results", "doctor": "Dr. Smith"}
        
        Returns:
            List of matching results
        """
        query_vector = self.embedder.encode_text(text_query)
        
        # Build filter conditions
        filter_conditions = [
            FieldCondition(
                key="patient_id",
                match=MatchValue(value=patient_id)
            )
        ]
        
        # Add metadata conditions
        if conditions:
            for key, value in conditions.items():
                filter_conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
        
        search_filter = Filter(must=filter_conditions)
        
        results = self.qm.client.query_points(
            collection_name="patient_reports",
            query=query_vector,
            query_filter=search_filter,
            limit=10
        )
        
        return self.format_results(results.points)