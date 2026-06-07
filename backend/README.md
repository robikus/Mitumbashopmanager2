# Backend — Mitumba Shop Manager

Django REST API backend for Mitumba Shop Manager.

## Architecture

```
Browser
  ├── GET /              → Django serves templates/index.html (SPA shell)
  ├── GET /static/...    → Nginx serves staticfiles/ directly
  ├── GET /auth/login/   → Django redirects to Cognito Hosted UI
  ├── GET /auth/callback/→ Django exchanges auth code, creates session
  └── GET/POST/DELETE /api/...  → Django REST Framework views
                                   authenticated via Django session
```

## Directory structure

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py         # Shared settings
│   │   ├── production.py   # EC2 production (reads /opt/mitumba/.env)
│   │   └── development.py  # Local dev (reads .env.local)
│   ├── urls.py             # Root URL conf
│   └── wsgi.py             # Gunicorn entrypoint
├── apps/
│   ├── authentication/     # Cognito OIDC, UserProfile model
│   ├── shop_settings/      # Per-user shop config + categories
│   ├── purchases/          # Purchase records
│   ├── sales/              # Sale records + line items
│   ├── dashboard/          # Aggregated dashboard data
│   └── finance/            # Monthly P&L + stock levels
├── templates/index.html    # SPA shell (served for authenticated users)
├── static/
│   ├── css/style.css
│   └── js/app.js
├── requirements.txt
└── deploy.sh
```

## PostgreSQL tables

| Table | Description |
|---|---|
| `auth_user` | Django built-in users |
| `auth_user_profile` | Cognito `sub` UUID + tokens |
| `shop_settings` | Per-user shop configuration |
| `shop_product_category` | Up to 10 categories per user |
| `purchase` | Purchase log (denormalised sellable/cpp) |
| `sale` | Sale log |
| `sale_item` | Individual items within a sale |

## Local development

```bash
# Install PostgreSQL locally and create the dev database
createuser -P mitumba_user     # enter: devpassword
createdb -O mitumba_user mitumba_dev

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure local secrets
cp .env.local.example .env.local
# Edit .env.local with your Cognito details

# Run migrations
python manage.py migrate

# Start dev server
python manage.py runserver
# App available at http://localhost:8000
```

## API reference

### Settings
| Method | URL | Description |
|---|---|---|
| `GET`  | `/api/settings/` | Get user's shop settings |
| `PUT`  | `/api/settings/` | Update all settings |

### Purchases
| Method | URL | Description |
|---|---|---|
| `GET`    | `/api/purchases/`      | List all purchases |
| `POST`   | `/api/purchases/`      | Create purchase |
| `DELETE` | `/api/purchases/<id>/` | Delete purchase |

### Sales
| Method | URL | Description |
|---|---|---|
| `GET`    | `/api/sales/`      | List all sales |
| `POST`   | `/api/sales/`      | Create sale (with nested items) |
| `DELETE` | `/api/sales/<id>/` | Delete sale |

### Dashboard / Finance / Stock
| Method | URL | Description |
|---|---|---|
| `GET` | `/api/dashboard/`          | Current month summary |
| `GET` | `/api/finance/?year=&month=` | Monthly P&L breakdown |
| `GET` | `/api/finance/stock/`       | Current stock levels |

## Production deployment

See [deploy.sh](deploy.sh) and [infrastructure/environments/production/README.md](../infrastructure/environments/production/README.md).
