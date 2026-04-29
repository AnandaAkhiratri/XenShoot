# XenShoot 📸

Modern screenshot tool with annotation and cloud upload capabilities, inspired by Flameshot.

![XenShoot](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## Features ✨

### Desktop App (PyQt5)
- 🎨 **Rich Annotation Tools**
  - Pen, Arrow, Rectangle, Circle, Line
  - Text annotations (inline editing)
  - Blur tool
  - Color invert
  - Number markers
- 🎯 **Flameshot-style UI**
  - Selection with size indicator
  - Floating toolbar
  - Corner handles
  - Move selection
- 📋 **Actions**
  - Copy to clipboard
  - Pin to screen (draggable)
  - Save to file
  - Open with app (Paint, Photoshop, GIMP, etc.)
- ☁️ **Cloud Upload**
  - Auto upload to Backblaze B2
  - Direct shareable links
- ⌨️ **Global Hotkey**
  - Quick screenshot with keyboard shortcut
  - System tray integration

### Web Dashboard (Laravel)
- 📊 **Screenshot History**
  - View all screenshots by user
  - Display IP address, filename, URL, date
  - Thumbnail preview with zoom modal
- 🔗 **Quick Actions**
  - Copy URL to clipboard
  - Delete screenshots
  - Open full-size image
- 🔐 **User Authentication**
  - Multi-user support
  - User management

## Tech Stack 🛠️

**Desktop App:**
- Python 3.8+
- PyQt5 (UI framework)
- keyboard (global hotkeys)
- requests (API calls)
- Pillow (image processing)
- boto3 (Backblaze B2)

**Web Dashboard:**
- Laravel 10
- MySQL/PostgreSQL
- Blade templates

## Installation 📦

### Desktop App

1. Clone repository:
```bash
git clone https://github.com/yourusername/xenshoot.git
cd xenshoot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure Backblaze B2:
   - Create account at https://www.backblaze.com/b2/
   - Create bucket (public)
   - Copy credentials to config

4. Run application:
```bash
python main.py
```

### Web Dashboard (Laravel)

1. Navigate to Laravel folder:
```bash
cd /path/to/laravel/project
```

2. Install dependencies:
```bash
composer install
npm install && npm run build
```

3. Configure database in `.env`:
```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=xenshoot
DB_USERNAME=root
DB_PASSWORD=
```

4. Run migrations:
```bash
php artisan migrate
```

5. Start server:
```bash
php artisan serve
```

## Configuration ⚙️

### Backblaze B2 Setup

1. Create Backblaze B2 bucket (public)
2. Generate application key
3. Configure in XenShoot settings or `config.json`:

```json
{
  "upload_service": "backblaze",
  "backblaze_bucket_id": "your-bucket-id",
  "backblaze_endpoint": "s3.us-east-005.backblazeb2.com",
  "backblaze_access_key_id": "your-access-key",
  "backblaze_secret_access_key": "your-secret-key",
  "backblaze_bucket_name": "YourBucket"
}
```

### Laravel API Integration

Configure Laravel API URL in XenShoot:

```json
{
  "laravel_api_url": "http://127.0.0.1:8000",
  "laravel_user_id": 1
}
```

## Usage 🚀

1. **Take Screenshot:**
   - Press global hotkey (default: `Win+Shift+S`)
   - Or click tray icon → "Capture"

2. **Annotate:**
   - Select area
   - Use toolbar tools to annotate
   - Choose colors and thickness

3. **Save/Share:**
   - Click Save → auto upload to Backblaze
   - Click Copy → copy to clipboard
   - Click Pin → pin to screen
   - Click Open → open in external app

4. **View History:**
   - Open web dashboard
   - Login with credentials
   - View all screenshots
   - Copy URLs, delete, zoom images

## Keyboard Shortcuts ⌨️

- `Win+Shift+S` - Take screenshot
- `ESC` - Cancel/Close
- `Ctrl+S` - Save
- `Ctrl+C` - Copy to clipboard
- Arrow keys - Fine-tune selection

## Theme Colors 🎨

- Primary: Navy Blue `#000a52`
- Accent: Yellow Gold `#f5cb11`
- Dark mode optimized

## API Endpoints 📡

### Screenshot Upload
```
POST /api/screenshots/upload
Content-Type: application/json

{
  "user_id": 1,
  "filename": "screenshot_20260429_103045.png",
  "file_url": "https://backblaze.url/file.png",
  "file_size": 123456,
  "width": 1920,
  "height": 1080
}
```

### Screenshot List
```
GET /api/screenshots/list?user_id=1
```

## Building Executable 📦

To build standalone `.exe`:

```bash
pip install pyinstaller
pyinstaller main.spec
```

## Contributing 🤝

Contributions are welcome! Please:
1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

## License 📄

MIT License - see [LICENSE](LICENSE) file for details.

## Credits 👏

- Inspired by [Flameshot](https://flameshot.org/)
- Icons from [SVG Repo](https://www.svgrepo.com/)
- Built with ❤️ by [Your Name]

## Support 💬

For issues, questions, or feature requests:
- Open an issue on GitHub
- Email: your@email.com

---

⭐ **Star this repo if you find it useful!**
