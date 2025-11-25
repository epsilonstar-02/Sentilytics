import os
import json
import glob
import re
from typing import List, Dict, Any, Optional
from functools import lru_cache
from collections import defaultdict, Counter

from agents.chatbot.tools.constants import normalize_product_name

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data_collector/data/transcripts"))

@lru_cache(maxsize=4)
def load_transcripts(product: str = None) -> List[Dict[str, Any]]:
    """Loads transcripts for a specific product or all products. Cached for performance."""
    all_data = []
    
    search_path = os.path.join(DATA_DIR, "**", "*.json")
    if product:
        normalized = normalize_product_name(product)
        search_path = os.path.join(DATA_DIR, normalized, "*.json")

    files = glob.glob(search_path, recursive=True)
    
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                else:
                    all_data.append(data)
        except Exception as e:
            print(f"Error reading {file}: {e}")
            
    return all_data

def search_transcripts(query: str, product: str = None) -> List[Dict[str, Any]]:
    """
    Searches transcripts for the query string.
    Returns a list of results with video_id, title, and the snippet of the transcript.
    """
    data = load_transcripts(product)
    results = []
    query_lower = query.lower()
    
    for item in data:
        transcript = item.get('transcript', '')
        if query_lower in transcript.lower():
            # Find the position and extract a snippet
            idx = transcript.lower().find(query_lower)
            start = max(0, idx - 50)
            end = min(len(transcript), idx + len(query) + 50)
            snippet = "..." + transcript[start:end] + "..."
            
            results.append({
                'video_id': item.get('video_id'),
                'title': item.get('title'),
                'url': item.get('url'),
                'snippet': snippet,
                'full_transcript': transcript # Optional, might be too large
            })
            
    return results

def search_transcripts_multi_term(terms: List[str], product: str = None, match_all: bool = False) -> List[Dict[str, Any]]:
    """
    Searches transcripts for multiple terms.
    match_all=True: Returns videos containing ALL terms
    match_all=False: Returns videos containing ANY term
    """
    data = load_transcripts(product)
    results = []
    terms_lower = [term.lower() for term in terms]
    
    for item in data:
        transcript = item.get('transcript', '').lower()
        
        if match_all:
            if all(term in transcript for term in terms_lower):
                matches = {term: transcript.count(term) for term in terms_lower}
                results.append({
                    'video_id': item.get('video_id'),
                    'title': item.get('title'),
                    'url': item.get('url'),
                    'product': item.get('product'),
                    'matches': matches,
                    'total_matches': sum(matches.values())
                })
        else:
            matching_terms = [term for term in terms_lower if term in transcript]
            if matching_terms:
                matches = {term: transcript.count(term) for term in matching_terms}
                results.append({
                    'video_id': item.get('video_id'),
                    'title': item.get('title'),
                    'url': item.get('url'),
                    'product': item.get('product'),
                    'matches': matches,
                    'total_matches': sum(matches.values())
                })
    
    # Sort by total matches
    results.sort(key=lambda x: x['total_matches'], reverse=True)
    return results

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
