import os
from dotenv import load_dotenv
from qdrant_manager import HealthcareQdrantManager
from data_ingestion import DataIngestionPipeline
from query_retrieval import HealthcareRetrieval

load_dotenv()

class HealthcareMemoryAssistant:
    def __init__(self):
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_key = os.getenv("QDRANT_API_KEY")
        
        self.qm = HealthcareQdrantManager(qdrant_url, qdrant_key)
        self.ingestion = DataIngestionPipeline(self.qm)
        self.retrieval = HealthcareRetrieval(self.qm)
    
    def add_consultation(self, patient_id, consultation_data):
        return self.ingestion.ingest_patient_report(
            patient_id, consultation_data
        )
    
    def search_history(self, patient_id, query):
        return self.retrieval.query_patient_history(
            patient_id, query
        )
    
    def get_patient_summary(self, patient_id):
        timeline = self.retrieval.get_patient_timeline(patient_id)
        
        summary = {
            "patient_id": patient_id,
            "total_records": len(timeline),
            "recent_visits": timeline[:5]
        }
        return summary

def demo():
    assistant = HealthcareMemoryAssistant()
    
    # Add sample data
    print("Adding patient data...")
    
    consultations = [
        {
            "text": "Patient presents with Type 2 Diabetes.",
            "report_type": "diagnosis",
            "doctor": "Dr. Smith",
            "diagnosis": "Type 2 Diabetes Mellitus",
            "medications": ["Metformin 500mg"]
        },
        {
            "text": "Follow-up: Blood sugar levels improving.",
            "report_type": "follow_up",
            "doctor": "Dr. Smith",
            "diagnosis": "Type 2 Diabetes Mellitus",
            "medications": ["Metformin 500mg", "Diet control"]
        },
        {
            "text": "Patient reports chest pain and shortness.",
            "report_type": "consultation",
            "doctor": "Dr. Johnson",
            "diagnosis": "Suspected Angina",
            "medications": ["Aspirin", "Nitroglycerin"]
        }
    ]
    
    for consult in consultations:
        assistant.add_consultation("P001", consult)
    
    print("\n" + "="*60)
    print("QUERYING PATIENT HISTORY")
    print("="*60)
    
    # Query examples
    queries = [
        "diabetes history",
        "heart problems",
        "current medications"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        print("-" * 60)
        results = assistant.search_history("P001", query)
        
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. Relevance: {result['score']:.3f}")
            print(f"   Date: {result['timestamp']}")
            print(f"   Diagnosis: {result.get('diagnosis', 'N/A')}")
            print(f"   Content: {result['text'][:80]}...")

if __name__ == "__main__":
    demo()