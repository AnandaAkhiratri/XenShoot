"""
BackBlaze B2 uploader using S3-compatible API
"""

import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import io

class BackBlazeUploader:
    def __init__(self, config):
        self.config = config
        self.bucket_id = config.get('backblaze_bucket_id', '')
        self.endpoint = config.get('backblaze_endpoint', '')
        self.access_key_id = config.get('backblaze_access_key_id', '')
        self.secret_access_key = config.get('backblaze_secret_access_key', '')
        self.bucket_name = config.get('backblaze_bucket_name', 'XenShot')
        
    def is_configured(self):
        """Check if BackBlaze is properly configured"""
        return bool(self.bucket_id and self.endpoint and self.access_key_id and self.secret_access_key)
    
    def upload(self, image_data, filename=None):
        """
        Upload image to BackBlaze B2
        
        Args:
            image_data: Binary image data
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Public URL of uploaded image or None if failed
        """
        if not self.is_configured():
            raise Exception("BackBlaze B2 not configured. Please set credentials in Settings.")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        try:
            # Initialize S3 client with BackBlaze B2 endpoint
            s3_client = boto3.client(
                's3',
                endpoint_url=f'https://{self.endpoint}',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name='us-east-005'
            )
            
            # Upload file
            object_key = f'images/{filename}'
            
            # BackBlaze B2 doesn't support ACL via S3 API
            # Bucket must be set to Public in BackBlaze console
            s3_client.upload_fileobj(
                io.BytesIO(image_data),
                self.bucket_name,
                object_key,
                ExtraArgs={
                    'ContentType': 'image/png'
                }
            )
            
            # Construct public URL using custom domain
            public_url = f"https://image.kshot.cloud/{object_key}"

            return public_url
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise Exception(f"BackBlaze B2 upload failed: {error_code} - {error_message}")
        except Exception as e:
            raise Exception(f"BackBlaze B2 upload failed: {str(e)}")
    
    def delete(self, filename):
        """Delete file from BackBlaze B2"""
        if not self.is_configured():
            raise Exception("BackBlaze B2 not configured")
        
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=f'https://{self.endpoint}',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name='us-east-005'
            )
            
            object_key = f'images/{filename}'
            s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to delete from BackBlaze B2: {str(e)}")
    
    def list_files(self, prefix='images/', max_keys=100):
        """List files in BackBlaze B2 bucket"""
        if not self.is_configured():
            raise Exception("BackBlaze B2 not configured")
        
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=f'https://{self.endpoint}',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name='us-east-005'
            )
            
            response = s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'url': f"https://image.kshot.cloud/{obj['Key']}"
                    })
            
            return files
            
        except Exception as e:
            raise Exception(f"Failed to list files from BackBlaze B2: {str(e)}")
