# Sangwoo.top - 杉宇国际贸易有限公司

## Project Structure

```
sangwoo.top/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py       # API endpoints + CRUDAdmin
│   │   ├── database.py   # Database setup
│   │   ├── models.py     # SQLAlchemy models
│   │   └── Dockerfile    # Backend container
│   └── requirements.txt  # Python dependencies
├── frontend/             # Astro frontend (PLAN3)
│   └── dist/             # Built static files
├── nginx/                # Nginx configuration
│   └── sangwoo.top.conf  # SSL + reverse proxy
├── scripts/              # Deployment scripts
│   ├── deploy.sh         # Deploy to EC2
│   ├── setup-ssl.sh      # Setup SSL certificates
│   └── backup.sh         # Database backup
├── data/                 # SQLite database (gitignored)
├── ssl/                  # SSL certificates (gitignored)
└── docker-compose.yml    # Container orchestration
```

## Setup

### Local Development

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run database migrations
python -c "from backend.app.database import init_db; import asyncio; asyncio.run(init_db())"

# Start development server
uvicorn backend.app.main:app --reload --port 8000
```

### Docker Deployment

```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/products | List active products |
| GET | /api/products/{id} | Get product details |
| POST | /api/products | Create product |
| PUT | /api/products/{id} | Update product |
| DELETE | /api/products/{id} | Delete product |
| GET | /api/news | List published news |
| GET | /api/news/{id} | Get news details |
| POST | /api/news | Create news |
| PUT | /api/news/{id} | Update news |
| DELETE | /api/news/{id} | Delete news |
| GET | /api/settings | Get site settings |
| PUT | /api/settings/{key} | Update setting |
| GET | /api/about | Get about page content |
| PUT | /api/about | Update about page |
| GET | /api/contact | Get contact info |
| PUT | /api/contact | Update contact info |
| GET | /api/submissions | List visitor submissions |
| POST | /api/submissions | Submit contact form |
| DELETE | /api/submissions/{id} | Delete submission |
| GET | /api/analytics | Get analytics data |
| POST | /api/analytics | Record analytics event |
| GET | /health | Health check |

## Admin Panel

CRUDAdmin available at `/admin` - provides visual management for all database tables.

## Plans

See `PLAN1.md` through `PLAN7.md` for the complete development roadmap.
