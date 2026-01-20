from embeddings import EmbeddingGenerator
from qdrant_manager import HealthcareQdrantManager
from datetime import datetime, timedelta

class HealthcareRetrieval:
    def __init__(self, qdrant_manager):
        self.qm = qdrant_manager
        self.embedder = EmbeddingGenerator()
    
    def query_patient_history(self, patient_id, query, 
                             top_k=5, recent_months=None):
        # Generate query embedding
        query_vector = self.embedder.encode_text(query)
        
        # Optional: filter by date
        filters = None
        if recent_months:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=recent_months*30)
            filters = {
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
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
        formatted = []
        for result in results:
            formatted.append({
                "score": result.score,
                "text": result.payload.get("text", ""),
                "timestamp": result.payload.get("timestamp"),
                "report_type": result.payload.get("report_type"),
                "doctor": result.payload.get("doctor"),
                "diagnosis": result.payload.get("diagnosis")
            })
        return formatted
    
    def get_patient_timeline(self, patient_id, limit=20):
        """Retrieve chronological patient history"""
        # This would use scroll or pagination
        all_records = []
        
        # Search with a generic vector to get all records
        dummy_vector = [0.0] * 768
        results = self.qm.client.search(
            collection_name="patient_reports",
            query_vector=dummy_vector,
            query_filter={
                "must": [{
                    "key": "patient_id",
                    "match": {"value": patient_id}
                }]
            },
            limit=limit
        )
        
        # Sort by timestamp
        sorted_results = sorted(
            results,
            key=lambda x: x.payload.get("timestamp", ""),
            reverse=True
        )
        
        return self.format_results(sorted_results)
    
    def hybrid_search(self, patient_id, text_query, 
                     conditions=None):
        """
        Hybrid search with metadata filtering
        conditions = {
            "report_type": "lab_results",
            "diagnosis": "diabetes"
        }
        """
        query_vector = self.embedder.encode_text(text_query)
        
        # Build complex filter
        filter_conditions = [{
            "key": "patient_id",
            "match": {"value": patient_id}
        }]
        
        if conditions:
            for key, value in conditions.items():
                filter_conditions.append({
                    "key": key,
                    "match": {"value": value}
                })
        
        results = self.qm.client.search(
            collection_name="patient_reports",
            query_vector=query_vector,
            query_filter={"must": filter_conditions},
            limit=10
        )
        
        return self.format_results(results)

# Example usage
if __name__ == "__main__":
    qm = HealthcareQdrantManager()
    retrieval = HealthcareRetrieval(qm)
    
    # Query patient history
    results = retrieval.query_patient_history(
        patient_id="P001",
        query="previous respiratory infections",
        top_k=5,
        recent_months=6
    )
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']:.3f}")
        print(f"   Date: {result['timestamp']}")
        print(f"   Type: {result['report_type']}")
        print(f"   Text: {result['text'][:100]}...")
        print(f"   Diagnosis: {result.get('diagnosis', 'N/A')}")