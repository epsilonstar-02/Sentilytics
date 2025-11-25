import os
import json
import glob
from typing import List, Dict, Any, Optional
from functools import lru_cache
from collections import defaultdict
import statistics

from agents.chatbot.tools.constants import normalize_product_name

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data_collector/sentiment_data"))

@lru_cache(maxsize=4)
def load_sentiment_data(product: str = None) -> List[Dict[str, Any]]:
    """Loads sentiment data for a specific product or all products."""
    all_data = []
    
    # Pattern to match both root files and nested files
    # e.g. iPhone_17_sentiment.json and ChatGPT_GPT-5/*.json
    
    if product:
        normalized = normalize_product_name(product)
        # Try to find specific file or folder
        # Case 1: product_sentiment.json in root
        root_file = os.path.join(DATA_DIR, f"{normalized}_sentiment.json")
        if os.path.exists(root_file):
             with open(root_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        all_data.append(data)
                except Exception as e:
                    print(f"Error reading {root_file}: {e}")
        
        # Case 2: Folder with json files
        folder_path = os.path.join(DATA_DIR, normalized, "*.json")
        files = glob.glob(folder_path)
        for file in files:
            with open(file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        all_data.append(data)
                except Exception as e:
                    print(f"Error reading {file}: {e}")

    else:
        # Load everything
        # Root json files
        root_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
        for file in root_files:
             with open(file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        all_data.append(data)
                except Exception as e:
                    print(f"Error reading {file}: {e}")
        
        # Nested json files
        nested_files = glob.glob(os.path.join(DATA_DIR, "**", "*.json"), recursive=True)
        # Avoid duplicates if root files are picked up by recursive glob (depends on implementation, but safe to check)
        processed_files = set(os.path.abspath(f) for f in root_files)
        
        for file in nested_files:
            if os.path.abspath(file) not in processed_files:
                with open(file, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        if isinstance(data, list):
                            all_data.extend(data)
                        else:
                            all_data.append(data)
                    except Exception as e:
                        print(f"Error reading {file}: {e}")
            
    return all_data

def get_sentiment_for_video(query: str) -> List[Dict[str, Any]]:
    """
    Searches for sentiment analysis of a video by title or video_id.
    """
    data = load_sentiment_data()
    results = []
    query_lower = query.lower()
    
    for item in data:
        title = item.get('title', '').lower()
        video_id = item.get('video_id', '').lower()
        
        if query_lower in title or query_lower == video_id:
            results.append(item)
            
    return results

def get_product_sentiment_summary(product_name: str) -> Dict[str, Any]:
    """
    Aggregates sentiment data for a specific product.
    Returns average score, common pros/cons (simplified), and overall sentiment distribution.
    """
    data = load_sentiment_data(product_name)
    
    if not data:
        # Try fuzzy match or searching in all data if product specific load failed
        all_data = load_sentiment_data()
        data = [d for d in all_data if product_name.lower() in d.get('product', '').lower()]
        
    if not data:
        return {"error": f"No sentiment data found for {product_name}"}
        
    total_score = 0
    count = 0
    sentiments = {}
    all_pros = []
    all_cons = []
    
    for item in data:
        analysis = item.get('sentiment_analysis', {})
        score = analysis.get('score')
        if score is not None:
            total_score += score
            count += 1
            
        sentiment = analysis.get('sentiment', 'Unknown')
        sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
        
        all_pros.extend(analysis.get('pros', []))
        all_cons.extend(analysis.get('cons', []))
        
    avg_score = total_score / count if count > 0 else 0
    
    return {
        "product": product_name,
        "video_count": len(data),
        "average_score": round(avg_score, 2),
        "sentiment_distribution": sentiments,
        "sample_pros": all_pros[:5], # Just take top 5 for now, could be more sophisticated
        "sample_cons": all_cons[:5]
    }

def get_sentiment_over_time(product_name: str) -> Dict[str, Any]:
    """
    Tracks sentiment changes over time for a product.
    Returns daily sentiment averages and trends.
    """
    data = load_sentiment_data(product_name)
    
    if not data:
        all_data = load_sentiment_data()
        data = [d for d in all_data if product_name.lower() in d.get('product', '').lower()]
    
    if not data:
        return {"error": f"No sentiment data found for {product_name}"}
    
    # Group by date
    daily_sentiment = defaultdict(lambda: {'scores': [], 'sentiments': []})
    
    for item in data:
        date = item.get('date')
        if not date:
            continue
        
        analysis = item.get('sentiment_analysis', {})
        score = analysis.get('score')
        sentiment = analysis.get('sentiment')
        
        if score is not None:
            daily_sentiment[date]['scores'].append(score)
        if sentiment:
            daily_sentiment[date]['sentiments'].append(sentiment)
    
    # Calculate daily averages
    daily_averages = {}
    for date, data_dict in sorted(daily_sentiment.items()):
        scores = data_dict['scores']
        sentiments = data_dict['sentiments']
        
        sentiment_counts = {}
        for s in sentiments:
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
        
        daily_averages[date] = {
            'average_score': round(statistics.mean(scores), 2) if scores else 0,
            'video_count': len(scores),
            'sentiment_distribution': sentiment_counts,
            'dominant_sentiment': max(sentiment_counts.items(), key=lambda x: x[1])[0] if sentiment_counts else 'Unknown'
        }
    
    # Calculate trend
    dates = sorted(daily_averages.keys())
    if len(dates) >= 2:
        first_avg = daily_averages[dates[0]]['average_score']
        last_avg = daily_averages[dates[-1]]['average_score']
        trend = 'improving' if last_avg > first_avg else 'declining' if last_avg < first_avg else 'stable'
        trend_change = round(last_avg - first_avg, 2)
    else:
        trend = 'insufficient data'
        trend_change = 0
    
    return {
        'product': product_name,
        'daily_sentiment': daily_averages,
        'trend': trend,
        'trend_change': trend_change,
        'date_range': f"{dates[0]} to {dates[-1]}" if dates else 'N/A'
    }

def compare_product_sentiments(product_list: List[str]) -> Dict[str, Any]:
    """
    Compares sentiment across multiple products.
    """
    comparison = {}
    
    for product in product_list:
        summary = get_product_sentiment_summary(product)
        
        if 'error' not in summary:
            comparison[product] = {
                'average_score': summary['average_score'],
                'video_count': summary['video_count'],
                'sentiment_distribution': summary['sentiment_distribution'],
                'dominant_sentiment': max(summary['sentiment_distribution'].items(), 
                                         key=lambda x: x[1])[0] if summary['sentiment_distribution'] else 'Unknown'
            }
        else:
            comparison[product] = {'error': 'No data'}
    
    # Rank by average score
    ranked = sorted([(k, v['average_score']) for k, v in comparison.items() if 'average_score' in v], 
                   key=lambda x: x[1], reverse=True)
    
    return {
        'comparison': comparison,
        'ranking': [{'product': p, 'score': s} for p, s in ranked]
    }

def get_sentiment_extremes(product_name: str, extreme_type: str = 'positive') -> List[Dict[str, Any]]:
    """
    Finds videos with extreme sentiment (most positive or most negative).
    extreme_type: 'positive' or 'negative'
    """
    data = load_sentiment_data(product_name)
    
    if not data:
        all_data = load_sentiment_data()
        data = [d for d in all_data if product_name.lower() in d.get('product', '').lower()]
    
    if not data:
        return []
    
    # Sort by score
    reverse = (extreme_type == 'positive')
    sorted_data = sorted(data, 
                        key=lambda x: x.get('sentiment_analysis', {}).get('score', 0), 
                        reverse=reverse)
    
    # Return top 5
    results = []
    for item in sorted_data[:5]:
        analysis = item.get('sentiment_analysis', {})
        results.append({
            'video_id': item.get('video_id'),
            'title': item.get('title'),
            'url': item.get('url'),
            'sentiment': analysis.get('sentiment'),
            'score': analysis.get('score'),
            'pros': analysis.get('pros', []),
            'cons': analysis.get('cons', []),
            'summary': analysis.get('summary')
        })
    
    return results

def analyze_sentiment_distribution(product_name: str) -> Dict[str, Any]:
    """
    Provides detailed sentiment distribution analysis.
    """
    data = load_sentiment_data(product_name)
    
    if not data:
        all_data = load_sentiment_data()
        data = [d for d in all_data if product_name.lower() in d.get('product', '').lower()]
    
    if not data:
        return {"error": f"No sentiment data found for {product_name}"}
    
    scores = []
    sentiments = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    
    # Score ranges
    score_ranges = {
        'Extremely Positive (9-10)': 0,
        'Positive (7-8.9)': 0,
        'Neutral (5-6.9)': 0,
        'Negative (3-4.9)': 0,
        'Extremely Negative (0-2.9)': 0
    }
    
    for item in data:
        analysis = item.get('sentiment_analysis', {})
        score = analysis.get('score')
        sentiment = analysis.get('sentiment', 'Unknown')
        
        if score is not None:
            scores.append(score)
            
            # Categorize into ranges
            if score >= 9:
                score_ranges['Extremely Positive (9-10)'] += 1
            elif score >= 7:
                score_ranges['Positive (7-8.9)'] += 1
            elif score >= 5:
                score_ranges['Neutral (5-6.9)'] += 1
            elif score >= 3:
                score_ranges['Negative (3-4.9)'] += 1
            else:
                score_ranges['Extremely Negative (0-2.9)'] += 1
        
        if sentiment in sentiments:
            sentiments[sentiment] += 1
    
    return {
        'product': product_name,
        'total_videos': len(data),
        'average_score': round(statistics.mean(scores), 2) if scores else 0,
        'median_score': round(statistics.median(scores), 2) if scores else 0,
        'std_dev': round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
        'score_ranges': score_ranges,
        'sentiment_categories': sentiments,
        'positive_percentage': round(sentiments['Positive'] / len(data) * 100, 1) if data else 0,
        'negative_percentage': round(sentiments['Negative'] / len(data) * 100, 1) if data else 0
    }
