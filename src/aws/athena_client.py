import boto3
import time
import json
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AthenaClient:
    def __init__(self, region='us-east-1', workgroup='primary'):
        self.athena = boto3.client('athena', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.workgroup = workgroup
        
    def execute_query(self, query, output_location, wait_for_completion=True):
        """Execute Athena query and optionally wait for completion"""
        try:
            response = self.athena.start_query_execution(
                QueryString=query,
                ResultConfiguration={'OutputLocation': output_location},
                WorkGroup=self.workgroup
            )
            
            execution_id = response['QueryExecutionId']
            print(f"🚀 Started query execution: {execution_id}")
            
            if wait_for_completion:
                return self.wait_for_query_completion(execution_id)
            else:
                return execution_id
                
        except ClientError as e:
            print(f"❌ Error executing query: {e}")
            raise
    
    def wait_for_query_completion(self, execution_id, max_wait_minutes=45):
        """Wait for query to complete with timeout"""
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            response = self.athena.get_query_execution(QueryExecutionId=execution_id)
            status = response['QueryExecution']['Status']['State']
            
            if status == 'SUCCEEDED':
                execution_time = time.time() - start_time
                data_scanned = response['QueryExecution']['Statistics'].get('DataScannedInBytes', 0)
                cost_estimate = (data_scanned / (1024**4)) * 5  # $5 per TB
                
                print(f"✅ Query completed successfully")
                print(f"⏱️  Execution time: {execution_time:.1f} seconds")
                print(f"📊 Data scanned: {data_scanned / (1024**3):.2f} GB")
                print(f"💰 Estimated cost: ${cost_estimate:.2f}")
                
                return response
                
            elif status in ['FAILED', 'CANCELLED']:
                error_reason = response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                print(f"❌ Query failed: {error_reason}")
                raise Exception(f"Query failed: {error_reason}")
                
            else:
                elapsed = time.time() - start_time
                print(f"⏳ Query running... ({elapsed:.0f}s elapsed, status: {status})")
                time.sleep(30)
        
        print(f"⏰ Query timed out after {max_wait_minutes} minutes")
        raise Exception(f"Query timed out after {max_wait_minutes} minutes")
    
    def get_query_results(self, execution_id, max_results=100):
        """Get query results"""
        try:
            response = self.athena.get_query_results(
                QueryExecutionId=execution_id,
                MaxResults=max_results
            )
            
            columns = [col['Name'] for col in response['ResultSet']['ResultSetMetadata']['ColumnInfo']]
            rows = []
            
            for row in response['ResultSet']['Rows'][1:]:  # Skip header
                row_data = [col.get('VarCharValue', '') for col in row['Data']]
                rows.append(dict(zip(columns, row_data)))
            
            return {'columns': columns, 'rows': rows}
            
        except ClientError as e:
            print(f"❌ Error getting query results: {e}")
            raise
    
