#!/usr/bin/env python3
"""
Upload domain CSV data to S3
"""

import sys
import os
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def upload_domain_csv():
    # Load configuration
    config_path = 'src/config/aws_config.json'
    if not os.path.exists(config_path):
        print("❌ Configuration file not found. Run setup first.")
        return 1
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    bucket_name = config['bucket_name']
    region = config['region']
    
    # Find CSV file
    csv_file = 'data/sample.csv'
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return 1
    
    s3 = boto3.client('s3', region_name=region)
    
    try:
        # Upload CSV file
        s3_key = 'domains/sample.csv'
        
        print(f"📤 Uploading {csv_file} to s3://{bucket_name}/{s3_key}")
        
        s3.upload_file(
            csv_file,
            bucket_name,
            s3_key
        )
        
        print(f"✅ Upload complete!")
        print(f"File location: s3://{bucket_name}/{s3_key}")
        
        # Update config with uploaded file info
        config['uploaded_csv'] = {
            'local_path': csv_file,
            's3_bucket': bucket_name,
            's3_key': s3_key,
            's3_url': f's3://{bucket_name}/{s3_key}'
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("💾 Configuration updated")
        
    except ClientError as e:
        print(f"❌ Upload failed: {e}")
        return 1
    
    return 0

def main():
    print("📤 Upload Domain CSV to S3")
    print("=" * 30)
    
    return upload_domain_csv()

if __name__ == "__main__":
    sys.exit(main())