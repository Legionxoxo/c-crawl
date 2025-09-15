import boto3
import json
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CommonCrawlAWSSetup:
    def __init__(self, bucket_name, region='us-east-1'):
        self.bucket_name = bucket_name
        self.region = region
        self.s3 = boto3.client('s3', region_name=region)
        self.athena = boto3.client('athena', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
    def create_s3_bucket(self):
        """Create S3 bucket with required folders"""
        try:
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            print(f"✅ Created S3 bucket: {self.bucket_name}")
            
            # Create folder structure
            folders = ['domains/', 'results/', 'athena-results/']
            for folder in folders:
                self.s3.put_object(Bucket=self.bucket_name, Key=folder)
                print(f"✅ Created folder: {folder}")
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                print(f"✅ S3 bucket {self.bucket_name} already exists")
            else:
                print(f"❌ Error creating bucket: {e}")
                raise
    
    def setup_billing_alert(self, threshold_usd=5.0):
        """Set up CloudWatch billing alarm"""
        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName=f'CommomCrawl-Billing-Alert-{self.bucket_name}',
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='EstimatedCharges',
                Namespace='AWS/Billing',
                Period=86400,
                Statistic='Maximum',
                Threshold=threshold_usd,
                ActionsEnabled=True,
                AlarmDescription=f'Alert when AWS charges exceed ${threshold_usd}',
                Dimensions=[
                    {
                        'Name': 'Currency',
                        'Value': 'USD'
                    }
                ],
                Unit='None'
            )
            print(f"✅ Created billing alert for ${threshold_usd}")
        except ClientError as e:
            print(f"⚠️  Could not create billing alert: {e}")
    
    def verify_permissions(self):
        """Verify required AWS permissions"""
        print("🔍 Checking AWS permissions...")
        
        # Test S3 permissions
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            self.s3.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
            print("✅ S3 permissions verified")
        except ClientError as e:
            print(f"❌ S3 permission error: {e}")
            
        # Test Athena permissions
        try:
            self.athena.list_work_groups()
            print("✅ Athena permissions verified")
        except ClientError as e:
            print(f"❌ Athena permission error: {e}")
    
    def get_aws_credentials_info(self):
        """Display current AWS configuration"""
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            print(f"🔑 AWS Account: {identity['Account']}")
            print(f"🔑 AWS User/Role: {identity['Arn']}")
            print(f"🌍 Region: {self.region}")
        except ClientError as e:
            print(f"❌ Could not get AWS identity: {e}")
    
    def save_config(self):
        """Save configuration for other scripts"""
        config = {
            'bucket_name': self.bucket_name,
            'region': self.region,
            'domains_location': f's3://{self.bucket_name}/domains/',
            'results_location': f's3://{self.bucket_name}/results/',
            'athena_results_location': f's3://{self.bucket_name}/athena-results/'
        }
        
        with open('src/config/aws_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"💾 Configuration saved to src/config/aws_config.json")
        return config