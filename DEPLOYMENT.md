# XenShoot Deployment Guide 🚀

Complete guide for deploying XenShoot (Desktop App + Laravel Web Dashboard).

---

## Production Setup

### 1. Laravel Web Dashboard (xenshot.cloud)

#### Requirements:
- PHP 8.1+
- MySQL/PostgreSQL
- Composer
- Web server (Nginx/Apache)

#### Deployment Steps:

1. **Upload Laravel files to server:**
```bash
cd /path/to/production
git clone [your-laravel-repo]
cd xenshoot-laravel
```

2. **Install dependencies:**
```bash
composer install --optimize-autoloader --no-dev
npm install && npm run build
```

3. **Configure environment:**
```bash
cp .env.example .env
php artisan key:generate
```

Edit `.env`:
```env
APP_NAME=XenShoot
APP_ENV=production
APP_DEBUG=false
APP_URL=https://xenshot.cloud

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=xenshot_db
DB_USERNAME=your_db_user
DB_PASSWORD=your_db_password
```

4. **Run migrations:**
```bash
php artisan migrate --force
```

5. **Set permissions:**
```bash
chmod -R 755 storage bootstrap/cache
chown -R www-data:www-data storage bootstrap/cache
```

6. **Configure web server (Nginx):**
```nginx
server {
    listen 80;
    server_name xenshot.cloud;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name xenshot.cloud;
    root /path/to/xenshoot-laravel/public;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;

    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";

    index index.php;

    charset utf-8;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location = /favicon.ico { access_log off; log_not_found off; }
    location = /robots.txt  { access_log off; log_not_found off; }

    error_page 404 /index.php;

    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
        include fastcgi_params;
    }

    location ~ /\.(?!well-known).* {
        deny all;
    }
}
```

7. **Restart services:**
```bash
sudo systemctl restart nginx
sudo systemctl restart php8.1-fpm
```

8. **Setup SSL (Let's Encrypt):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d xenshot.cloud
```

---

### 2. Desktop App Configuration

#### Update API URL:
Users need to ensure XenShoot points to production:

**Option A: Auto-configured (already done)**
- Default `laravel_api_url` in `config_manager.py` is set to `https://xenshot.cloud`
- New users automatically use production

**Option B: Manual config (for existing users)**
Users can edit `~/.xenshoot/config.json`:
```json
{
  "laravel_api_url": "https://xenshot.cloud",
  "laravel_user_id": 1
}
```

Or use Settings dialog in app (if implemented).

---

## User Management

### Create First User:
```bash
php artisan tinker
```

```php
$user = new App\Models\User();
$user->name = 'Admin';
$user->email = 'admin@xenshot.cloud';
$user->password = Hash::make('your-password');
$user->save();
```

### Get User ID for XenShoot:
```bash
php artisan tinker
```

```php
App\Models\User::where('email', 'user@example.com')->first()->id;
```

Then update XenShoot config with this user_id.

---

## Testing API Connection

### Test from command line:
```bash
curl -X POST https://xenshot.cloud/api/screenshots/upload \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "filename": "test_screenshot.png",
    "file_url": "https://example.com/test.png",
    "file_size": 123456,
    "width": 1920,
    "height": 1080
  }'
```

Expected response:
```json
{
  "success": true,
  "message": "Screenshot saved successfully",
  "data": {
    "user_id": 1,
    "ip_address": "123.45.67.89",
    "filename": "test_screenshot.png",
    "file_url": "https://example.com/test.png",
    "file_size": 123456,
    "width": 1920,
    "height": 1080,
    "uploaded_at": "2026-04-29T10:30:45.000000Z",
    "updated_at": "2026-04-29T10:30:45.000000Z",
    "created_at": "2026-04-29T10:30:45.000000Z",
    "id": 1
  }
}
```

---

## Monitoring & Logs

### Laravel logs:
```bash
tail -f storage/logs/laravel.log
```

### Nginx logs:
```bash
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

### Database queries:
Enable in `.env`:
```env
DB_LOG=true
```

---

## Security Checklist

- [ ] SSL certificate installed (HTTPS)
- [ ] CORS properly configured
- [ ] `.env` file secured (chmod 600)
- [ ] Database credentials strong
- [ ] Backblaze credentials not exposed in code
- [ ] API rate limiting enabled
- [ ] User authentication required for dashboard
- [ ] Regular backups scheduled
- [ ] Firewall configured (UFW/iptables)

---

## Troubleshooting

### "Connection refused" error:
- Check if Laravel is running: `php artisan serve` (dev) or check Nginx/Apache (prod)
- Check firewall: `sudo ufw status`
- Check API URL in XenShoot config

### "422 Unprocessable Entity":
- Check `user_id` exists in database
- Verify all required fields sent
- Check Laravel logs for validation errors

### "CORS error":
- Verify `config/cors.php` has `'allowed_origins' => ['*']`
- Clear config cache: `php artisan config:clear`

### Screenshots not appearing:
- Check database: `SELECT * FROM screenshots;`
- Verify `user_id` matches logged-in user
- Check XenShoot terminal output for API errors

---

## Backup & Restore

### Backup database:
```bash
mysqldump -u user -p xenshot_db > backup_$(date +%F).sql
```

### Restore database:
```bash
mysql -u user -p xenshot_db < backup_2026-04-29.sql
```

### Backup Laravel files:
```bash
tar -czf laravel_backup_$(date +%F).tar.gz /path/to/xenshoot-laravel
```

---

## Updating

### Update Laravel:
```bash
cd /path/to/xenshoot-laravel
git pull origin main
composer install --optimize-autoloader --no-dev
php artisan migrate --force
php artisan config:clear
php artisan cache:clear
php artisan view:clear
```

### Update Desktop App:
Users download new version from GitHub releases.

---

## Support

For issues:
- Check logs (Laravel + Nginx)
- Review GitHub Issues
- Contact: support@xenshot.cloud

---

**Production URL:** https://xenshot.cloud
**GitHub Repo:** https://github.com/AnandaAkhiratri/XenShoot
