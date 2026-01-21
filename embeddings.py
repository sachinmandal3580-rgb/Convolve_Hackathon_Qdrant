"""
Embedding Generator - Converts text and images to vectors by creating small chunks/tokens
"""

from sentence_transformers import SentenceTransformer
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch

class EmbeddingGenerator:
    def __init__(self):
        """Initialize embedding models"""
        print("Loading embedding models...")
        
        # Text embeddings - 768 dimensions
        self.text_model = SentenceTransformer(
            'sentence-transformers/all-mpnet-base-v2'
        )
        print("Text model loaded")
        
        # Image embeddings - 512 dimensions
        self.image_model = CLIPModel.from_pretrained(
            "openai/clip-vit-base-patch32"
        )
        self.image_processor = CLIPProcessor.from_pretrained(
            "openai/clip-vit-base-patch32"
        )
        print("Image model loaded")
        print("Models are ready now!\n")
    
    def encode_text(self, text):
        """
        Convert text to 768-dimensional vector
        
        Args:
            text: String to encode
            
        Returns:
            List of 768 floats representing the text
        """
        return self.text_model.encode(text).tolist()
    
    def encode_image(self, image_path):
        """
        Convert image to 512-dimensional vector
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of 512 floats representing the image
        """
        try:
            image = Image.open(image_path).convert("RGB")
            inputs = self.image_processor(
                images=image, 
                return_tensors="pt"
            )
            
            with torch.no_grad():
                image_features = self.image_model.get_image_features(**inputs)
            
            return image_features[0].cpu().numpy().tolist()
        except Exception as e:
            print(f"Error encoding image {image_path}: {e}")
            raise
    
    def encode_batch_texts(self, texts):
        """
        Encode multiple texts at once (more efficient)
        
        Args:
            texts: List of strings
            
        Returns:
            List of embeddings
        """
        return self.text_model.encode(texts).tolist()