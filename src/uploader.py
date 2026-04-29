"""
Image uploader - supports multiple image hosting services
"""

import requests
import base64
from PyQt5.QtWidgets import QMessageBox
from datetime import datetime
import io
from PIL import Image

class ImageUploader:
    def __init__(self, config):
        self.config = config
        self.upload_service = config.get('upload_service', 'imgbb')
        
    def upload(self, image_data):
        """Upload image and return URL"""
        try:
            if self.upload_service == 'backblaze':
                url = self.upload_backblaze(image_data)
            elif self.upload_service == 'imgbb':
                url = self.upload_imgbb(image_data)
            elif self.upload_service == 'imgur':
                url = self.upload_imgur(image_data)
            elif self.upload_service == 'cloudinary':
                url = self.upload_cloudinary(image_data)
            elif self.upload_service == 'custom':
                url = self.upload_custom(image_data)
            else:
                url = self.upload_backblaze(image_data)
            
            return url
            
        except Exception as e:
            QMessageBox.critical(None, "Upload Error", f"Failed to upload: {str(e)}")
            return None
    
    def upload_backblaze(self, image_data):
        """Upload to BackBlaze B2 Storage"""
        from .backblaze_uploader import BackBlazeUploader
        
        bb = BackBlazeUploader(self.config)
        
        if not bb.is_configured():
            QMessageBox.warning(
                None,
                "BackBlaze B2 Not Configured",
                "Please configure BackBlaze B2 credentials in Settings.\n\n"
                "Required:\n"
                "• Bucket ID\n"
                "• Endpoint\n"
                "• Access Key ID\n"
                "• Secret Access Key"
            )
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        
        # Upload to Backblaze
        url = bb.upload(image_data, filename)
        
        # If upload successful, send metadata to Laravel API
        if url:
            self.send_to_laravel_api(url, filename, image_data)
        
        return url
    
    def send_to_laravel_api(self, file_url, filename, image_data):
        """Send screenshot metadata to Laravel API"""
        try:
            # Get Laravel API URL from config (default to localhost)
            laravel_api_url = self.config.get('laravel_api_url', 'http://127.0.0.1:8000')
            
            # Get user_id from config (default to 1 for testing)
            user_id = self.config.get('laravel_user_id', 1)
            
            # Get image dimensions
            try:
                from PIL import Image as PILImage
                img = PILImage.open(io.BytesIO(image_data))
                width, height = img.size
                file_size = len(image_data)
            except:
                width = None
                height = None
                file_size = len(image_data)
            
            # Prepare data
            data = {
                'user_id': user_id,
                'filename': filename,
                'file_url': file_url,
                'file_size': file_size,
                'width': width,
                'height': height,
            }
            
            # Send to Laravel API
            response = requests.post(
                f"{laravel_api_url}/api/screenshots/upload",
                json=data,
                timeout=10
            )
            
            if response.status_code == 201:
                print(f"[LARAVEL API] Screenshot metadata saved successfully")
            else:
                print(f"[LARAVEL API] Failed to save metadata: {response.status_code}")
                print(f"[LARAVEL API] Response: {response.text}")
                
        except Exception as e:
            print(f"[LARAVEL API] Error sending to API: {e}")
            # Don't show error to user, just log it
            
    def upload_imgbb(self, image_data):
        """Upload to ImgBB"""
        api_key = self.config.get('imgbb_api_key', '')
        
        if not api_key:
            QMessageBox.warning(
                None, 
                "API Key Required", 
                "Please set your ImgBB API key in Settings.\nGet free API key at: https://api.imgbb.com/"
            )
            return None
            
        url = "https://api.imgbb.com/1/upload"
        
        payload = {
            "key": api_key,
            "image": base64.b64encode(image_data).decode('utf-8'),
        }
        
        response = requests.post(url, data=payload)
        result = response.json()
        
        if result.get('success'):
            data = result['data']
            
            # ImgBB returns multiple URLs, let user choose preference
            url_type = self.config.get('imgbb_url_type', 'page')
            
            if url_type == 'direct':
                # Direct image URL (i.ibb.co/xxxxx/image.png) - WARNING: May have SSL issues
                return data.get('display_url', data.get('image', {}).get('url', data.get('url')))
            elif url_type == 'page':
                # ImgBB viewer page (ibb.co/xxxxx) - Most reliable, always accessible
                return data.get('url_viewer', data.get('url'))
            else:
                # Default: use url_viewer (page link) for reliability
                return data.get('url_viewer', data.get('url'))
        else:
            error_msg = result.get('error', {}).get('message', 'Unknown error')
            raise Exception(f"ImgBB upload failed: {error_msg}")
            
    def upload_imgur(self, image_data):
        """Upload to Imgur"""
        client_id = self.config.get('imgur_client_id', '')
        
        if not client_id:
            QMessageBox.warning(
                None, 
                "Client ID Required", 
                "Please set your Imgur Client ID in Settings.\nRegister at: https://api.imgur.com/oauth2/addclient"
            )
            return None
            
        url = "https://api.imgur.com/3/image"
        
        headers = {
            "Authorization": f"Client-ID {client_id}"
        }
        
        response = requests.post(url, headers=headers, data={"image": base64.b64encode(image_data)})
        result = response.json()
        
        if result.get('success'):
            return result['data']['link']
        else:
            raise Exception(result.get('data', {}).get('error', 'Unknown error'))
            
    def upload_cloudinary(self, image_data):
        """Upload to Cloudinary using UNSIGNED upload (simpler, no signature needed)"""
        cloud_name = self.config.get('cloudinary_cloud_name', '')
        
        if not cloud_name:
            QMessageBox.warning(
                None, 
                "Cloudinary Cloud Name Required", 
                "Please set your Cloudinary cloud name in Settings.\n\n"
                "Get it at: https://cloudinary.com/console"
            )
            return None
        
        # Use UNSIGNED upload - no signature/authentication needed!
        # This requires an unsigned upload preset in Cloudinary dashboard
        upload_preset = self.config.get('cloudinary_upload_preset', 'xenshoot')
        
        # Upload URL for unsigned uploads
        url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
        
        # Prepare files
        files = {
            'file': ('screenshot.png', image_data, 'image/png')
        }
        
        # Data for unsigned upload - much simpler!
        data = {
            'upload_preset': upload_preset,
            'folder': 'xenshoot'
        }
        
        # Upload
        response = requests.post(url, files=files, data=data)
        result = response.json()
        
        if response.status_code == 200 and 'secure_url' in result:
            # Return secure HTTPS URL
            return result['secure_url']
        else:
            error_msg = result.get('error', {}).get('message', 'Unknown error')
            
            # Check if it's unsigned preset issue
            if 'unsigned' in error_msg.lower() or 'preset' in error_msg.lower():
                QMessageBox.warning(
                    None,
                    "Cloudinary Unsigned Preset Required",
                    f"Cloudinary upload failed: {error_msg}\n\n"
                    "You need to create an UNSIGNED upload preset:\n\n"
                    "1. Go to: https://cloudinary.com/console/settings/upload\n"
                    "2. Scroll to 'Upload presets'\n"
                    "3. Click 'Add upload preset'\n"
                    "4. Signing Mode: 'Unsigned'\n"
                    "5. Preset name: 'xenshoot'\n"
                    "6. Folder: 'xenshoot'\n"
                    "7. Save\n\n"
                    "Then try again!"
                )
                return None
            
            raise Exception(f"Cloudinary upload failed: {error_msg}")
            
    def upload_custom(self, image_data):
        """Upload to custom endpoint"""
        endpoint = self.config.get('custom_endpoint', '')
        
        if not endpoint:
            QMessageBox.warning(
                None, 
                "Custom Endpoint Required", 
                "Please set your custom upload endpoint in Settings."
            )
            return None
            
        # Custom upload logic - adjust based on your API
        files = {'image': ('screenshot.png', image_data, 'image/png')}
        response = requests.post(endpoint, files=files)
        
        # Assuming the response contains a URL field
        result = response.json()
        return result.get('url', result.get('link', ''))
