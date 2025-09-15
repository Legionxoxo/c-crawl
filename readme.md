# Common Crawl

Extract URLs and metadata from Common Crawl index for specified domains using AWS Athena. 

## 🌟 Features

-   **Domain-Specific Extraction**: Extract crawl data for your specific list of domains
-   **CDX Format Output**: Generates newline-delimited JSON files compatible with CDX format
-   **Intelligent Deduplication**: Latest capture per content digest to avoid duplicates
-   **Advanced Filtering**: HTTP 200 responses, HTML content only
-   **AWS Integration**: Leverages AWS Athena for scalable querying
-   **Cost Optimization**: Efficient queries to minimize Athena scan costs
-   **Automated Setup**: One-command AWS infrastructure deployment

## 📁 Project Structure

```
common-crawl/
├── src/
│   ├── aws/
│   │   ├── athena_client.py    # Athena query execution
│   │   └── setup.py            # AWS infrastructure setup
│   └── config/
│       └── aws_config.json     # Configuration file
├── scripts/
│   ├── create_bucket.py        # AWS bucket setup
│   ├── upload_data.py          # Domain list upload
│   ├── run_cc_query.py         # Main CDX extraction
│   └── check_s3_results.py     # Results verification
├── data/
│   └── sample.csv              # Domain list template
└── .env.example                # Environment variables template
```

## 🚀 Quick Start

### Prerequisites

-   Python 3.8 or higher
-   AWS Account with appropriate permissions
-   AWS CLI configured or environment variables set

### Installation

1. **Clone the repository**

    ```bash
    git clone <repository-url>
    cd common-crawl
    ```

2. **Install dependencies**

    ```bash
    pip install boto3 python-dotenv
    ```

3. **Set up environment variables**

    ```bash
    cp .env.example .env
    # Edit .env with your AWS credentials
    ```

4. **Configure your domains**
    ```bash
    # Edit data/sample.csv with your target domains
    # Format: single column with header 'domain'
    ```

### Setup

1. **Create AWS infrastructure**

    ```bash
    python scripts/create_bucket.py
    ```

2. **Upload your domain list**

    ```bash
    python scripts/upload_data.py
    ```

3. **Extract CDX data**

    ```bash
    python scripts/run_cc_query.py
    ```

4. **Check results**
    ```bash
    python scripts/check_s3_results.py
    ```

## 📊 Configuration

### AWS Configuration (`src/config/aws_config.json`)

```json
{
    "bucket_name": "your-bucket-name",
    "region": "us-east-1",
    "results_location": "s3://your-bucket-name/results/",
    "athena_results_location": "s3://your-bucket-name/athena-results/",
    "domains_location": "s3://your-bucket-name/domains/"
}
```

### Environment Variables (`.env`)

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### Domain List Format (`data/sample.csv`)

```csv
domain
example.com
mysite.org
another-domain.net
```

## 💻 Usage Examples

### Basic CDX Extraction

```bash
# Full workflow
python scripts/create_bucket.py      # Setup AWS infrastructure
python scripts/upload_data.py        # Upload domain list
python scripts/run_cc_query.py       # Extract CDX records
python scripts/check_s3_results.py   # Verify results
```

### Download and Inspect Results

```bash
# Sync results locally
aws s3 sync s3://your-bucket/results/CC-MAIN-2025-30-cdx-json/ ./cdx-results/

# Preview CDX records
zcat ./cdx-results/*.gz | head -n 5

# Count total records
zcat ./cdx-results/*.gz | wc -l
```

### Sample CDX Output

```json
{"urlkey":"com,example)/page1","timestamp":"20250130123456","url":"https://example.com/page1","mime":"text/html","mime-detected":"text/html","status":"200","digest":"sha1:ABC123...","length":"2048","offset":"12345","filename":"CC-MAIN-20250130-120000-warc.gz","languages":"en","encoding":"utf-8"}
{"urlkey":"org,mysite)/about","timestamp":"20250130134567","url":"https://mysite.org/about","mime":"text/html","mime-detected":"text/html","status":"200","digest":"sha1:DEF456...","length":"1536","offset":"67890","filename":"CC-MAIN-20250130-130000-warc.gz","languages":"en","encoding":"utf-8"}
```

## 📋 Scripts Reference

### `scripts/create_bucket.py`

-   **Purpose**: Sets up AWS S3 bucket and folder structure
-   **Actions**: Creates bucket, folders, billing alerts, validates permissions
-   **Output**: Configured AWS infrastructure

### `scripts/upload_data.py`

-   **Purpose**: Uploads domain list to S3
-   **Input**: `data/sample.csv`
-   **Output**: Domains available in S3 for Athena queries

### `scripts/run_cc_query.py`

-   **Purpose**: Main CDX extraction using Athena
-   **Process**: Creates tables, adds partitions, exports CDX JSON
-   **Output**: Gzipped JSONL files with CDX records

### `scripts/check_s3_results.py`

-   **Purpose**: Validates and reports on extraction results
-   **Output**: File counts, sizes, download instructions

## 🔧 Advanced Configuration

### Custom Crawl Selection

Edit `scripts/run_cc_query.py`:

```python
crawl_id = "CC-MAIN-2024-51"  # Change to desired crawl
subset = "warc"               # Keep as 'warc' for web pages
```

### Filter Modifications

The extraction query supports various filters:

```sql
-- Current filters in run_cc_query.py
WHERE cc.fetch_status = 200                    -- Successful responses only
  AND cc.content_mime_detected = 'text/html'   -- HTML content only
  AND cc.content_digest IS NOT NULL            -- Valid content
```

### Cost Optimization

-   **Partition Filtering**: Script only loads specific crawl partitions
-   **Domain Joining**: Efficient join with your domain list
-   **Deduplication**: Latest capture per content digest reduces output size

## 💰 Cost Estimation

### Typical Athena Costs

-   **Small domain list** (< 100 domains): $0.05 - $0.30 per query
-   **Medium domain list** (100-1000 domains): $0.30 - $1.50 per query
-   **Large domain list** (> 1000 domains): $1.50 - $5.00 per query

### CloudWatch Billing Alert

The setup automatically creates a billing alert at $10 to monitor costs.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgments

-   [Common Crawl](https://commoncrawl.org/) for providing web crawl data

---

