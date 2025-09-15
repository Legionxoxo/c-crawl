# How I Scaled Common Crawl Data Extraction

## The Challenge I Faced

When I needed to analyze data from 10 million websites, I quickly discovered that the standard approach wasn't going to work.

### 📋 What is CDX?

CDX (Canonical URL and Timestamp with Digest) is Common Crawl's index format that tells you exactly where to find specific web pages in their massive WARC archives. Think of it as a catalog that says "page X is in file Y at position Z."

### 🐌 The CDX API Bottleneck

Common Crawl's CDX API has practical limitations for large-scale work:

**Rate Limits:**

-   **3 requests per second** maximum
-   **No concurrent requests** allowed
-   **One domain at a time** - no bulk queries

**My Scale Problem:**

```bash
# What I needed: 10 million domains
# CDX API: 10,000,000 domains ÷ 3 requests/second = 38+ days minimum
# Plus processing time, retries, network delays = months
# My solution: Process in 100K batches = 2-5 minutes per batch
```

### 💾 The Data Waste Problem

The traditional approach meant downloading massive amounts of unnecessary data:

```bash
# Standard approach: Download entire WARC files (1GB+ each)
# Extract only what you need (maybe 0.1% of the file)
# Result: 99.9% wasted bandwidth and storage

# My approach: Get precise file locations, offsets, and lengths
# Download only the specific records needed
# Result: 1000x reduction in data transfer
```

## My Solution: AWS Athena for Scale

I realized that Common Crawl also provides their indices in Parquet format on AWS, which meant I could use Athena to query them directly instead of going through the rate-limited API.

**What this enabled:**

-   **Parallel processing**: Query millions of domains in batches
-   **Smart filtering**: Built-in deduplication and content type filtering
-   **Cost efficiency**: Typical cost $0.50-$2.00 per 100K batch
-   **Speed**: Minutes instead of hours

### 🎯 Smart Filtering

I built in automatic filtering to avoid junk data:

```sql
-- Only get what matters:
WHERE cc.fetch_status = 200                    -- Successful responses only
  AND cc.content_mime_detected = 'text/html'   -- HTML content only
  AND cc.content_digest IS NOT NULL            -- Valid content only
```

Plus deduplication - since Common Crawl captures the same page multiple times, I keep only the latest version of each unique piece of content.

### 📍 The Result: Precise Data Locations

The output gives you everything needed for targeted downloading:

```json
{
    "url": "https://example.com/page",
    "filename": "CC-MAIN-20250130-120000-warc.gz",
    "offset": "12345",
    "length": "2048",
    "digest": "sha1:ABC123..."
}
```

## What I Achieved

**Scale accomplished:**

-   **10 million domains** processed in a single run
-   **Total runtime**: 7 minutes 50 seconds
-   **Output**: 60 files totaling 37.9 GB compressed
-   **Records extracted**: 383,162,078 total lines
-   **Per-domain distribution**:
    -   Median (p50): 17 pages per domain
    -   90th percentile: 207 pages per domain
    -   99th percentile: 991 pages per domain
    -   Maximum: 1,351,208 pages (single domain)
-   **Cost**: ~$2-5 total

**The workflow:**

1. Load domain lists (10M domains)
2. Single Athena query extracts all CDX records (7m 50s actual runtime)
3. Result: 383M+ CDX records across 60 output files (37.9 GB compressed)
4. Download only the specific content needed using offset+length
5. Process the targeted data without wasting bandwidth

```

```
