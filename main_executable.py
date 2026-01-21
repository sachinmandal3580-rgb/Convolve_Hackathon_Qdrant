"""
Main Application - Healthcare Memory Assistant
"""

import os
from dotenv import load_dotenv
from qdrant_manager import HealthcareQdrantManager
from data_ingestion import DataIngestionPipeline
from query_retrieval import HealthcareRetrieval

# Load environment variables
load_dotenv()

class HealthcareMemoryAssistant:
    def __init__(self):
        """Initialize the healthcare assistant system"""
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_key = os.getenv("QDRANT_API_KEY")
        
        print("Initializing Healthcare Memory Assistant...")
        print("=" * 70)
        
        # Initialize components
        self.qm = HealthcareQdrantManager(qdrant_url, qdrant_key)
        self.ingestion = DataIngestionPipeline(self.qm)
        self.retrieval = HealthcareRetrieval(self.qm)
        
        print("=" * 70)
        print("✓ System ready!\n")
    
    def add_consultation(self, patient_id, consultation_data):
        """Add a patient consultation record"""
        return self.ingestion.ingest_patient_report(patient_id, consultation_data)
    
    def add_image(self, patient_id, image_data):
        """Add a medical image record"""
        return self.ingestion.ingest_medical_image(patient_id, image_data)
    
    def search_history(self, patient_id, query, recent_months=None):
        """Search patient history"""
        return self.retrieval.query_patient_history(
            patient_id, query, recent_months=recent_months
        )
    
    def get_timeline(self, patient_id):
        """Get patient timeline"""
        return self.retrieval.get_patient_timeline(patient_id)
    
    def get_summary(self, patient_id):
        """Get patient summary"""
        timeline = self.get_timeline(patient_id)
        
        return {
            "patient_id": patient_id,
            "total_records": len(timeline),
            "recent_visits": timeline[:5]
        }


def demo():
    """Run demonstration of the healthcare assistant"""
    try:
        # Initialize system
        assistant = HealthcareMemoryAssistant()
        
        # ===== ADD SAMPLE DATA =====
        print("\n" + "=" * 70)
        print("ADDING PATIENT DATA")
        print("=" * 70)
        
        sample_consultations = [
            {
                "text": "Patient presents with Type 2 Diabetes Mellitus. Fasting blood glucose: 156 mg/dL. HbA1c: 7.8%. Started on Metformin 500mg twice daily. Patient counseled on diet and exercise.",
                "report_type": "diagnosis",
                "doctor": "Dr. Sarah Smith",
                "diagnosis": "Type 2 Diabetes Mellitus",
                "medications": ["Metformin 500mg BID"]
            },
            {
                "text": "Follow-up visit after 4 weeks. Blood sugar levels improving with current medication. Fasting glucose: 118 mg/dL. Patient reports better energy levels and 5 lb weight loss. Continue current treatment plan.",
                "report_type": "follow_up",
                "doctor": "Dr. Sarah Smith",
                "diagnosis": "Type 2 Diabetes Mellitus - Improving",
                "medications": ["Metformin 500mg BID", "Lifestyle modifications"]
            },
            {
                "text": "Patient presents to ER with acute chest pain radiating to left arm and jaw. Shortness of breath noted. ECG shows ST-segment elevation. Troponin levels elevated. Immediate cardiac catheterization performed. Stent placed in LAD artery.",
                "report_type": "emergency",
                "doctor": "Dr. Michael Johnson",
                "diagnosis": "Acute ST-Elevation Myocardial Infarction (STEMI)",
                "medications": ["Aspirin 325mg", "Clopidogrel 75mg", "Atorvastatin 80mg", "Metoprolol 25mg"]
            },
            {
                "text": "Post-MI follow-up. Patient recovering well from cardiac event 2 weeks ago. No chest pain. Vital signs stable. BP: 128/82, HR: 72. Continue cardiac medications. Cardiac rehab referral provided.",
                "report_type": "follow_up",
                "doctor": "Dr. Michael Johnson",
                "diagnosis": "Status post STEMI",
                "medications": ["Aspirin", "Clopidogrel", "Atorvastatin", "Metoprolol", "Lisinopril 10mg"]
            },
            {
                "text": "Routine checkup. Patient managing diabetes well with medication and lifestyle changes. Blood pressure controlled on current medications. HbA1c: 6.2% (excellent control). Continue current treatment regimen.",
                "report_type": "routine",
                "doctor": "Dr. Sarah Smith",
                "diagnosis": "Type 2 Diabetes - Well Controlled, Hypertension - Controlled",
                "medications": ["Metformin 500mg BID", "Lisinopril 10mg daily"]
            }
        ]
        
        for i, consult in enumerate(sample_consultations, 1):
            print(f"\n{i}. Adding {consult['report_type']} record...")
            assistant.add_consultation("P001", consult)
        
        # ===== QUERY PATIENT HISTORY =====
        print("\n" + "=" * 70)
        print("QUERYING PATIENT HISTORY")
        print("=" * 70)
        
        queries = [
            ("diabetes management", None, "Finding diabetes-related records"),
            ("heart problems", None, "Finding cardiac-related records"),
            ("recent medications", 6, "Finding medication info from last 6 months"),
            ("blood pressure readings", None, "Finding BP-related records")
        ]
        
        for query, months, description in queries:
            print(f"\n{'─' * 70}")
            print(f"Query: '{query}'")
            if months:
                print(f"Filter: Last {months} months")
            print(f"Purpose: {description}")
            print('─' * 70)
            
            results = assistant.search_history("P001", query, recent_months=months)
            
            if results:
                for i, result in enumerate(results[:3], 1):
                    print(f"\n  {i}. Relevance Score: {result['score']:.3f}")
                    print(f"     Date: {result['timestamp'][:10]}")
                    print(f"     Type: {result['report_type']}")
                    print(f"     Doctor: {result.get('doctor', 'N/A')}")
                    print(f"     Diagnosis: {result.get('diagnosis', 'N/A')}")
                    print(f"     Medications: {', '.join(result.get('medications', []))}")
                    print(f"     Excerpt: {result['text'][:100]}...")
            else:
                print("\n  No results found.")
        
        # ===== PATIENT TIMELINE =====
        print("\n" + "=" * 70)
        print("PATIENT TIMELINE (Chronological)")
        print("=" * 70)
        
        summary = assistant.get_summary("P001")
        print(f"\nTotal Records: {summary['total_records']}")
        print("\nRecent Visits (Most Recent First):")
        
        for i, visit in enumerate(summary['recent_visits'], 1):
            print(f"\n{i}. {visit['timestamp'][:10]} - {visit['report_type'].upper()}")
            print(f"   Doctor: {visit.get('doctor', 'N/A')}")
            print(f"   Diagnosis: {visit.get('diagnosis', 'N/A')}")
            print(f"   Summary: {visit['text'][:80]}...")
        
        # ===== SUMMARY =====
        print("\n" + "=" * 70)
        print("DEMO COMPLETE")
        print("=" * 70)
        print("\n✅ Successfully demonstrated:")
        print("  • Multimodal data ingestion (text reports)")
        print("  • Semantic vector search")
        print("  • Temporal filtering")
        print("  • Long-term memory storage")
        print("  • Patient timeline reconstruction")
        print("\nThe system is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("1. Check if Qdrant is running: docker ps")
        print("2. Verify .env file has correct credentials")
        print("3. Run: python fix_indexes.py")
        print("4. Check internet connection for model downloads")


if __name__ == "__main__":
    demo()