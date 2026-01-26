🏥 HEALTHCARE MEMORY ASSISTANT AI AGENT

The Healthcare Memory Assistant is an intelligent agent designed to create a longitudinal "memory" of patient care. It ingests clinical documents and medical images, converting them into a unified vector space for semantic retrieval and clinical decision support.

🛠 Required Dependencies
To run the agent, you must install the following libraries categorized by their role in the pipeline:

1. Core AI & Vector Search

    (a)torch, torchvision: Handles GPU-accelerated tensor computations for embeddings.

    (b)sentence-transformers: Powers text vectorization using the all-mpnet-base-v2 model.

    (c)transformers: Provides the CLIP model for medical image vectorization.

    (d)qdrant-client: Interface for the vector database storage and retrieval.

3. Document & Image Processing

   (a)PyPDF2: Required for extracting clinical text from PDF reports.

    (a)python-docx: Used for parsing Microsoft Word clinical documents.

    (b)Pillow (PIL): Essential for processing and normalizing medical images.

5. System Utilities

    (a)python-dotenv: Manages secure environment variables like Qdrant API keys.

    (b)pathlib, re: Handles file system paths and complex regex-based metadata extraction.

Now, running in your environment

Clone the repo in your env 

run in your terminal --> git clone <given_git_repository_link>

Install required dependencies to run Agent on your env

run in your terminal --> pip install -r requirements.txt
Also add some more dependencies --> pip install pytesseract opencv-python

Setup Qdrant using Qdrant Cloud (Recommended for Production)

1. Sign up at cloud.qdrant.io

2. Create a cluster-->Get credentials:

3. Copy your Cluster URL (looks like: https://abc123.aws.cloud.qdrant.io:6333)
    Go to "API Keys" tab
    Click "Generate API Key"
    Copy and save the API key (you won't see it again!)

Now, create .env file and use your credentials to use the Health Memory Assistant
Inside .env :
#Qdrant_Cloud_Configuration

QDRANT_URL=<your Qdrant URL>
QDRANT_API_KEY=<your created API key>

Then, install tesseract OCR for better image procesing, using https://github.com/UB-Mannheim/tesseract/wiki
and save into program files(by default don't change) and must keep name as tesseract of the installed file 

NOTE:- Initial run may take some time to install and load some more dependencies.
Then upload demo medical record folder file using batch folder upload option of interactive_CLI
After that you can check patient history, timeline and other query using the CLI.

📊 Agent Logic Overview

1. Ingestion: The DocumentProcessor parses raw files into structured text or image paths.
2. Vectorization: The EmbeddingGenerator creates 768-dimensional text vectors or 512-dimensional image vectors.
3. Memory Storage: The DataIngestionPipeline upserts these vectors to Qdrant with associated medical metadata.
4. Retrieval: The retrieval engine performs semantic search, allowing for natural language queries like "Show cardiac reports for patient P001 from last year".




