# Cloud Deployment Guide

## YouTube Analytics Multi-Agent System - Production Deployment

This guide covers deploying the YouTube Analytics application to Google Cloud Platform (GCP), including AlloyDB/Cloud SQL setup, Cloud Run deployment, and production configurations.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Database Setup (AlloyDB/Cloud SQL)](#database-setup)
4. [Environment Configuration](#environment-configuration)
5. [Docker Containerization](#docker-containerization)
6. [Cloud Run Deployment](#cloud-run-deployment)
7. [Security Best Practices](#security-best-practices)
8. [Monitoring & Logging](#monitoring--logging)
9. [Cost Optimization](#cost-optimization)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Google Cloud Platform                              │
│                                                                             │
│  ┌─────────────┐     ┌─────────────────┐     ┌─────────────────────────┐   │
│  │   Cloud     │────▶│   Cloud Run     │────▶│   AlloyDB / Cloud SQL   │   │
│  │   Load      │     │   (Dashboard)   │     │   (PostgreSQL + pgvector)│   │
│  │   Balancer  │     │                 │     │                         │   │
│  └─────────────┘     └─────────────────┘     └─────────────────────────┘   │
│         │                    │                          │                   │
│         │                    ▼                          │                   │
│         │           ┌─────────────────┐                 │                   │
│         │           │  Gemini API     │                 │                   │
│         │           │  (AI Agents)    │                 │                   │
│         │           └─────────────────┘                 │                   │
│         │                    │                          │                   │
│         │                    ▼                          │                   │
│         │           ┌─────────────────┐                 │                   │
│         │           │  Embedding API  │                 │                   │
│         │           │  (Vector Search)│                 │                   │
│         │           └─────────────────┘                 │                   │
│         │                                               │                   │
│  ┌──────▼────────────────────────────────────────────────────────────────┐  │
│  │                        Secret Manager                                  │  │
│  │  (API Keys, DB Credentials, Service Account Keys)                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### 1. GCP Account Setup
```bash
# Install Google Cloud SDK
brew install google-cloud-sdk   # macOS
# or
curl https://sdk.cloud.google.com | bash  # Linux

# Login to GCP
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    alloydb.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com
```

### 2. Local Tools Required
- Docker Desktop
- Python 3.11+
- `gcloud` CLI
- `psql` (PostgreSQL client)

---

## Database Setup

### Option A: AlloyDB (Recommended for Production)

AlloyDB provides better performance with pgvector for vector similarity searches.

```bash
# Create AlloyDB cluster
gcloud alloydb clusters create youtube-analytics-cluster \
    --region=us-central1 \
    --password=YOUR_SECURE_PASSWORD \
    --network=default

# Create primary instance
gcloud alloydb instances create youtube-analytics-primary \
    --cluster=youtube-analytics-cluster \
    --region=us-central1 \
    --instance-type=PRIMARY \
    --cpu-count=2

# Get connection IP
gcloud alloydb instances describe youtube-analytics-primary \
    --cluster=youtube-analytics-cluster \
    --region=us-central1 \
    --format="value(ipAddress)"
```

### Option B: Cloud SQL (Simpler Setup)

```bash
# Create Cloud SQL instance with pgvector
gcloud sql instances create youtube-analytics-db \
    --database-version=POSTGRES_15 \
    --tier=db-custom-2-4096 \
    --region=us-central1 \
    --database-flags=cloudsql.enable_pgvector=on

# Set root password
gcloud sql users set-password postgres \
    --instance=youtube-analytics-db \
    --password=YOUR_SECURE_PASSWORD

# Create database
gcloud sql databases create youtube_analytics \
    --instance=youtube-analytics-db
```

### Database Schema Setup

Connect to your cloud database and run the schema:

```bash
# For Cloud SQL with Cloud SQL Auth Proxy
./cloud-sql-proxy YOUR_PROJECT:us-central1:youtube-analytics-db &

# Connect
psql -h 127.0.0.1 -U postgres -d youtube_analytics

# Run schema
\i database/schema.sql

# Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

# Create vector table for transcript chunks
CREATE TABLE transcript_chunks (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(50) NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for vector similarity search
CREATE INDEX ON transcript_chunks 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);
```

---

## Environment Configuration

### 1. Create Production `.env` File

Create `.env.production`:

```bash
# =============================================================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# =============================================================================

# Application Mode
APP_ENV=production
DEBUG_MODE=False

# =============================================================================
# Google Cloud Configuration
# =============================================================================
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Gemini API Key (from Google AI Studio)
GOOGLE_API_KEY=your_gemini_api_key

# YouTube API Key
YOUTUBE_API_KEY=your_youtube_api_key

# =============================================================================
# Database Configuration (Cloud SQL / AlloyDB)
# =============================================================================
# For Cloud SQL with Private IP:
DB_HOST=/cloudsql/YOUR_PROJECT:us-central1:youtube-analytics-db
DB_PORT=5432
DB_NAME=youtube_analytics
DB_USER=postgres
DB_PASSWORD=your_secure_password

# For AlloyDB:
# DB_HOST=ALLOYDB_PRIVATE_IP
# DB_PORT=5432
# DB_NAME=youtube_analytics
# DB_USER=postgres
# DB_PASSWORD=your_secure_password

# =============================================================================
# Dashboard Configuration
# =============================================================================
DASHBOARD_PORT=8080
DASHBOARD_HOST=0.0.0.0
```

### 2. Store Secrets in Secret Manager

```bash
# Create secrets
echo -n "your_gemini_api_key" | \
    gcloud secrets create google-api-key --data-file=-

echo -n "your_youtube_api_key" | \
    gcloud secrets create youtube-api-key --data-file=-

echo -n "your_db_password" | \
    gcloud secrets create db-password --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding google-api-key \
    --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

---

## Docker Containerization

### 1. Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
# YouTube Analytics Multi-Agent System
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional production dependencies
RUN pip install --no-cache-dir \
    gunicorn \
    psycopg2-binary \
    cloud-sql-python-connector[pg8000]

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Run the application
CMD ["python", "dashboard/app.py"]
```

### 2. Create `.dockerignore`

```
.venv/
__pycache__/
*.pyc
*.pyo
.git/
.gitignore
*.md
.env
.env.*
!.env.example
data_collector/data/
plots/
*.log
.DS_Store
vertex-ai-key.json
```

### 3. Build and Test Locally

```bash
# Build Docker image
docker build -t youtube-analytics:latest .

# Test locally
docker run -p 8080:8080 \
    -e GOOGLE_API_KEY=your_key \
    -e DB_HOST=host.docker.internal \
    -e DB_PORT=5432 \
    -e DB_NAME=youtube_analytics \
    -e DB_USER=postgres \
    -e DB_PASSWORD=your_password \
    youtube-analytics:latest
```

---

## Cloud Run Deployment

### 1. Push to Artifact Registry

```bash
# Create Artifact Registry repository
gcloud artifacts repositories create youtube-analytics \
    --repository-format=docker \
    --location=us-central1

# Configure Docker authentication
gcloud auth configure-docker us-central1-docker.pkg.dev

# Tag and push image
docker tag youtube-analytics:latest \
    us-central1-docker.pkg.dev/YOUR_PROJECT/youtube-analytics/app:latest

docker push us-central1-docker.pkg.dev/YOUR_PROJECT/youtube-analytics/app:latest
```

### 2. Deploy to Cloud Run

```bash
gcloud run deploy youtube-analytics \
    --image=us-central1-docker.pkg.dev/YOUR_PROJECT/youtube-analytics/app:latest \
    --platform=managed \
    --region=us-central1 \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=0 \
    --max-instances=10 \
    --timeout=300 \
    --concurrency=80 \
    --set-env-vars="APP_ENV=production" \
    --set-env-vars="DASHBOARD_PORT=8080" \
    --set-secrets="GOOGLE_API_KEY=google-api-key:latest" \
    --set-secrets="YOUTUBE_API_KEY=youtube-api-key:latest" \
    --set-secrets="DB_PASSWORD=db-password:latest" \
    --set-env-vars="DB_HOST=/cloudsql/YOUR_PROJECT:us-central1:youtube-analytics-db" \
    --set-env-vars="DB_PORT=5432" \
    --set-env-vars="DB_NAME=youtube_analytics" \
    --set-env-vars="DB_USER=postgres" \
    --add-cloudsql-instances=YOUR_PROJECT:us-central1:youtube-analytics-db
```

### 3. Update `dashboard/app.py` for Production

Make these changes to `dashboard/app.py`:

```python
# At the top of the file, add:
import os

# Change the app.run() at the bottom to:
if __name__ == "__main__":
    port = int(os.environ.get("DASHBOARD_PORT", 8080))
    host = os.environ.get("DASHBOARD_HOST", "0.0.0.0")
    debug = os.environ.get("DEBUG_MODE", "False").lower() == "true"
    
    print(f"\n{'='*60}")
    print("   🎬 YouTube Analytics Chatbot Dashboard")
    print(f"{'='*60}")
    print(f"\n✅ Starting server on {host}:{port}...")
    
    app.run(debug=debug, host=host, port=port)
```

### 4. Update `database/db_config.py` for Cloud SQL

Add Cloud SQL connector support:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Check if running in Cloud Run with Cloud SQL
if os.getenv('DB_HOST', '').startswith('/cloudsql'):
    # Use Cloud SQL Python Connector
    from google.cloud.sql.connector import Connector
    import pg8000
    
    connector = Connector()
    
    def getconn():
        conn = connector.connect(
            os.getenv('CLOUD_SQL_CONNECTION_NAME'),
            "pg8000",
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            db=os.getenv('DB_NAME'),
        )
        return conn
    
    from sqlalchemy import create_engine
    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
else:
    # Local PostgreSQL connection (existing code)
    DATABASE_URL = (
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    engine = create_engine(DATABASE_URL, ...)
```

---

## Security Best Practices

### 1. IAM Permissions

```bash
# Create service account for Cloud Run
gcloud iam service-accounts create youtube-analytics-sa \
    --display-name="YouTube Analytics Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT \
    --member="serviceAccount:youtube-analytics-sa@YOUR_PROJECT.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding YOUR_PROJECT \
    --member="serviceAccount:youtube-analytics-sa@YOUR_PROJECT.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 2. Network Security

```bash
# Create VPC for private connections
gcloud compute networks create youtube-analytics-vpc \
    --subnet-mode=auto

# Enable Private Google Access
gcloud compute networks subnets update default \
    --region=us-central1 \
    --enable-private-ip-google-access
```

### 3. HTTPS & Custom Domain (Optional)

```bash
# Map custom domain
gcloud run domain-mappings create \
    --service=youtube-analytics \
    --domain=analytics.yourdomain.com \
    --region=us-central1
```

---

## Monitoring & Logging

### 1. Enable Cloud Monitoring

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=youtube-analytics" \
    --limit=50
```

### 2. Create Alerts

```bash
# Create alert policy for errors
gcloud alpha monitoring policies create \
    --notification-channels=YOUR_CHANNEL_ID \
    --display-name="YouTube Analytics Error Rate" \
    --condition-display-name="Error rate > 1%" \
    --condition-filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count" AND metric.labels.response_code_class!="2xx"'
```

### 3. Add Application Logging

```python
# In your Python code
import google.cloud.logging

client = google.cloud.logging.Client()
client.setup_logging()

import logging
logger = logging.getLogger(__name__)

logger.info("Application started")
logger.error("Error occurred", exc_info=True)
```

---

## Cost Optimization

### Estimated Monthly Costs

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| Cloud Run | 2 vCPU, 2GB RAM, ~100K requests | $20-50 |
| Cloud SQL | db-custom-2-4096 | $80-100 |
| AlloyDB | 2 vCPU | $150-200 |
| Secret Manager | 3 secrets | <$1 |
| Gemini API | ~100K requests | $10-30 |
| **Total (Cloud SQL)** | | **~$120-180/month** |
| **Total (AlloyDB)** | | **~$190-280/month** |

### Cost Reduction Tips

1. **Use Cloud Run min-instances=0** for dev/staging
2. **Use Cloud SQL for smaller workloads** (AlloyDB for high-traffic)
3. **Enable auto-scaling** with appropriate limits
4. **Use committed use discounts** for production

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check Cloud SQL connectivity
gcloud sql connect youtube-analytics-db --user=postgres

# Verify Cloud Run has Cloud SQL connection
gcloud run services describe youtube-analytics --region=us-central1
```

#### 2. Secret Access Denied
```bash
# Check IAM bindings
gcloud secrets get-iam-policy google-api-key
```

#### 3. Model Not Found (Gemini API)
```python
# List available models
from google import genai
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
for model in client.models.list():
    print(model.name)
```

#### 4. Vector Search Slow
```sql
-- Check index usage
EXPLAIN ANALYZE 
SELECT * FROM transcript_chunks 
ORDER BY embedding <=> '[...]'::vector 
LIMIT 10;

-- Rebuild index if needed
REINDEX INDEX transcript_chunks_embedding_idx;
```

---

## Quick Deployment Checklist

- [ ] Create GCP project and enable APIs
- [ ] Set up Cloud SQL/AlloyDB with pgvector
- [ ] Run database schema migration
- [ ] Generate embeddings for existing transcripts
- [ ] Store secrets in Secret Manager
- [ ] Build and push Docker image
- [ ] Deploy to Cloud Run
- [ ] Test application endpoint
- [ ] Set up monitoring alerts
- [ ] Configure custom domain (optional)

---

## Support

For issues specific to this deployment:
1. Check Cloud Run logs: `gcloud logging read`
2. Verify database connectivity
3. Ensure all secrets are properly configured
4. Check Gemini API quotas

---

*Last Updated: November 2025*
