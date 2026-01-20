from sentence_transformers import SentenceTransformer
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch

class EmbeddingGenerator:
    def __init__(self):
        # Text embeddings
        self.text_model = SentenceTransformer(
            'sentence-transformers/all-mpnet-base-v2'
        )
        
        # Image embeddings
        self.image_model = CLIPModel.from_pretrained(
            "openai/clip-vit-base-patch32"
        )
        self.image_processor = CLIPProcessor.from_pretrained(
            "openai/clip-vit-base-patch32"
        )
    
    def encode_text(self, text):
        return self.text_model.encode(text).tolist()
    
    def encode_image(self, image_path):
        image = Image.open(image_path).convert("RGB")
        inputs = self.image_processor(
            images=image, 
            return_tensors="pt"
        )
        
        with torch.no_grad():
            image_features = self.image_model.get_image_features(
                **inputs
            )
        
        return image_features[0].cpu().numpy().tolist()