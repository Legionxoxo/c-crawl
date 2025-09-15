#!/usr/bin/env python3
"""
Check S3 export results size and details
"""

import boto3
import json
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

def format_bytes(bytes_val):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

def main():
    print("📊 Checking S3 Export Results")
    print("=" * 50)
    
    # Load config
    with open('src/config/aws_config.json', 'r') as f:
        config = json.load(f)

    # Use config values instead of hardcoded
    bucket_name = config['bucket_name']
    crawl_id = config.get('last_cdx_export', {}).get('crawl_id', 'CC-MAIN-2025-30')
    export_location = config.get('last_cdx_export', {}).get('output_location', f"s3://{bucket_name}/results/{crawl_id}-cdx-json/")

    # Extract prefix from S3 URL
    if export_location.startswith("s3://"):
        # Remove s3://bucket_name/ to get the prefix
        prefix = export_location.replace(f"s3://{bucket_name}/", "")
    else:
        prefix = f"results/{crawl_id}-cdx-json/"

    s3_path = export_location
    
    print(f"🔍 Checking: {s3_path}\n")
    
    s3 = boto3.client('s3', region_name=config['region'])
    
    try:
        # List all objects with the prefix
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
        
        total_size = 0
        total_files = 0
        files = []
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    total_size += obj['Size']
                    total_files += 1
                    files.append({
                        'name': obj['Key'].split('/')[-1],
                        'size': obj['Size'],
                        'modified': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        if total_files == 0:
            print("📭 No results found at this location")
            return
        
        print(f"📊 Summary:")
        print(f"   Total files: {total_files}")
        print(f"   Total size: {format_bytes(total_size)} ({total_size:,} bytes)")
        print(f"   Average file size: {format_bytes(total_size/total_files if total_files > 0 else 0)}\n")
        
        print(f"📁 Files:")
        for file_info in sorted(files, key=lambda x: x['name']):
            print(f"   {file_info['name']}")
            print(f"     Size: {format_bytes(file_info['size'])} ({file_info['size']:,} bytes)")
            print(f"     Modified: {file_info['modified']}")
        
        # Estimate records count (if gzipped JSON)
        if files and files[0]['name'].endswith('.gz'):
            print(f"\n📈 Estimated content:")
            print(f"   Compressed data (.gz files)")
            print(f"   Likely contains millions of CDX JSON records")
            print(f"   Each record is one crawled URL from your domains")
        
        print(f"\n💾 To download and inspect:")
        print(f"   aws s3 cp {s3_path} ./results/ --recursive")
        print(f"   zcat ./results/*.gz | head -n 10")
        
    except ClientError as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()