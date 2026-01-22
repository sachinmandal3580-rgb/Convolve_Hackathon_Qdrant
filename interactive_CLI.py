"""
Interactive CLI 
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Import the new unified medical document processor
from document_processor import MedicalDocumentProcessor

load_dotenv()

class InteractiveCLI:
    """Interactive Command Line Interface with Medical Document Processor"""
    
    def __init__(self):
        """Initialize the system"""
        print("\n" + "=" * 70)
        print("🏥 HEALTHCARE MEMORY ASSISTANT - Interactive Mode")
        print("=" * 70)
        
        print("\nInitializing system...")
        
        # Initialize the unified medical document processor
        self.doc_processor = MedicalDocumentProcessor()
        
        # Timeout for processing operations (in seconds)
        self.processing_timeout = 30
        
        print("✅ System ready!")
        print(f"📄 Text formats: {', '.join(self.doc_processor.supported_text_formats)}")
        print(f"🖼️  Image formats: {', '.join(self.doc_processor.supported_image_formats)}")
        print()
    
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
        
        # Extract metadata
        print("\n🔍 Analyzing text...", end='', flush=True)
        try:
            start_time = time.time()
            metadata = self.doc_processor.extract_medical_metadata(text, fast_mode=True)
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
        except Exception as e:
            print(f"\n⚠️  Warning: Metadata extraction failed ({e})")
            print("Using default metadata...")
            metadata = {
                'report_type': 'general',
                'doctor': None,
                'diagnosis': None,
                'medications': []
            }
        
        # Show extracted info
        print("\n" + "-" * 70)
        print("✨ Extracted Information:")
        print(f"   📋 Report Type: {metadata.get('report_type', 'general')}")
        print(f"   👨‍⚕️ Doctor: {metadata.get('doctor') or 'Not detected'}")
        print(f"   🩺 Diagnosis: {metadata.get('diagnosis') or 'Not detected'}")
        print(f"   🏥 Department: {metadata.get('department') or 'Not detected'}")
        print(f"   📅 Date: {metadata.get('report_date') or 'Not detected'}")
        if metadata.get('medications'):
            print(f"   💊 Medications: {', '.join(metadata['medications'])}")
        else:
            print(f"   💊 Medications: None detected")
        print("-" * 70)
        
        # Allow manual override
        print("\nWould you like to modify any information? (y/n): ", end='')
        if input().strip().lower() == 'y':
            metadata['report_type'] = input(f"Report Type [{metadata.get('report_type', 'general')}]: ").strip() or metadata.get('report_type', 'general')
            metadata['doctor'] = input(f"Doctor [{metadata.get('doctor', '')}]: ").strip() or metadata.get('doctor')
            metadata['diagnosis'] = input(f"Diagnosis [{metadata.get('diagnosis', '')}]: ").strip() or metadata.get('diagnosis')
        
        # Confirm
        print("\nProceed with adding this report? (y/n): ", end='')
        if input().strip().lower() != 'y':
            print("❌ Cancelled")
            return
        
        # Save using the document processor (which stores in database)
        try:
            print("\n💾 Saving report to database...", end='', flush=True)
            start_time = time.time()
            
            # Create a temporary text file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(text)
                temp_path = f.name
            
            # Upload using document processor
            result = self.doc_processor.upload_document(patient_id, temp_path)
            
            # Clean up temp file
            os.remove(temp_path)
            
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            
            if result['success']:
                print(f"\n✅ Report saved successfully! (ID: {result['document_id']})")
            else:
                print(f"\n❌ Error saving report: {result['error']}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    def upload_document(self):
        """Upload a document file"""
        print("\n" + "=" * 70)
        print("📄 UPLOAD DOCUMENT")
        print("=" * 70)
        
        patient_id = input("\nEnter Patient ID: ").strip()
        if not patient_id:
            print("❌ Patient ID required!")
            return
        
        file_path = input("Enter file path (PDF, DOCX, TXT, JSON): ").strip()
        
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
            print("⏳ Uploading and processing document...", end='', flush=True)
            
            start_time = time.time()
            result = self.doc_processor.upload_document(patient_id, file_path)
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            
            if not result['success']:
                print(f"\n❌ Error: {result['error']}")
                return
            
            # Show results
            print("\n" + "=" * 70)
            print("✅ Document uploaded successfully!")
            print("=" * 70)
            print(f"📄 File Type: {result['file_type'].upper()} ({result['format'].upper()})")
            print(f"📝 Extracted: {result['extracted_text_length']} characters")
            print(f"🆔 Document ID: {result['document_id']}")
            print("\n✨ Extracted Information:")
            print(f"   📋 Report Type: {result['metadata']['report_type']}")
            print(f"   👨‍⚕️ Doctor: {result['metadata']['doctor'] or 'Not detected'}")
            print(f"   🩺 Diagnosis: {result['metadata']['diagnosis'] or 'Not detected'}")
            print(f"   🏥 Department: {result['metadata']['department'] or 'Not detected'}")
            print(f"   📅 Date: {result['metadata']['report_date'] or 'Not detected'}")
            if result['metadata']['medications']:
                print(f"   💊 Medications: {', '.join(result['metadata']['medications'])}")
            print(f"   💾 Stored at: {result['storage_path']}")
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def add_image(self):
        """Add medical image with OCR"""
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
            print("⏳ Uploading and performing OCR...", end='', flush=True)
            
            start_time = time.time()
            result = self.doc_processor.upload_document(patient_id, image_path)
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            
            if not result['success']:
                print(f"\n❌ Error: {result['error']}")
                return
            
            # Show results
            print("\n" + "=" * 70)
            print("✅ Medical image uploaded successfully!")
            print("=" * 70)
            print(f"🖼️  File Type: {result['format'].upper()}")
            print(f"📝 OCR Extracted: {result['extracted_text_length']} characters")
            print(f"🆔 Document ID: {result['document_id']}")
            print("\n✨ Extracted Information:")
            print(f"   📋 Report Type: {result['metadata']['report_type']}")
            print(f"   👨‍⚕️ Doctor: {result['metadata']['doctor'] or 'Not detected'}")
            print(f"   🩺 Diagnosis: {result['metadata']['diagnosis'] or 'Not detected'}")
            print(f"   🏥 Department: {result['metadata']['department'] or 'Not detected'}")
            if result['metadata']['medications']:
                print(f"   💊 Medications: {', '.join(result['metadata']['medications'])}")
            print(f"   💾 Stored at: {result['storage_path']}")
            
            # Show OCR preview if text was extracted
            if result['extracted_text_length'] > 0:
                print("\n📄 OCR Text Preview (first 300 characters):")
                print("-" * 70)
                # Get the extracted text from database
                import sqlite3
                conn = sqlite3.connect(self.doc_processor.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT extracted_text FROM medical_documents WHERE document_id = ?', 
                             (result['document_id'],))
                row = cursor.fetchone()
                if row and row[0]:
                    preview = row[0][:300]
                    print(preview + "..." if len(row[0]) > 300 else preview)
                conn.close()
            else:
                print("\n⚠️  No text could be extracted from image (OCR found no readable text)")
            
            print("=" * 70)
            
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
            results = self.doc_processor.search_patient_records(
                patient_id=patient_id,
                search_query=query,
                months_filter=recent_months
            )
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            
            if not results:
                print("\n❌ No results found")
                return
            
            print(f"\n✅ Found {len(results)} results:")
            print("=" * 70)
            
            for i, result in enumerate(results, 1):
                record_id, record_type, content, doctor_name, record_date, created_at, file_path, extracted_text = result
                
                print(f"\n{i}. 📋 {record_type}")
                print(f"   🆔 Record ID: {record_id}")
                print(f"   📅 Created: {created_at}")
                if record_date:
                    print(f"   📅 Report Date: {record_date}")
                if doctor_name:
                    print(f"   👨‍⚕️ Doctor: {doctor_name}")
                if content:
                    print(f"   📝 {content[:200]}...")
                if file_path:
                    print(f"   📄 File: {Path(file_path).name}")
                print("-" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
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
            timeline = self.doc_processor.search_patient_records(patient_id)
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            
            if not timeline:
                print("\n❌ No records found")
                return
            
            print(f"\n✅ Found {len(timeline)} records (most recent first):")
            print("=" * 70)
            
            for i, result in enumerate(timeline, 1):
                record_id, record_type, content, doctor_name, record_date, created_at, file_path, extracted_text = result
                
                print(f"\n{i}. 📅 {created_at[:10]} - {record_type}")
                if doctor_name:
                    print(f"   👨‍⚕️ {doctor_name}")
                if record_date:
                    print(f"   📅 Report Date: {record_date}")
                if content:
                    print(f"   📝 {content[:150]}...")
                if file_path:
                    print(f"   📄 Source: {Path(file_path).name}")
                print("-" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def ask_question(self):
        """Natural language Q&A"""
        print("\n" + "=" * 70)
        print("❓ ASK A QUESTION")
        print("=" * 70)
        print("\n💡 Examples:")
        print("   • What medications is the patient taking?")
        print("   • Show reports from Dr. Smith")
        print("   • Find diagnosis information")
        
        patient_id = input("\nEnter Patient ID: ").strip()
        if not patient_id:
            print("❌ Patient ID required!")
            return
        
        question = input("Your question: ").strip()
        if not question:
            print("❌ Question required!")
            return
        
        try:
            print("\n🤔 Searching for relevant information...", end='', flush=True)
            start_time = time.time()
            results = self.doc_processor.search_patient_records(
                patient_id=patient_id,
                search_query=question
            )
            elapsed = time.time() - start_time
            print(f" ✓ ({elapsed:.1f}s)")
            
            if not results:
                print("\n❌ No relevant information found")
                return
            
            # Show best answer
            print(f"\n✅ Found {len(results)} relevant record(s):")
            print("=" * 70)
            
            for i, result in enumerate(results[:3], 1):  # Show top 3
                record_id, record_type, content, doctor_name, record_date, created_at, file_path, extracted_text = result
                
                print(f"\n{i}. 📋 {record_type}")
                print(f"   📅 Date: {created_at[:10]}")
                if doctor_name:
                    print(f"   👨‍⚕️ Doctor: {doctor_name}")
                if record_date:
                    print(f"   📅 Report Date: {record_date}")
                
                # Show content or extracted text
                display_text = extracted_text if extracted_text else content
                if display_text:
                    print(f"\n   📝 Content:")
                    print(f"   {display_text[:400]}...")
                
                print("-" * 70)
            
            if len(results) > 3:
                print(f"\n... and {len(results) - 3} more record(s)")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def batch_upload(self):
        """Batch upload folder"""
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
        
        try:
            print(f"\n📂 Scanning folder...", end='', flush=True)
            result = self.doc_processor.batch_upload_folder(patient_id, folder_path)
            
            if not result['success']:
                print(f"\n❌ Error: {result['error']}")
                return
            
            print(f" ✓")
            print("\n" + "=" * 70)
            print("✅ Batch upload complete!")
            print("=" * 70)
            print(f"📊 Total files: {result['total_files']}")
            print(f"✅ Successful: {result['successful']}")
            print(f"❌ Failed: {result['failed']}")
            print("\n📋 Details:")
            
            for item in result['results']:
                filename = item['filename']
                item_result = item['result']
                
                if item_result.get('success'):
                    print(f"   ✅ {filename} - ID: {item_result['document_id']}")
                else:
                    error = item_result.get('error', 'Unknown error')[:50]
                    print(f"   ❌ {filename} - {error}")
            
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
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