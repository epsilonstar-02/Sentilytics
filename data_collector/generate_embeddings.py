import os
import sys
import time
import logging
from typing import List
from dotenv import load_dotenv
from sqlalchemy import text
from google import genai

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db_config import get_db_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('embedding_generation.log')
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration
CHUNK_SIZE = 1000  # Characters
CHUNK_OVERLAP = 100
MODEL_NAME = "text-embedding-004"

def get_genai_client():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found")
    return genai.Client(api_key=api_key)

def chunk_text(text: str, size: int, overlap: int) -> List[str]:
    """Simple sliding window chunking."""
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + size
        chunk = text[start:end]
        chunks.append(chunk)
        
        if end >= text_len:
            break
            
        start += size - overlap
        
    return chunks

def generate_embeddings(client, texts: List[str]):
    """Generate embeddings for a batch of texts."""
    try:
        embeddings = []
        for text_chunk in texts:
            response = client.models.embed_content(
                model=MODEL_NAME,
                contents=text_chunk
            )
            # Handle different response structures if needed
            if hasattr(response, 'embeddings') and response.embeddings:
                embeddings.append(response.embeddings[0].values)
            else:
                # Fallback or error
                logger.warning("Unexpected embedding response structure")
                
            # Rate limit protection (simple)
            time.sleep(0.05) 
            
        return embeddings
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise

def main():
    logger.info("Starting embedding generation...")
    client = get_genai_client()
    
    with get_db_session() as session:
        # 1. Get all transcripts
        logger.info("Fetching transcripts from database...")
        result = session.execute(text("SELECT video_id, transcript FROM transcripts"))
        transcripts = result.fetchall()
        logger.info(f"Found {len(transcripts)} transcripts to process.")
        
        total_chunks = 0
        processed_videos = 0
        
        for video_id, transcript_text in transcripts:
            if not transcript_text:
                continue
                
            # Check if already processed
            existing = session.execute(
                text("SELECT 1 FROM transcript_chunks WHERE video_id = :vid LIMIT 1"),
                {"vid": video_id}
            ).fetchone()
            
            if existing:
                # logger.info(f"Skipping video {video_id} (already processed)")
                continue

            # Chunking
            chunks = chunk_text(transcript_text, CHUNK_SIZE, CHUNK_OVERLAP)
            if not chunks:
                continue
                
            try:
                # Generate embeddings
                embeddings = generate_embeddings(client, chunks)
                
                if len(embeddings) != len(chunks):
                    logger.error(f"Mismatch in chunks vs embeddings for {video_id}")
                    continue

                # Insert into DB
                for i, (chunk_content, embedding) in enumerate(zip(chunks, embeddings)):
                    session.execute(
                        text("""
                            INSERT INTO transcript_chunks (video_id, chunk_index, content, embedding)
                            VALUES (:vid, :idx, :content, :emb)
                        """),
                        {
                            "vid": video_id,
                            "idx": i,
                            "content": chunk_content,
                            "emb": embedding
                        }
                    )
                
                session.commit()
                total_chunks += len(chunks)
                processed_videos += 1
                
                if processed_videos % 10 == 0:
                    logger.info(f"Processed {processed_videos} videos ({total_chunks} chunks generated)")
                    
            except Exception as e:
                logger.error(f"Failed to process video {video_id}: {e}")
                session.rollback()
                continue
                
    logger.info(f"✅ Completed! Processed {processed_videos} videos, created {total_chunks} chunks.")

if __name__ == "__main__":
    main()
