# StockFlow AI — Custom Domain, SSL & Live Connection Guide

This document outlines the step-by-step procedure for pointing a custom production domain (e.g. `stockflow.example.com` or `wms.yourcompany.com`) to your **StockFlow AI** installation with automatic HTTPS/SSL certificate generation.

---

## 🌐 1. Domain Architecture & Mapping

```
Custom Domain: https://stockflow.example.com
      │
      ├───> Main Web Application (WMS Dashboard)
      ├───> REST API Endpoints (/api/ & /sales/api/ etc.)
      └───> Health Check (/health/)
```

---

## 📡 2. DNS Record Setup Table

Log into your DNS Registrar (Cloudflare, GoDaddy, Namecheap, AWS Route 53, etc.) and add the following DNS records pointing to your server's Public IPv4 Address:

| Type  | Name / Host | Target / Value            | TTL  | Purpose                             |
|-------|-------------|---------------------------|------|-------------------------------------|
| **A** | `@`         | `YOUR_SERVER_PUBLIC_IP`   | Auto | Connects apex domain to server      |
| **A** | `stockflow` | `YOUR_SERVER_PUBLIC_IP`   | Auto | Connects subdomain (stockflow)      |
| **CNAME** | `www`   | `stockflow.example.com.`  | Auto | Redirects WWW traffic to canonical  |

> [!NOTE]
> Replace `YOUR_SERVER_PUBLIC_IP` with your cloud server's actual Elastic IP / Public IPv4 address.

---

## 🔒 3. Django Domain & Security Settings (`.env`)

In your production environment file `.env`, update the domain settings:

```bash
ALLOWED_HOSTS=stockflow.example.com,www.stockflow.example.com,YOUR_SERVER_PUBLIC_IP
CSRF_TRUSTED_ORIGINS=https://stockflow.example.com,https://www.stockflow.example.com
CORS_ALLOWED_ORIGINS=https://stockflow.example.com,https://www.stockflow.example.com

# Enable HTTPS Redirects & Secure Cookies once SSL is installed
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## 🛡️ 4. Free SSL Certificate Installation (Certbot & Let's Encrypt)

Run the following commands on your Ubuntu/Debian production server:

```bash
# 1. Install Certbot for Nginx
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# 2. Issue Let's Encrypt Certificate
sudo certbot --nginx -d stockflow.example.com -d www.stockflow.example.com

# 3. Test Automatic SSL Certificate Renewal
sudo certbot renew --dry-run
```

---

## 📷 5. Mobile Camera & Barcode Scanner HTTPS Requirement

> [!IMPORTANT]
> Modern web browsers (Chrome, Safari, Edge, Firefox) **strictly enforce HTTPS** for HTML5 Camera Media Devices (`navigator.mediaDevices.getUserMedia`).
> - Over HTTP, camera access for Barcode / QR Scanning will be **blocked** by browser security policies.
> - Connecting your custom domain with a valid SSL certificate enables seamless mobile barcode scanning in the warehouse!

---

## 🤖 6. Search Engine Privacy & Indexing Protection

StockFlow AI is a private enterprise business application. Search engine indexing is restricted:

- **`static/robots.txt`**: Served at `/static/robots.txt` disallowing crawlers (`Disallow: /`).
- **HTML Meta Tag**: Included `<meta name="robots" content="noindex, nofollow">` in all admin templates.

---

## 🧪 7. Live Domain Post-Deployment Checklist

After pointing DNS records and installing SSL:

1. **Test HTTPS Redirect**: Visit `http://stockflow.example.com` -> Verify automatic 301 redirect to `https://stockflow.example.com`.
2. **Test Health Endpoint**: `curl -I https://stockflow.example.com/health/` -> Verify `HTTP 200 OK`.
3. **Test Mobile Barcode Camera**: Open `https://stockflow.example.com/barcodes/scan/` on mobile -> Verify camera permission prompt appears and scans barcodes cleanly!
