"""
Quick Fix Script - Add Indexes to Existing Qdrant Collections
Run this once to fix the "Index required" error
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType

load_dotenv()

def add_indexes_to_collections():
    """Add required indexes to all collections"""
    
    # Connect to Qdrant
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("QDRANT_API_KEY")
    
    print("Connecting to Qdrant...")
    client = QdrantClient(url=url, api_key=api_key, timeout=60)
    print(f"✓ Connected to: {url}\n")
    
    collections = ["patient_reports", "medical_images", "patient_timeline"]
    
    # Indexes to create for each collection
    indexes = [
        ("patient_id", PayloadSchemaType.KEYWORD, "For filtering by patient"),
        ("timestamp", PayloadSchemaType.FLOAT, "For date range queries"),
        ("report_type", PayloadSchemaType.KEYWORD, "For filtering by report type"),
        ("doctor", PayloadSchemaType.KEYWORD, "For filtering by doctor"),
        ("diagnosis", PayloadSchemaType.KEYWORD, "For filtering by diagnosis"),
    ]
    
    print("=" * 70)
    print("ADDING PAYLOAD INDEXES")
    print("=" * 70)
    
    for collection_name in collections:
        print(f"\n{collection_name}:")
        print("-" * 70)
        
        if not client.collection_exists(collection_name):
            print(f"  ⚠ Collection doesn't exist, skipping...")
            continue
        
        for field_name, field_type, description in indexes:
            try:
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
                print(f"  ✓ Created index: {field_name:15} ({description})")
                
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower():
                    print(f"  ℹ Index exists: {field_name:15} (skipping)")
                else:
                    print(f"  ⚠ Error on {field_name}: {error_msg[:50]}...")
    
    print("\n" + "=" * 70)
    print("✅ INDEX SETUP COMPLETE!")
    print("=" * 70)
    print("\nYou can now run your main application:")
    print("  python main.py")
    print()


def verify_indexes():
    """Verify that indexes were created successfully"""
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("QDRANT_API_KEY")
    
    client = QdrantClient(url=url, api_key=api_key, timeout=60)
    
    print("\n" + "=" * 70)
    print("VERIFYING INDEXES")
    print("=" * 70)
    
    collections = ["patient_reports", "medical_images", "patient_timeline"]
    
    for collection_name in collections:
        if not client.collection_exists(collection_name):
            continue
            
        print(f"\n{collection_name}:")
        try:
            info = client.get_collection(collection_name)
            
            if hasattr(info, 'payload_schema') and info.payload_schema:
                print("  Indexed fields:")
                for field, schema in info.payload_schema.items():
                    print(f"    - {field}: {schema}")
            else:
                print("  ℹ No payload schema information available")
                print("    (Indexes may still exist)")
                
        except Exception as e:
            print(f"  ⚠ Could not get collection info: {e}")


if __name__ == "__main__":
    print("=" * 70)
    print("QDRANT PAYLOAD INDEX FIX")
    print("=" * 70)
    print()
    print("This script will add required indexes to your Qdrant collections")
    print("to fix the 'Index required but not found' error.")
    print()
    
    try:
        add_indexes_to_collections()
        verify_indexes()
        
        print("\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print("""
1. Your indexes are now created
2. Run your main application: python main.py
3. Queries with filters should now work!

If you still see errors:
- Make sure all collections exist
- Try running this script again
- Check Qdrant logs for any issues
""")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\nTroubleshooting:")
        print("1. Make sure Qdrant is running")
        print("2. Check your .env file has correct credentials")
        print("3. Verify you can connect to Qdrant")