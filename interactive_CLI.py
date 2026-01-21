"""
Interactive CLI - Optimized for performance
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from qdrant_manager import HealthcareQdrantManager
from data_ingestion import DataIngestionPipeline
from query_retrieval import HealthcareRetrieval
from document_processor import DocumentProcessor

load_dotenv()

class InteractiveCLI:
    """Interactive Command Line Interface with performance optimizations"""
    
    def __init__(self):
        """Initialize the system"""
        print("\n" + "=" * 70)
        print("🏥 HEALTHCARE MEMORY ASSISTANT - Interactive Mode")
        print("=" * 70)
        
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_key = os.getenv("QDRANT_API_KEY")
        
        print("\nInitializing system...")
        self.qm = HealthcareQdrantManager(qdrant_url, qdrant_key)
        self.ingestion = DataIngestionPipeline(self.qm)
        self.retrieval = HealthcareRetrieval(self.qm)
        self.doc_processor = DocumentProcessor()
        
        # Timeout for processing operations (in seconds)
        self.processing_timeout = 30
        
        print("System ready!\n")
    
    def display_menu(self):
        """Display main menu"""
        print("\n" + "=" * 70)
        print("📋 MAIN MENU")
        print("=" * 70)
        print("\n1. 📝 Add Text Report (type or paste)")
        print("2. 📄 Upload Document (PDF, DOCX, TXT)")
        print("3. 🖼️  Add Medical Image")
        print("4. 🔍 Search Patient History")
        print("5. 📅 View Patient Timeline")
        print("6. ❓ Ask a Question")
        print("7. 📁 Batch Upload Folder")
        print("8. 🚪 Exit")
        print("\n" + "-" * 70)
    
    def process_with_timeout(self, func, *args, timeout=None, **kwargs):
        """Execute a function with timeout protection"""
        if timeout is None:
            timeout = self.processing_timeout
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except TimeoutError:
                raise Exception(f"Processing timeout after {timeout} seconds. File may be too large or corrupted.")
    
    def add_text_directly(self):
        """Add text by typing/pasting"""
        print("\n" + "=" * 70)
        print("📝 ADD TEXT REPORT")
        print("=" * 70)
        
        patient_id = input("\nEnter Patient ID (e.g., P001): ").strip()
        if not patient_id:
            print("❌ Patient ID required!")
            return
        
        print("\nEnter/paste the medical report below.")
        print("When done, type 'END' on a new line and press Enter:")
        print("-" * 70)
        
        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == 'END':
                    break
                lines.append(line)
            except EOFError:
                break
        
        text = '\n'.join(lines).strip()
        
        if not text:
            print("❌ No text entered!")
            return
        
        # Extract metadata with timeout
        print("\nAnalyzing text...", end='', flush=True)
        try:
            start_time = time.time()
            metadata = self.process_with_timeout(
                self.doc_processor.extract_medical_metadata, 
                text,
                timeout=10
            )
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
        except Exception as e:
            print(f"\n⚠️  Warning: Metadata extraction failed ({e})")
            print("Using default metadata...")
            metadata = {
                'report_type': 'general',
                'doctor': 'Unknown',
                'diagnosis': None,
                'medications': []
            }
        
        # Show extracted info
        print("\n" + "-" * 70)
        print("✨ Extracted Information:")
        print(f"   Report Type: {metadata.get('report_type', 'general')}")
        print(f"   Doctor: {metadata.get('doctor', 'Unknown')}")
        print(f"   Diagnosis: {metadata.get('diagnosis') or 'Not detected'}")
        print(f"   Medications: {', '.join(metadata.get('medications', [])) if metadata.get('medications') else 'None detected'}")
        print("-" * 70)
        
        # Allow manual override
        print("\nWould you like to modify any information? (y/n): ", end='')
        if input().strip().lower() == 'y':
            metadata['report_type'] = input(f"Report Type [{metadata.get('report_type', 'general')}]: ").strip() or metadata.get('report_type', 'general')
            metadata['doctor'] = input(f"Doctor [{metadata.get('doctor', 'Unknown')}]: ").strip() or metadata.get('doctor', 'Unknown')
            metadata['diagnosis'] = input(f"Diagnosis [{metadata.get('diagnosis', '')}]: ").strip() or metadata.get('diagnosis')
        
        # Confirm
        print("\nProceed with adding this report? (y/n): ", end='')
        if input().strip().lower() != 'y':
            print("❌ Cancelled")
            return
        
        # Ingest
        try:
            print("\nSaving report...", end='', flush=True)
            start_time = time.time()
            report_data = {'text': text, **metadata}
            point_id = self.process_with_timeout(
                self.ingestion.ingest_patient_report,
                patient_id,
                report_data,
                timeout=15
            )
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            print(f"\n✅ Successfully added report: {point_id[:8]}...")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    def upload_document(self):
        """Upload a document file with optimization"""
        print("\n" + "=" * 70)
        print("📄 UPLOAD DOCUMENT")
        print("=" * 70)
        
        patient_id = input("\nEnter Patient ID: ").strip()
        if not patient_id:
            print("❌ Patient ID required!")
            return
        
        file_path = input("Enter file path (PDF, DOCX, TXT): ").strip()
        
        # Remove quotes if user added them
        file_path = file_path.strip('"').strip("'")
        
        if not file_path or not os.path.exists(file_path):
            print("❌ File not found!")
            return
        
        # Check file size
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        if file_size > 10:
            print(f"⚠️  Large file detected ({file_size:.1f} MB). This may take longer to process.")
            print("Continue? (y/n): ", end='')
            if input().strip().lower() != 'y':
                print("❌ Cancelled")
                return
        
        try:
            print(f"\n📖 Processing: {Path(file_path).name}")
            print("Reading file...", end='', flush=True)
            
            start_time = time.time()
            # Process file with timeout (adjusted based on file size)
            timeout = max(30, int(file_size * 5))  # 5 seconds per MB, min 30s
            result = self.process_with_timeout(
                self.doc_processor.process_file,
                file_path,
                timeout=timeout
            )
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            
            if result['type'] != 'text':
                print("❌ Not a text document!")
                return
            
            text = result['text']
            print(f"✓ Extracted {len(text)} characters from {result['metadata']['format'].upper()}")
            
            # Extract metadata with timeout
            print("Analyzing content...", end='', flush=True)
            start_time = time.time()
            try:
                metadata = self.process_with_timeout(
                    self.doc_processor.extract_medical_metadata,
                    text[:5000],  # Only analyze first 5000 chars for speed
                    timeout=10
                )
                metadata.update(result['metadata'])
                elapsed = time.time() - start_time
                print(f" ✓ ({elapsed:.1f}s)")
            except Exception as e:
                print(f"\n⚠️  Warning: Metadata extraction timed out")
                metadata = {
                    'report_type': 'general',
                    'doctor': 'Unknown',
                    'diagnosis': None,
                    'medications': []
                }
                metadata.update(result['metadata'])
            
            # Show preview
            print("\n" + "-" * 70)
            print("📄 Document Preview:")
            preview = text[:400] + "..." if len(text) > 400 else text
            print(preview)
            print("\n" + "-" * 70)
            print("✨ Extracted Information:")
            print(f"   Report Type: {metadata.get('report_type', 'general')}")
            print(f"   Doctor: {metadata.get('doctor', 'Unknown')}")
            print(f"   Diagnosis: {metadata.get('diagnosis') or 'Not detected'}")
            print(f"   Medications: {', '.join(metadata.get('medications', [])) or 'None'}")
            print("-" * 70)
            
            # Confirm
            print("\nAdd this document? (y/n): ", end='')
            if input().strip().lower() != 'y':
                print("❌ Cancelled")
                return
            
            # Ingest
            print("\nSaving document...", end='', flush=True)
            start_time = time.time()
            report_data = {'text': text, **metadata}
            point_id = self.process_with_timeout(
                self.ingestion.ingest_patient_report,
                patient_id,
                report_data,
                timeout=20
            )
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            print(f"\n✅ Document added successfully: {point_id[:8]}...")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def add_image(self):
        """Add medical image with optimization"""
        print("\n" + "=" * 70)
        print("🖼️  ADD MEDICAL IMAGE")
        print("=" * 70)
        
        patient_id = input("\nEnter Patient ID: ").strip()
        if not patient_id:
            print("❌ Patient ID required!")
            return
        
        image_path = input("Enter image file path: ").strip().strip('"').strip("'")
        
        if not image_path or not os.path.exists(image_path):
            print("❌ Image file not found!")
            return
        
        # Check file size
        file_size = os.path.getsize(image_path) / (1024 * 1024)  # MB
        if file_size > 20:
            print(f"⚠️  Large image file ({file_size:.1f} MB). This may take longer to process.")
            print("Continue? (y/n): ", end='')
            if input().strip().lower() != 'y':
                print("❌ Cancelled")
                return
        
        try:
            print(f"\n🖼️  Processing: {Path(image_path).name}")
            print("Reading image...", end='', flush=True)
            
            start_time = time.time()
            # Process with timeout (adjusted for image size)
            timeout = max(30, int(file_size * 3))  # 3 seconds per MB
            result = self.process_with_timeout(
                self.doc_processor.process_file,
                image_path,
                timeout=timeout
            )
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            
            if result['type'] != 'image':
                print("❌ Not a valid image file!")
                return
            
            print(f"✓ Valid {result['metadata']['format']} image")
            if 'size' in result['metadata']:
                print(f"  Size: {result['metadata']['size'][0]}x{result['metadata']['size'][1]} pixels")
            
            # Get metadata
            print("\n📝 Enter image details:")
            modality = input("  Modality (X-ray/MRI/CT/Ultrasound/Other): ").strip() or "Unknown"
            body_part = input("  Body part (chest/head/abdomen/etc.): ").strip() or "Unknown"
            findings = input("  Findings/Notes: ").strip() or ""
            
            # Confirm
            print("\nAdd this image? (y/n): ", end='')
            if input().strip().lower() != 'y':
                print("❌ Cancelled")
                return
            
            # Ingest
            print("\nSaving image...", end='', flush=True)
            start_time = time.time()
            image_data = {
                'path': result['path'],
                'modality': modality,
                'body_part': body_part,
                'findings': findings
            }
            
            point_id = self.process_with_timeout(
                self.ingestion.ingest_medical_image,
                patient_id,
                image_data,
                timeout=30
            )
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            print(f"\n✅ Image added successfully: {point_id[:8]}...")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def search_history(self):
        """Search patient history"""
        print("\n" + "=" * 70)
        print("🔍 SEARCH PATIENT HISTORY")
        print("=" * 70)
        
        patient_id = input("\nEnter Patient ID: ").strip()
        if not patient_id:
            print("❌ Patient ID required!")
            return
        
        query = input("Search query: ").strip()
        if not query:
            print("❌ Query required!")
            return
        
        time_filter = input("Filter by time? (enter months, e.g., 6 for last 6 months, or leave empty): ").strip()
        recent_months = int(time_filter) if time_filter.isdigit() else None
        
        try:
            print("\n🔍 Searching...", end='', flush=True)
            start_time = time.time()
            results = self.process_with_timeout(
                self.retrieval.query_patient_history,
                patient_id=patient_id,
                query=query,
                top_k=10,
                recent_months=recent_months,
                timeout=15
            )
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            
            if not results:
                print("\n❌ No results found")
                return
            
            print(f"\n✅ Found {len(results)} results:")
            print("=" * 70)
            
            for i, result in enumerate(results, 1):
                print(f"\n{i}. 📊 Relevance: {result['score']:.1%}")
                print(f"   📅 Date: {result['timestamp'][:10]}")
                print(f"   📋 Type: {result['report_type']}")
                print(f"   👨‍⚕️ Doctor: {result['doctor']}")
                print(f"   🩺 Diagnosis: {result['diagnosis'] or 'N/A'}")
                if result.get('medications'):
                    print(f"   💊 Medications: {', '.join(result['medications'])}")
                print(f"   📝 {result['text'][:150]}...")
                print("-" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    def view_timeline(self):
        """View patient timeline"""
        print("\n" + "=" * 70)
        print("📅 PATIENT TIMELINE")
        print("=" * 70)
        
        patient_id = input("\nEnter Patient ID: ").strip()
        if not patient_id:
            print("❌ Patient ID required!")
            return
        
        try:
            print("\n🔄 Loading timeline...", end='', flush=True)
            start_time = time.time()
            timeline = self.process_with_timeout(
                self.retrieval.get_patient_timeline,
                patient_id,
                limit=20,
                timeout=10
            )
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            
            if not timeline:
                print("\n❌ No records found")
                return
            
            print(f"\n✅ Found {len(timeline)} records (most recent first):")
            print("=" * 70)
            
            for i, record in enumerate(timeline, 1):
                print(f"\n{i}. 📅 {record['timestamp'][:10]} - {record['report_type'].upper()}")
                print(f"   👨‍⚕️ {record['doctor']}")
                print(f"   🩺 {record['diagnosis'] or 'N/A'}")
                if record.get('medications'):
                    print(f"   💊 {', '.join(record['medications'])}")
                print(f"   📝 {record['text'][:100]}...")
                print("-" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    def ask_question(self):
        """Natural language Q&A"""
        print("\n" + "=" * 70)
        print("❓ ASK A QUESTION")
        print("=" * 70)
        print("\n💡 Examples:")
        print("   • What medications is the patient taking for diabetes?")
        print("   • Show recent cardiac evaluations")
        print("   • When was the last blood pressure reading?")
        
        patient_id = input("\nEnter Patient ID: ").strip()
        if not patient_id:
            print("❌ Patient ID required!")
            return
        
        question = input("Your question: ").strip()
        if not question:
            print("❌ Question required!")
            return
        
        try:
            print("\n🤔 Analyzing question...", end='', flush=True)
            start_time = time.time()
            results = self.process_with_timeout(
                self.retrieval.query_patient_history,
                patient_id=patient_id,
                query=question,
                top_k=5,
                timeout=15
            )
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            
            if not results:
                print("\n❌ No relevant information found")
                return
            
            # Show best answer
            best = results[0]
            print(f"\n✅ Answer (Confidence: {best['score']:.1%}):")
            print("=" * 70)
            print(f"📅 Date: {best['timestamp'][:10]}")
            print(f"📋 Type: {best['report_type']}")
            print(f"👨‍⚕️ Doctor: {best['doctor']}")
            print(f"🩺 Diagnosis: {best['diagnosis'] or 'N/A'}")
            if best.get('medications'):
                print(f"💊 Medications: {', '.join(best['medications'])}")
            print(f"\n📝 Content:\n{best['text']}")
            
            # Show other relevant results
            if len(results) > 1:
                print("\n" + "=" * 70)
                print("📚 Other Relevant Records:")
                for i, r in enumerate(results[1:], 2):
                    print(f"\n{i}. {r['timestamp'][:10]} - {r['report_type']} ({r['score']:.1%})")
                    print(f"   {r['text'][:80]}...")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    def batch_upload(self):
        """Batch upload folder with parallel processing"""
        print("\n" + "=" * 70)
        print("📁 BATCH UPLOAD")
        print("=" * 70)
        
        patient_id = input("\nEnter Patient ID: ").strip()
        if not patient_id:
            print("❌ Patient ID required!")
            return
        
        folder_path = input("Enter folder path: ").strip().strip('"').strip("'")
        
        if not folder_path or not os.path.isdir(folder_path):
            print("❌ Invalid folder!")
            return
        
        folder = Path(folder_path)
        
        # Find all files
        files = []
        for ext in self.doc_processor.supported_text_formats + self.doc_processor.supported_image_formats:
            files.extend(folder.glob(f"*{ext}"))
        
        if not files:
            print("❌ No supported files found!")
            return
        
        print(f"\n📂 Found {len(files)} files:")
        for i, f in enumerate(files[:10], 1):
            print(f"   {i}. {f.name}")
        if len(files) > 10:
            print(f"   ... and {len(files) - 10} more")
        
        print(f"\nProcess all {len(files)} files? (y/n): ", end='')
        if input().strip().lower() != 'y':
            print("❌ Cancelled")
            return
        
        # Process with progress tracking
        success = 0
        errors = 0
        skipped = 0
        
        print("\n" + "=" * 70)
        print("Processing files...")
        print("=" * 70)
        
        for idx, file_path in enumerate(files, 1):
            try:
                print(f"\n[{idx}/{len(files)}] 📄 {file_path.name}...", end=' ', flush=True)
                start_time = time.time()
                
                # Check file size
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                if file_size > 50:
                    print(f"⊘ Skipped (too large: {file_size:.1f}MB)")
                    skipped += 1
                    continue
                
                # Process with timeout
                timeout = max(30, int(file_size * 5))
                result = self.process_with_timeout(
                    self.doc_processor.process_file,
                    file_path,
                    timeout=timeout
                )
                
                if result['type'] == 'text':
                    # Quick metadata extraction on partial text
                    text_sample = result['text'][:3000]
                    try:
                        metadata = self.process_with_timeout(
                            self.doc_processor.extract_medical_metadata,
                            text_sample,
                            timeout=5
                        )
                    except:
                        metadata = {
                            'report_type': 'general',
                            'doctor': 'Unknown',
                            'diagnosis': None,
                            'medications': []
                        }
                    
                    report_data = {'text': result['text'], **metadata}
                    self.process_with_timeout(
                        self.ingestion.ingest_patient_report,
                        patient_id,
                        report_data,
                        timeout=15
                    )
                    
                elif result['type'] == 'image':
                    image_data = {
                        'path': result['path'],
                        'modality': 'Unknown',
                        'body_part': 'Unknown',
                        'findings': ''
                    }
                    self.process_with_timeout(
                        self.ingestion.ingest_medical_image,
                        patient_id,
                        image_data,
                        timeout=20
                    )
                
                elapsed = time.time() - start_time
                print(f"✓ ({elapsed:.1f}s)")
                success += 1
                
            except Exception as e:
                error_msg = str(e)[:50]
                print(f"✗ ({error_msg})")
                errors += 1
        
        print("\n" + "=" * 70)
        print(f"✅ Batch complete!")
        print(f"   Success: {success}")
        print(f"   Errors: {errors}")
        print(f"   Skipped: {skipped}")
        print("=" * 70)
    
    def run(self):
        """Main loop"""
        while True:
            try:
                self.display_menu()
                choice = input("Select option (1-8): ").strip()
                
                if choice == '1':
                    self.add_text_directly()
                elif choice == '2':
                    self.upload_document()
                elif choice == '3':
                    self.add_image()
                elif choice == '4':
                    self.search_history()
                elif choice == '5':
                    self.view_timeline()
                elif choice == '6':
                    self.ask_question()
                elif choice == '7':
                    self.batch_upload()
                elif choice == '8':
                    print("\n👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid option!")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    cli = InteractiveCLI()
    cli.run()