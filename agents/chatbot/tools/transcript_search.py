import os
import sys
import json
import glob
import re
from typing import List, Dict, Any, Optional
from functools import lru_cache
from collections import defaultdict, Counter
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

from agents.chatbot.tools.constants import normalize_product_name

# Load environment variables
load_dotenv()

# Add database directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from database.db_config import get_db_session
from sqlalchemy import text

logger = logging.getLogger(__name__)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data_collector/data/transcripts"))

# Initialize Google Gen AI Client
try:
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise KeyError("GOOGLE_API_KEY not found")
    client = genai.Client(api_key=api_key)
except Exception as e:
    logger.warning(f"Failed to initialize Google Gen AI client: {e}. Vector search will not work.")
    client = None

def get_embedding(text_content: str) -> List[float]:
    """Generates embedding for the given text using Google Gen AI."""
    if not client:
        raise ValueError("Google Gen AI client not initialized. Check GOOGLE_API_KEY.")
    
    response = client.models.embed_content(
        model="text-embedding-004",
        contents=text_content,
    )
    return response.embeddings[0].values

def search_transcripts_vector(query: str, product: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Searches transcripts using vector similarity search (simulating AlloyDB).
    """
    try:
        query_embedding = get_embedding(query)
        
        with get_db_session() as session:
            # SQL for vector similarity search using pgvector's <=> operator (cosine distance)
            sql = """
                SELECT 
                    tc.video_id,
                    tc.content as snippet,
                    tc.chunk_index,
                    v.title,
                    v.url,
                    p.name as product_name,
                    1 - (tc.embedding <=> :query_embedding) as similarity
                FROM transcript_chunks tc
                JOIN videos v ON tc.video_id = v.video_id
                JOIN products p ON v.product_id = p.id
                WHERE 1=1
            """
            
            params = {"query_embedding": str(query_embedding), "limit": limit}
            
            if product:
                sql += " AND p.name = :product_name"
                params["product_name"] = product
            
            sql += " ORDER BY tc.embedding <=> :query_embedding ASC LIMIT :limit"
            
            result = session.execute(text(sql), params)
            
            results = []
            for row in result:
                results.append({
                    'video_id': row.video_id,
                    'title': row.title,
                    'url': row.url,
                    'snippet': row.snippet,
                    'chunk_index': row.chunk_index,
                    'product': row.product_name,
                    'similarity': float(row.similarity)
                })
            
            logger.info(f"Found {len(results)} vector matches for '{query}'")
            return results
            
    except Exception as e:
        logger.error(f"Error in vector search: {e}")
        return []

@lru_cache(maxsize=10)
def load_transcripts(product: str = None) -> List[Dict[str, Any]]:
    """
    Loads transcripts for a specific product or all products from PostgreSQL.
    Cached for performance.
    """
    try:
        with get_db_session() as session:
            if product:
                query = text("""
                    SELECT 
                        t.video_id,
                        t.transcript,
                        t.word_count,
                        v.title,
                        v.url,
                        p.name as product_name
                    FROM transcripts t
                    JOIN videos v ON t.video_id = v.video_id
                    JOIN products p ON v.product_id = p.id
                    WHERE p.name = :product_name
                    ORDER BY t.created_at DESC
                """)
                result = session.execute(query, {"product_name": product})
            else:
                query = text("""
                    SELECT 
                        t.video_id,
                        t.transcript,
                        t.word_count,
                        v.title,
                        v.url,
                        p.name as product_name
                    FROM transcripts t
                    JOIN videos v ON t.video_id = v.video_id
                    JOIN products p ON v.product_id = p.id
                    ORDER BY t.created_at DESC
                """)
                result = session.execute(query)
            
            # Convert to old format
            all_data = []
            for row in result:
                all_data.append({
                    'video_id': row.video_id,
                    'transcript': row.transcript,
                    'word_count': row.word_count,
                    'title': row.title,
                    'url': row.url,
                    'product': row.product_name
                })
            
            logger.info(f"Loaded {len(all_data)} transcripts from database for product: {product or 'all'}")
            return all_data
            
    except Exception as e:
        logger.error(f"Error loading transcripts from database: {e}")
        return []


def search_transcripts_keyword(query: str, product: str = None) -> List[Dict[str, Any]]:
    """
    Searches transcripts for the query string using PostgreSQL full-text search.
    Returns a list of results with video_id, title, and the snippet of the transcript.
    """
    try:
        with get_db_session() as session:
            sql = """
                SELECT 
                    t.video_id,
                    v.title,
                    v.url,
                    ts_headline('english', t.transcript, 
                               to_tsquery('english', :search_query),
                               'MaxWords=50, MinWords=10') as snippet,
                    t.transcript as full_transcript,
                    p.name as product_name
                FROM transcripts t
                JOIN videos v ON t.video_id = v.video_id
                JOIN products p ON v.product_id = p.id
                WHERE to_tsvector('english', t.transcript) @@ to_tsquery('english', :search_query)
            """
            
            params = {"search_query": query.replace(' ', ' & ')}
            
            if product:
                sql += " AND p.name = :product_name"
                params["product_name"] = product
            
            sql += " ORDER BY ts_rank(to_tsvector('english', t.transcript), to_tsquery('english', :search_query)) DESC LIMIT 100"
            
            result = session.execute(text(sql), params)
            
            results = []
            for row in result:
                results.append({
                    'video_id': row.video_id,
                    'title': row.title,
                    'url': row.url,
                    'snippet': row.snippet,
                    'product': row.product_name,
                    'full_transcript': row.full_transcript
                })
            
            logger.info(f"Found {len(results)} transcripts matching '{query}' (keyword search)")
            return results
            
    except Exception as e:
        logger.error(f"Error searching transcripts: {e}")
        return []

def search_transcripts(query: str, product: str = None) -> List[Dict[str, Any]]:
    """
    Primary search function. Uses Vector Search (AlloyDB style) for semantic retrieval.
    Falls back to keyword search if vector search fails or returns no results.
    """
    # Try vector search first
    results = search_transcripts_vector(query, product)
    
    if not results:
        logger.info("Vector search returned no results, falling back to keyword search.")
        return search_transcripts_keyword(query, product)
        
    return results



def search_transcripts_multi_term(terms: List[str], product: str = None, match_all: bool = False) -> List[Dict[str, Any]]:
    """
    Searches transcripts for multiple terms using PostgreSQL.
    match_all=True: Returns videos containing ALL terms (AND)
    match_all=False: Returns videos containing ANY term (OR)
    """
    try:
        with get_db_session() as session:
            # Build query based on match_all
            if match_all:
                # All terms must be present (AND)
                search_query = ' & '.join(terms)
            else:
                # Any term can be present (OR)
                search_query = ' | '.join(terms)
            
            sql = """
                SELECT 
                    t.video_id,
                    v.title,
                    v.url,
                    t.transcript,
                    p.name as product_name,
                    ts_rank(to_tsvector('english', t.transcript), 
                           to_tsquery('english', :search_query)) as rank
                FROM transcripts t
                JOIN videos v ON t.video_id = v.video_id
                JOIN products p ON v.product_id = p.id
                WHERE to_tsvector('english', t.transcript) @@ to_tsquery('english', :search_query)
            """
            
            params = {"search_query": search_query}
            
            if product:
                sql += " AND p.name = :product_name"
                params["product_name"] = product
            
            sql += " ORDER BY rank DESC LIMIT 100"
            
            result = session.execute(text(sql), params)
            
            results = []
            for row in result:
                transcript = row.transcript
                
                # Count matches for each term
                matches = {}
                for term in terms:
                    matches[term] = transcript.lower().count(term.lower())
                
                results.append({
                    'video_id': row.video_id,
                    'title': row.title,
                    'url': row.url,
                    'product': row.product_name,
                    'matches': matches,
                    'total_matches': sum(matches.values()),
                    'full_transcript': transcript
                })
            
            logger.info(f"Found {len(results)} transcripts with terms: {terms}")
            return results
            
    except Exception as e:
        logger.error(f"Error searching multi-term transcripts: {e}")
        return []


def extract_topics(product: str = None, top_n: int = 20) -> List[Dict[str, Any]]:
    """
    Extracts common topics/keywords from transcripts using frequency analysis.
    Returns the most frequently mentioned terms.
    """
    data = load_transcripts(product)
    
    # Common stop words to filter out
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                  'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
                  'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
                  'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
                  'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
                  'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'just',
                  'now', 'there', 'here', 'then', 'also', 'up', 'out', 'if', 'about',
                  'into', 'through', 'during', 'before', 'after', 'above', 'below', 'like'}
    
    word_freq = Counter()
    
    for item in data:
        transcript = item.get('transcript', '')
        # Simple tokenization
        words = re.findall(r'\b[a-z]{3,}\b', transcript.lower())
        # Filter stop words
        filtered_words = [w for w in words if w not in stop_words]
        word_freq.update(filtered_words)
    
    # Get top N terms+1
    top_terms = [{'term': term, 'frequency': freq} for term, freq in word_freq.most_common(top_n)]
    
    return top_terms

def compare_transcript_coverage(product_list: List[str], topic: str) -> Dict[str, Any]:
    """
    Compares how much different products' videos discuss a specific topic.
    """
    results = {}
    topic_lower = topic.lower()
    
    for product in product_list:
        data = load_transcripts(product)
        
        videos_mentioning = 0
        total_mentions = 0
        videos_with_details = []
        
        for item in data:
            transcript = item.get('transcript', '').lower()
            count = transcript.count(topic_lower)
            
            if count > 0:
                videos_mentioning += 1
                total_mentions += count
                videos_with_details.append({
                    'video_id': item.get('video_id'),
                    'title': item.get('title'),
                    'mentions': count
                })
        
        # Sort videos by mentions
        videos_with_details.sort(key=lambda x: x['mentions'], reverse=True)
        
        results[product] = {
            'total_videos': len(data),
            'videos_mentioning_topic': videos_mentioning,
            'total_mentions': total_mentions,
            'mention_rate': (videos_mentioning / len(data) * 100) if data else 0,
            'avg_mentions_per_video': (total_mentions / videos_mentioning) if videos_mentioning > 0 else 0,
            'top_videos': videos_with_details[:5]
        }
    
    return {
        'topic': topic,
        'products': results
    }

def get_transcript_statistics(product: str = None) -> Dict[str, Any]:
    """
    Provides statistical overview of transcript data.
    """
    data = load_transcripts(product)
    
    if not data:
        return {'error': 'No transcript data found'}
    
    lengths = []
    word_counts = []
    
    for item in data:
        transcript = item.get('transcript', '')
        lengths.append(len(transcript))
        word_counts.append(len(transcript.split()))
    
    import statistics
    
    return {
        'product': product or 'All Products',
        'total_transcripts': len(data),
        'avg_length_chars': round(statistics.mean(lengths)),
        'median_length_chars': round(statistics.median(lengths)),
        'avg_word_count': round(statistics.mean(word_counts)),
        'median_word_count': round(statistics.median(word_counts)),
        'total_words': sum(word_counts)
    }
