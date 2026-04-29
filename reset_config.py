"""
Reset config to BackBlaze B2 default
Run this if screenshots are still uploading to Cloudinary/other services
"""

import json
from pathlib import Path

# Config path
config_dir = Path.home() / ".xenshoot"
config_file = config_dir / "config.json"

# Default config with BackBlaze B2
default_config = {
    'upload_service': 'backblaze',
    
    # BackBlaze B2 Storage (Primary)
    'backblaze_bucket_id': '63bf91f04bf0f57e99cb061f',
    'backblaze_endpoint': 's3.us-east-005.backblazeb2.com',
    'backblaze_access_key_id': '0053f10b05e9b6f0000000001',
    'backblaze_secret_access_key': 'K005+CqN5dlkoFX7ibbcA0Jx2gXtm0E',
    'backblaze_bucket_name': 'XenShot',
    
    # Other services (optional)
    'imgbb_api_key': '',
    'imgbb_url_type': 'page',
    'imgur_client_id': '',
    'cloudinary_cloud_name': '',
    'cloudinary_upload_preset': 'xenshoot',
    'custom_endpoint': '',
    
    # Hotkeys
    'hotkey_area': 'ctrl+shift+a',
    'hotkey_fullscreen': 'ctrl+shift+f',
    
    # Local settings
    'save_local_copy': True,
    'local_save_path': str(Path.home() / "Pictures" / "XenShoot"),
    'auto_copy_url': True,
    'show_notification': True,
}

# Create config directory if not exists
if not config_dir.exists():
    config_dir.mkdir(parents=True)
    print(f"Created config directory: {config_dir}")

# Delete old config if exists
if config_file.exists():
    config_file.unlink()
    print(f"Deleted old config: {config_file}")

# Write new config
with open(config_file, 'w') as f:
    json.dump(default_config, f, indent=4)

print("[OK] Config reset successfully!")
print(f"[*] Config file: {config_file}")
print(f"[*] Upload service: {default_config['upload_service']}")
print(f"[*] BackBlaze B2 bucket: {default_config['backblaze_bucket_name']}")
print(f"[*] Access Key ID: {default_config['backblaze_access_key_id']}")
print()
print("[SUCCESS] Now restart XenShoot and try taking a screenshot!")
print("          Press Ctrl+Shift+A to test")
