# D&D Character Creator Tool

A full-stack web application for creating and managing Dungeons & Dragons characters, built with Django and designed for serverless deployment on AWS.

## Features

- Complete D&D character creation wizard (6-step process)
- Support for all classes, species, backgrounds, and feats from the 2024 Player's Handbook
- Character management (create, edit, delete, duplicate)
- Export characters to PDF or JSON
- RESTful API for all character operations
- Responsive design for desktop and mobile

## Tech Stack

- **Backend**: Django 4.2.16 + Django REST Framework
- **Database**: PostgreSQL (production) / SQLite (development)
- **Deployment**: Zappa (AWS Lambda + API Gateway)
- **Frontend**: Django Templates + HTMX + Alpine.js
- **Storage**: AWS S3 (for character portraits and static files)
- **Authentication**: Django authentication + JWT for API

## Prerequisites

- Python 3.11+ (tested with 3.13.5)
- pip and virtualenv
- PostgreSQL (for production) or SQLite (for development)
- AWS account (for deployment)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/DnDCharacterTool.git
cd DnDCharacterTool
```

### 2. Create Virtual Environment

```bash
# Create a new virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Note**: If you encounter issues with `psycopg2-binary` on Python 3.13+, the requirements.txt has been updated to use version 2.9.11 which supports newer Python versions.

### 4. Set Up Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

For local development with SQLite, ensure your `.env` file has empty database values:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (leave empty for local SQLite development)
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

# AWS Configuration (leave empty for local development)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=us-east-1
```

### 5. Create Required Directories

```bash
# Create logs directory (required by Django logging configuration)
mkdir -p logs
```

### 6. Run Database Migrations

```bash
python manage.py migrate
```

### 7. Load Initial Data (Optional)

```bash
# Import D&D game content (classes, species, backgrounds, etc.)
python manage.py import_dnd_data
```

### 8. Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 9. Run the Development Server

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000/`

## Common Setup Issues and Solutions

### 1. PostgreSQL Connection Error

If you see an error about PostgreSQL connection when running the server, make sure your `.env` file has empty database values for local development. The application will automatically use SQLite when no PostgreSQL configuration is provided.

### 2. Missing pkg_resources Module

If you encounter `ModuleNotFoundError: No module named 'pkg_resources'` on Python 3.13+:

```bash
pip install setuptools
```

### 3. Port Already in Use

If port 8000 is already in use, run the server on a different port:

```bash
python manage.py runserver 8001
```

### 4. Missing Logs Directory

If you see `FileNotFoundError` related to `django.log`, create the logs directory:

```bash
mkdir -p logs
```

## Project Structure

```
DnDCharacterTool/
├── characters/          # Character models and API
├── game_content/        # D&D game content (classes, species, etc.)
├── users/              # Custom user model
├── core/               # Core utilities
├── dnd_character_creator/
│   └── settings/       # Django settings
│       ├── base.py     # Common settings
│       ├── local.py    # Local development settings
│       └── production.py # Production settings
├── templates/          # Django templates
├── static/            # Static files
├── data/              # D&D data files
├── manage.py
├── requirements.txt
└── .env.example
```

## API Documentation

Once the server is running, API documentation is available at:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=.
```

## Code Quality

Format code with Black:

```bash
black .
```

Sort imports with isort:

```bash
isort .
```

Run linting with flake8:

```bash
flake8 .
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed AWS deployment instructions using Zappa.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- D&D content based on the 2024 Player's Handbook
- Built with Django and Django REST Framework
- Deployed using Zappa for serverless architecture