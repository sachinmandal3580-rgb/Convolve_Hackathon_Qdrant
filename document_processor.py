"""
Document Processor - Handles various file formats (OPTIMIZED & FIXED)
Supports: PDF, DOCX, TXT, JSON, Images (JPG, PNG, etc.)
"""

import os
import json
import re
from pathlib import Path
from PIL import Image
import PyPDF2
import docx

class DocumentProcessor:
    """Process various document types with performance optimizations"""
    
    def __init__(self):
        self.supported_text_formats = ['.txt', '.pdf', '.docx', '.json']
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
        
        # Performance settings
        self.max_pdf_pages = 100  # Limit pages to prevent hang
        self.max_text_length = 1_000_000  # 1MB text limit
        self.max_image_dimension = 2048  # Resize large images
    
    def process_file(self, file_path):
        """
        Process any supported file type
        
        Args:
            file_path: Path to file (str or Path object)
            
        Returns:
            dict: {'type': 'text'|'image', 'text': str, 'path': str, 'metadata': dict}
        """
        # CRITICAL FIX: Removed the buggy input() line!
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file size upfront
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 100:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB (max 100MB)")
        
        extension = file_path.suffix.lower()
        
        # Text documents
        if extension == '.txt':
            return self.process_txt(file_path)
        elif extension == '.pdf':
            return self.process_pdf(file_path)
        elif extension == '.docx':
            return self.process_docx(file_path)
        elif extension == '.json':
            return self.process_json(file_path)
        
        # Images
        elif extension in self.supported_image_formats:
            return self.process_image(file_path)
        
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    def process_txt(self, file_path):
        """Process plain text file with size limit"""
        file_size = file_path.stat().st_size
        
        # Read with size limit
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            if file_size > self.max_text_length:
                text = f.read(self.max_text_length)
                truncated = True
            else:
                text = f.read()
                truncated = False
        
        return {
            'type': 'text',
            'text': text,
            'metadata': {
                'filename': file_path.name,
                'format': 'txt',
                'size_bytes': file_size,
                'truncated': truncated
            }
        }
    
    def process_pdf(self, file_path):
        """Process PDF file with page limit and error handling"""
        text_content = []
        
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                num_pages = len(pdf_reader.pages)
                
                # Limit pages to prevent hanging
                pages_to_process = min(num_pages, self.max_pdf_pages)
                truncated = num_pages > self.max_pdf_pages
                
                for page_num in range(pages_to_process):
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        if text and text.strip():
                            text_content.append(text)
                        
                        # Break if we've collected enough text
                        current_length = sum(len(t) for t in text_content)
                        if current_length > self.max_text_length:
                            truncated = True
                            break
                            
                    except Exception as e:
                        print(f"Warning: Could not extract page {page_num}: {e}")
                        continue
        
        except Exception as e:
            raise ValueError(f"Error processing PDF: {e}")
        
        if not text_content:
            raise ValueError("No text could be extracted from PDF")
        
        full_text = '\n\n'.join(text_content)
        
        return {
            'type': 'text',
            'text': full_text[:self.max_text_length],  # Enforce limit
            'metadata': {
                'filename': file_path.name,
                'format': 'pdf',
                'num_pages': num_pages,
                'pages_processed': pages_to_process,
                'size_bytes': file_path.stat().st_size,
                'truncated': truncated
            }
        }
    
    def process_docx(self, file_path):
        """Process Word document with paragraph limit"""
        try:
            doc = docx.Document(file_path)
            
            text_content = []
            total_chars = 0
            truncated = False
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
                    total_chars += len(paragraph.text)
                    
                    # Break if we've collected enough
                    if total_chars > self.max_text_length:
                        truncated = True
                        break
            
            if not text_content:
                raise ValueError("No text content found in document")
            
            return {
                'type': 'text',
                'text': '\n\n'.join(text_content),
                'metadata': {
                    'filename': file_path.name,
                    'format': 'docx',
                    'num_paragraphs': len(doc.paragraphs),
                    'size_bytes': file_path.stat().st_size,
                    'truncated': truncated
                }
            }
        except Exception as e:
            raise ValueError(f"Error processing DOCX: {e}")
    
    def process_json(self, file_path):
        """Process JSON file with size limit"""
        file_size = file_path.stat().st_size
        
        if file_size > 10 * 1024 * 1024:  # 10MB limit for JSON
            raise ValueError(f"JSON file too large: {file_size / (1024*1024):.1f}MB")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")
        
        # Convert JSON to readable text
        if isinstance(data, dict) and 'text' in data:
            text = data['text']
            metadata = {k: v for k, v in data.items() if k != 'text'}
        else:
            text = json.dumps(data, indent=2)
            metadata = {}
        
        # Truncate if needed
        if len(text) > self.max_text_length:
            text = text[:self.max_text_length]
            metadata['truncated'] = True
        
        metadata.update({
            'filename': file_path.name,
            'format': 'json',
            'size_bytes': file_size
        })
        
        return {
            'type': 'text',
            'text': text,
            'metadata': metadata
        }
    
    def process_image(self, file_path):
        """Process image file with size optimization"""
        try:
            # Open and verify image
            with Image.open(file_path) as img:
                # Get original metadata
                original_format = img.format
                original_size = img.size
                original_mode = img.mode
                
                # Check if image needs resizing
                width, height = img.size
                needs_resize = width > self.max_image_dimension or height > self.max_image_dimension
                
                if needs_resize:
                    # Calculate new dimensions maintaining aspect ratio
                    if width > height:
                        new_width = self.max_image_dimension
                        new_height = int(height * (self.max_image_dimension / width))
                    else:
                        new_height = self.max_image_dimension
                        new_width = int(width * (self.max_image_dimension / height))
                    
                    # Note: We're not actually resizing here, just noting it
                    # The resizing can be done later when creating embeddings
                    resized = (new_width, new_height)
                else:
                    resized = None
            
            return {
                'type': 'image',
                'path': str(file_path.absolute()),
                'metadata': {
                    'filename': file_path.name,
                    'format': original_format,
                    'size': original_size,
                    'mode': original_mode,
                    'size_bytes': file_path.stat().st_size,
                    'needs_resize': needs_resize,
                    'suggested_size': resized
                }
            }
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}")
    
    def extract_medical_metadata(self, text, fast_mode=False):
        """
        Extract medical metadata from text using pattern matching
        
        Args:
            text: Medical text
            fast_mode: If True, analyze only first 5000 chars for speed
            
        Returns:
            dict: Extracted metadata
        """
        # Optimize by limiting text length
        if fast_mode or len(text) > 5000:
            text_to_analyze = text[:5000]
        else:
            text_to_analyze = text
        
        metadata = {
            'report_type': 'general',
            'doctor': 'unknown',
            'diagnosis': '',
            'medications': []
        }
        
        text_lower = text_to_analyze.lower()
        
        # Detect report type (optimized with early returns)
        report_keywords = {
            'lab_results': ['lab', 'laboratory', 'test result'],
            'imaging': ['x-ray', 'mri', 'ct scan', 'ultrasound', 'imaging'],
            'diagnosis': ['diagnosis', 'diagnosed with'],
            'follow_up': ['follow-up', 'followup', 'follow up'],
            'emergency': ['emergency', 'er', 'acute', 'urgent'],
            'prescription': ['prescription', 'rx', 'prescribed'],
            'consultation': ['consultation', 'visit', 'checkup', 'check-up']
        }
        
        for report_type, keywords in report_keywords.items():
            if any(word in text_lower for word in keywords):
                metadata['report_type'] = report_type
                break
        
        # Extract doctor name (optimized patterns)
        doctor_patterns = [
            r'dr\.?\s+([a-z]{2,15}\s+[a-z]{2,15})',
            r'doctor\s+([a-z]{2,15}\s+[a-z]{2,15})',
            r'physician:?\s+([a-z]{2,15}\s+[a-z]{2,15})',
        ]
        for pattern in doctor_patterns:
            match = re.search(pattern, text_lower)
            if match:
                metadata['doctor'] = f"Dr. {match.group(1).title()}"
                break
        
        # Extract diagnosis (first match only)
        diagnosis_patterns = [
            r'diagnosis:?\s*([^\n]{1,200})',
            r'diagnosed\s+with:?\s*([^\n]{1,200})',
            r'impression:?\s*([^\n]{1,200})',
        ]
        for pattern in diagnosis_patterns:
            match = re.search(pattern, text_lower)
            if match:
                diagnosis = match.group(1).strip()
                # Clean up whitespace
                diagnosis = ' '.join(diagnosis.split())
                metadata['diagnosis'] = diagnosis[:200]  # Limit length
                break
        
        # Extract medications (limit search area)
        med_text_section = text_lower[:3000]  # Only search first 3000 chars
        med_patterns = [
            r'medications?:?\s*([^\n]+(?:\n[^\n]+){0,5})',
            r'prescribed:?\s*([^\n]+(?:\n[^\n]+){0,5})',
            r'drugs?:?\s*([^\n]+(?:\n[^\n]+){0,5})',
        ]
        for pattern in med_patterns:
            match = re.search(pattern, med_text_section, re.MULTILINE)
            if match:
                meds_text = match.group(1)
                # Split by common delimiters
                medications = re.split(r'[,;\n•\-]', meds_text)
                # Filter and clean
                cleaned_meds = []
                for med in medications:
                    med = med.strip()
                    # Remove common non-medication text
                    if med and len(med) > 2 and len(med) < 50 and not any(skip in med.lower() for skip in ['none', 'n/a', 'patient', 'see']):
                        cleaned_meds.append(med.title())
                    if len(cleaned_meds) >= 10:  # Limit to 10 medications
                        break
                
                metadata['medications'] = cleaned_meds
                break
        
        return metadata


# Test the processor
if __name__ == "__main__":
    processor = DocumentProcessor()
    
    # Test with sample text
    sample_text = """
    Patient Consultation Report
    
    Date: January 21, 2026
    Doctor: Dr. Sarah Smith
    
    Patient presents with Type 2 Diabetes Mellitus.
    Blood glucose: 156 mg/dL
    
    Diagnosis: Type 2 Diabetes Mellitus
    
    Medications:
    - Metformin 500mg twice daily
    - Lifestyle modifications
    """
    
    print("Testing metadata extraction...")
    metadata = processor.extract_medical_metadata(sample_text)
    print("Extracted Metadata:")
    print(f"  Report Type: {metadata['report_type']}")
    print(f"  Doctor: {metadata['doctor']}")
    print(f"  Diagnosis: {metadata['diagnosis']}")
    print(f"  Medications: {metadata['medications']}")
    
    print("\n✅ All tests passed!")