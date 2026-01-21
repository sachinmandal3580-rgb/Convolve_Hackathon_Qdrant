import os
from dotenv import load_dotenv
from qdrant_manager import HealthcareQdrantManager
from data_ingestion import DataIngestionPipeline
from query_retrieval import HealthcareRetrieval

load_dotenv()

class HealthcareMemoryAssistant:
    def __init__(self):
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_key = os.getenv("QDRANT_API_KEY")
        
        print("Initializing Healthcare Memory Assistant...")
        self.qm = HealthcareQdrantManager(qdrant_url, qdrant_key)
        self.ingestion = DataIngestionPipeline(self.qm)
        self.retrieval = HealthcareRetrieval(self.qm)
        print("✓ System ready!\n")
    
    def add_consultation(self, patient_id, consultation_data):
        return self.ingestion.ingest_patient_report(patient_id, consultation_data)
    
    def search_history(self, patient_id, query, recent_months=None):
        return self.retrieval.query_patient_history(
            patient_id, query, recent_months=recent_months
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
    """Run demonstration of the healthcare assistant"""
    try:
        assistant = HealthcareMemoryAssistant()
        
        # Add sample data
        print("=" * 70)
        print("ADDING PATIENT DATA")
        print("=" * 70)
        
        consultations = [
            {
                "text": "Patient presents with Type 2 Diabetes Mellitus. Fasting glucose: 156 mg/dL. Started on Metformin 500mg twice daily.",
                "report_type": "diagnosis",
                "doctor": "Dr. Smith",
                "diagnosis": "Type 2 Diabetes Mellitus",
                "medications": ["Metformin 500mg"]
            },
            {
                "text": "Follow-up visit. Blood sugar levels improving with current medication. Fasting glucose: 118 mg/dL. Patient reports better energy levels.",
                "report_type": "follow_up",
                "doctor": "Dr. Smith",
                "diagnosis": "Type 2 Diabetes Mellitus",
                "medications": ["Metformin 500mg", "Diet control"]
            },
            {
                "text": "Patient reports chest pain radiating to left arm and shortness of breath. ECG shows ST elevation. Troponin elevated.",
                "report_type": "emergency",
                "doctor": "Dr. Johnson",
                "diagnosis": "Suspected Acute MI",
                "medications": ["Aspirin", "Nitroglycerin"]
            }
        ]
        
        for i, consult in enumerate(consultations, 1):
            print(f"\n{i}. Adding {consult['report_type']} record...")
            assistant.add_consultation("P001", consult)
        
        print("\n" + "=" * 70)
        print("QUERYING PATIENT HISTORY")
        print("=" * 70)
        
        # Query examples
        queries = [
            ("diabetes history", None),
            ("heart problems", None),
            ("recent checkups", 6)
        ]
        
        for query, months in queries:
            print(f"\n{'─' * 70}")
            if months:
                print(f"Query: '{query}' (last {months} months)")
            else:
                print(f"Query: '{query}'")
            print('─' * 70)
            
            results = assistant.search_history("P001", query, recent_months=months)
            
            if results:
                for i, result in enumerate(results[:3], 1):
                    print(f"\n{i}. Relevance Score: {result['score']:.3f}")
                    print(f"   Date: {result['timestamp']}")
                    print(f"   Type: {result['report_type']}")
                    print(f"   Doctor: {result.get('doctor', 'N/A')}")
                    print(f"   Diagnosis: {result.get('diagnosis', 'N/A')}")
                    print(f"   Text: {result['text'][:80]}...")
            else:
                print("   No results found.")
        
        print("\n" + "=" * 70)
        print("PATIENT TIMELINE")
        print("=" * 70)
        
        summary = assistant.get_patient_summary("P001")
        print(f"\nTotal Records: {summary['total_records']}")
        print("\nRecent Visits:")
        for i, visit in enumerate(summary['recent_visits'], 1):
            print(f"\n{i}. {visit['timestamp']}")
            print(f"   Type: {visit['report_type']}")
            print(f"   Diagnosis: {visit.get('diagnosis', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nMake sure:")
        print("1. Qdrant is running or cloud credentials are correct")
        print("2. All dependencies are installed")


if __name__ == "__main__":
    demo()