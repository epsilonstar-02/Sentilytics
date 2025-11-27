import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for thread safety
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from scipy.interpolate import make_interp_spline
from scipy.ndimage import gaussian_filter1d
import os
import base64
from io import BytesIO
from typing import List, Dict, Any, Optional

# Set Seaborn style for better aesthetics
sns.set_theme(style="whitegrid", palette="husl")
sns.set_context("notebook", font_scale=1.1)

# Custom color palette for products
PRODUCT_COLORS = {
    "iPhone_17_Pro": "#007AFF",      # Apple Blue
    "MacBook_Pro_14-inch_M5": "#5856D6",  # Purple
    "ChatGPT_GPT-5": "#10A37F",      # OpenAI Green
}
DEFAULT_PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860"]


def _smooth_line(x_values: np.ndarray, y_values: np.ndarray, smoothing_factor: int = 300) -> tuple:
    """
    Smooths a line using spline interpolation for continuous data.
    Falls back to gaussian smoothing if spline fails.
    """
    try:
        if len(x_values) < 4:
            # Not enough points for spline, use gaussian smoothing
            y_smooth = gaussian_filter1d(y_values.astype(float), sigma=0.8)
            return x_values, y_smooth
        
        # Create numeric x values for interpolation
        x_numeric = np.arange(len(x_values))
        x_smooth = np.linspace(x_numeric.min(), x_numeric.max(), smoothing_factor)
        
        # Create spline
        spl = make_interp_spline(x_numeric, y_values.astype(float), k=min(3, len(x_values) - 1))
        y_smooth = spl(x_smooth)
        
        return x_smooth, y_smooth
    except Exception:
        # Fallback to gaussian smoothing
        y_smooth = gaussian_filter1d(y_values.astype(float), sigma=1.0)
        return np.arange(len(x_values)), y_smooth


def _save_and_encode_plot(filename_prefix: str) -> str:
    """
    Saves the current matplotlib figure to a file and returns a response 
    containing both the file path and the base64-encoded image for inline display.
    """
    plots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../plots"))
    os.makedirs(plots_dir, exist_ok=True)
    
    filename = f"{filename_prefix}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(plots_dir, filename)
    
    # Save to file
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    
    # Also encode as base64 for inline display
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    
    plt.close()
    
    # Return both the path and base64 data in a structured format
    return f"![Plot]({filepath})\n\n[IMAGE_BASE64:{img_base64}]\n\nPlot saved to: {filepath}"


def generate_plot(data: List[Dict[str, Any]], x_key: str, y_key: str, title: str = "Plot", plot_type: str = "line", smooth: bool = True):
    """
    Generates a plot from a list of dictionaries.
    Returns the path to the saved image or base64 string.
    Uses Seaborn for enhanced aesthetics with optional line smoothing.
    """
    if not data:
        return "No data to plot."

    df = pd.DataFrame(data)
    
    # Ensure keys exist
    if x_key not in df.columns or y_key not in df.columns:
        return f"Keys {x_key} or {y_key} not found in data."

    # Convert numeric if needed
    try:
        df[y_key] = pd.to_numeric(df[y_key])
    except:
        pass
        
    fig, ax = plt.subplots(figsize=(12, 7))
    
    if plot_type == "line":
        if smooth and len(df) >= 3:
            # Plot smoothed line
            x_smooth, y_smooth = _smooth_line(np.arange(len(df)), df[y_key].values)
            ax.plot(x_smooth, y_smooth, linewidth=2.5, color=DEFAULT_PALETTE[0], alpha=0.9)
            # Add original data points
            ax.scatter(np.arange(len(df)), df[y_key], s=80, color=DEFAULT_PALETTE[0], 
                      edgecolor='white', linewidth=2, zorder=5, alpha=0.9)
            ax.set_xticks(np.arange(len(df)))
            ax.set_xticklabels(df[x_key], rotation=45, ha='right')
        else:
            sns.lineplot(data=df, x=x_key, y=y_key, ax=ax, marker='o', 
                        linewidth=2.5, markersize=10, color=DEFAULT_PALETTE[0])
    elif plot_type == "bar":
        sns.barplot(data=df, x=x_key, y=y_key, ax=ax, palette=DEFAULT_PALETTE, 
                   edgecolor='white', linewidth=1.5)
    elif plot_type == "scatter":
        sns.scatterplot(data=df, x=x_key, y=y_key, ax=ax, s=120, 
                       color=DEFAULT_PALETTE[0], edgecolor='white', linewidth=1.5)
        
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel(x_key, fontsize=13, labelpad=10)
    ax.set_ylabel(y_key, fontsize=13, labelpad=10)
    plt.xticks(rotation=45, ha='right')
    
    # Enhanced grid
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    sns.despine(left=True, bottom=True)
    plt.tight_layout()
    
    return _save_and_encode_plot("plot")

def generate_time_series_plot(daily_data: Dict[str, Any], metric_name: str, title: str, smooth: bool = True) -> str:
    """
    Generates a time series plot from daily aggregated data.
    Handles both simple {date: value} and nested {date: {metric: value}} formats.
    Uses Seaborn styling with optional smoothed lines.
    """
    if not daily_data:
        return "No data to plot."
    
    dates = sorted(daily_data.keys())
    
    # Handle nested dict structure (e.g., from get_sentiment_over_time)
    first_value = daily_data[dates[0]]
    if isinstance(first_value, dict):
        # Try common metric keys
        metric_key = None
        for key in ['average_score', 'score', 'value', 'count', metric_name.lower().replace(' ', '_')]:
            if key in first_value:
                metric_key = key
                break
        
        if metric_key is None:
            # Just use the first numeric value found
            for key, val in first_value.items():
                if isinstance(val, (int, float)):
                    metric_key = key
                    break
        
        if metric_key is None:
            return f"No numeric data found to plot in the daily data structure."
        
        values = [daily_data[date].get(metric_key, 0) for date in dates]
    else:
        values = [daily_data[date] for date in dates]
    
    values = np.array(values, dtype=float)
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    if smooth and len(dates) >= 3:
        # Plot smoothed trend line
        x_smooth, y_smooth = _smooth_line(np.arange(len(dates)), values)
        ax.plot(x_smooth, y_smooth, linewidth=3, color=DEFAULT_PALETTE[0], 
               alpha=0.8, label='Trend')
        # Add light fill under the curve
        ax.fill_between(x_smooth, y_smooth, alpha=0.15, color=DEFAULT_PALETTE[0])
        # Add original data points
        ax.scatter(np.arange(len(dates)), values, s=100, color=DEFAULT_PALETTE[0], 
                  edgecolor='white', linewidth=2.5, zorder=5, label='Daily Value')
        ax.set_xticks(np.arange(len(dates)))
        ax.set_xticklabels(dates, rotation=45, ha='right')
    else:
        ax.plot(dates, values, marker='o', linewidth=2.5, markersize=10, 
               color=DEFAULT_PALETTE[0])
        ax.fill_between(dates, values, alpha=0.15, color=DEFAULT_PALETTE[0])
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=13, labelpad=10)
    ax.set_ylabel(metric_name, fontsize=13, labelpad=10)
    
    # Enhanced grid
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    if smooth and len(dates) >= 3:
        ax.legend(loc='best', fontsize=11, framealpha=0.9)
    
    sns.despine(left=True, bottom=True)
    plt.tight_layout()
    
    return _save_and_encode_plot("timeseries")

def generate_comparison_plot(comparison_data: Dict[str, float], title: str, ylabel: str) -> str:
    """
    Generates a bar chart comparing multiple products or metrics.
    Uses Seaborn for enhanced aesthetics with product-specific colors.
    """
    if not comparison_data:
        return "No data to plot."
    
    products = list(comparison_data.keys())
    values = list(comparison_data.values())
    
    # Get product-specific colors or use defaults
    colors = [PRODUCT_COLORS.get(p, DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)]) 
              for i, p in enumerate(products)]
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Create bars with Seaborn styling
    bars = ax.bar(products, values, color=colors, edgecolor='white', linewidth=2, width=0.6)
    
    # Add value labels on bars with improved styling
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                   xy=(bar.get_x() + bar.get_width()/2., height),
                   xytext=(0, 8),
                   textcoords='offset points',
                   ha='center', va='bottom',
                   fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                           edgecolor='gray', alpha=0.8))
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel(ylabel, fontsize=13, labelpad=10)
    ax.set_xlabel('Product', fontsize=13, labelpad=10)
    plt.xticks(rotation=45, ha='right', fontsize=11)
    
    # Enhanced grid (y-axis only)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.set_axisbelow(True)
    
    # Add subtle gradient effect by adjusting y-limit
    ax.set_ylim(0, max(values) * 1.15)
    
    sns.despine(left=True, bottom=True)
    plt.tight_layout()
    
    return _save_and_encode_plot("comparison")

def generate_sentiment_distribution_plot(sentiment_data: Dict[str, int], title: str) -> str:
    """
    Generates a pie/donut chart for sentiment distribution with Seaborn styling.
    """
    if not sentiment_data:
        return "No data to plot."
    
    labels = list(sentiment_data.keys())
    sizes = list(sentiment_data.values())
    
    # Sentiment-specific colors (green=positive, red=negative, gray=neutral)
    color_map = {
        'positive': '#2ecc71', 'Positive': '#2ecc71',
        'negative': '#e74c3c', 'Negative': '#e74c3c',
        'neutral': '#95a5a6', 'Neutral': '#95a5a6',
        'mixed': '#f39c12', 'Mixed': '#f39c12'
    }
    colors = [color_map.get(label, DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)]) 
              for i, label in enumerate(labels)]
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Create donut chart (more modern look)
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%', 
        startangle=90, 
        colors=colors,
        explode=[0.02] * len(sizes),  # Slight separation
        wedgeprops=dict(width=0.6, edgecolor='white', linewidth=3),
        textprops={'fontsize': 13, 'fontweight': 'bold'},
        pctdistance=0.75
    )
    
    # Style the percentage labels
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(12)
        autotext.set_fontweight('bold')
    
    # Add center circle for donut effect
    centre_circle = plt.Circle((0, 0), 0.35, fc='white')
    ax.add_artist(centre_circle)
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.axis('equal')
    
    # Add legend
    ax.legend(wedges, [f'{l}: {s}' for l, s in zip(labels, sizes)],
             title="Sentiment", loc="center left", bbox_to_anchor=(0.9, 0.5),
             fontsize=11)
    
    plt.tight_layout()
    
    return _save_and_encode_plot("sentiment")

def generate_multi_product_trend_plot(products_data: Dict[str, Dict[str, Any]], metric_name: str, title: str, smooth: bool = True) -> str:
    """
    Generates a multi-line plot comparing trends across products over time.
    products_data format: {product_name: {date: value}} or {product_name: {date: {metric: value}}}
    Uses Seaborn styling with optional smoothed lines.
    """
    if not products_data:
        return "No data to plot."
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    for idx, (product, daily_data) in enumerate(products_data.items()):
        if not daily_data:
            continue
            
        dates = sorted(daily_data.keys())
        
        # Handle nested dict structure
        first_value = daily_data[dates[0]]
        if isinstance(first_value, dict):
            # Try to find numeric value
            metric_key = None
            for key in ['average_score', 'score', 'value', 'count']:
                if key in first_value:
                    metric_key = key
                    break
            
            if metric_key is None:
                for key, val in first_value.items():
                    if isinstance(val, (int, float)):
                        metric_key = key
                        break
            
            if metric_key:
                values = [daily_data[date].get(metric_key, 0) for date in dates]
            else:
                continue  # Skip this product if no numeric data
        else:
            values = [daily_data[date] for date in dates]
        
        values = np.array(values, dtype=float)
        
        # Get product-specific color or use palette
        color = PRODUCT_COLORS.get(product, DEFAULT_PALETTE[idx % len(DEFAULT_PALETTE)])
        
        if smooth and len(dates) >= 3:
            # Plot smoothed trend line
            x_smooth, y_smooth = _smooth_line(np.arange(len(dates)), values)
            ax.plot(x_smooth, y_smooth, linewidth=3, color=color, 
                   alpha=0.85, label=f'{product} (trend)')
            # Add original data points
            ax.scatter(np.arange(len(dates)), values, s=80, color=color, 
                      edgecolor='white', linewidth=2, zorder=5, alpha=0.9)
        else:
            ax.plot(np.arange(len(dates)), values, marker='o', label=product, 
                   linewidth=2.5, markersize=8, color=color)
    
    # Set x-axis labels from the first product's dates
    if products_data:
        first_product_data = list(products_data.values())[0]
        if first_product_data:
            all_dates = sorted(first_product_data.keys())
            ax.set_xticks(np.arange(len(all_dates)))
            ax.set_xticklabels(all_dates, rotation=45, ha='right')
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=13, labelpad=10)
    ax.set_ylabel(metric_name, fontsize=13, labelpad=10)
    
    # Enhanced legend
    ax.legend(loc='best', fontsize=11, framealpha=0.9, fancybox=True, shadow=True)
    
    # Enhanced grid
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    sns.despine(left=True, bottom=True)
    plt.tight_layout()
    
    return _save_and_encode_plot("multi_trend")

def generate_heatmap(data_matrix: List[List[float]], x_labels: List[str], y_labels: List[str], title: str) -> str:
    """
    Generates a heatmap visualization using Seaborn.
    """
    if not data_matrix:
        return "No data to plot."
    
    # Convert to DataFrame for Seaborn
    df = pd.DataFrame(data_matrix, index=y_labels, columns=x_labels)
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Create heatmap with Seaborn
    sns.heatmap(
        df, 
        annot=True, 
        fmt='.2f',
        cmap='RdYlGn',  # Red-Yellow-Green colormap (good for sentiment)
        center=0,
        linewidths=0.5,
        linecolor='white',
        cbar_kws={'label': 'Value', 'shrink': 0.8},
        annot_kws={'size': 10, 'weight': 'bold'},
        ax=ax
    )
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=11)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=11)
    
    plt.tight_layout()
    
    return _save_and_encode_plot("heatmap")
