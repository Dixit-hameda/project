# Electrical Safety Compliance Monitoring System

A complete Flask prototype for electrical safety compliance monitoring with worker and admin flows.

## Features

- Premium responsive Bootstrap 5 interface
- Dark green and white theme
- Animated home page with professional navbar, hero, and footer
- Worker login and admin login
- Daily safety checklist
- Hazard reporting with image upload
- QR code generation and scan verification page
- Dashboard statistics cards
- Chart.js dashboard and analytics charts
- PDF report download
- SQLite database
- Separate templates, CSS, and JavaScript files

## Demo Credentials

- Worker badge: `ES-1042`
- Admin username: `admin`
- Admin password: `admin123`

## Run in VS Code

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Folder Structure

```text
.
├── app.py
├── requirements.txt
├── instance/
│   └── safety.db
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── uploads/
└── templates/
    ├── base.html
    ├── home.html
    ├── about.html
    ├── worker_login.html
    ├── admin_login.html
    ├── checklist.html
    ├── hazard_report.html
    ├── qr.html
    ├── scan.html
    ├── dashboard.html
    └── analytics.html
```
