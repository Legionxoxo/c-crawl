#!/usr/bin/env python3
"""
Create S3 bucket using configuration
"""

import sys
import os
import json
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from src.aws.setup import CommonCrawlAWSSetup

def main():
    print("🪣 Create S3 Bucket")
    print("=" * 25)
    
    # Load configuration
    config_path = 'src/config/aws_config.json'
    if not os.path.exists(config_path):
        print("❌ Configuration file not found")
        return 1
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    bucket_name = config['bucket_name']
    region = config['region']
    
    print(f"📦 Creating bucket: {bucket_name}")
    print(f"🌍 Region: {region}")
    
    try:
        setup = CommonCrawlAWSSetup(bucket_name, region)
        
        # Step 1: Check credentials
        print("\n1️⃣ Checking AWS credentials...")
        setup.get_aws_credentials_info()
        
        # Step 2: Create bucket and folders
        print("\n2️⃣ Creating S3 bucket and folders...")
        setup.create_s3_bucket()
        
        # Step 3: Verify permissions
        print("\n3️⃣ Verifying permissions...")
        setup.verify_permissions()
        
        # Step 4: Set up billing alert
        print("\n4️⃣ Setting up billing alert...")
        setup.setup_billing_alert(threshold_usd=5.0)
        
        print(f"\n✅ S3 bucket '{bucket_name}' created successfully!")
        print("\nBucket structure:")
        print(f"  📁 s3://{bucket_name}/domains/")
        print(f"  📁 s3://{bucket_name}/results/")
        print(f"  📁 s3://{bucket_name}/athena-results/")
        
        print("\nNext step: python scripts/upload_data.py")
        
    except Exception as e:
        print(f"❌ Bucket creation failed: {e}")
        print("\nCommon issues:")
        print("- Bucket name already exists globally")
        print("- AWS credentials not configured")
        print("- Insufficient permissions")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())