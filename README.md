# Notification Service 

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Architecture](#project-architecture)
3. [Database Structure](#database-structure)
4. [Development and Deployment Guide](#development-and-deployment-guide)
5. [API Usage Guide](#api-usage-guide)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Extension Points](#extension-points)

## Project Overview

### Purpose
The Python Notification Service is a FastAPI-based microservice designed to handle multi-channel notifications with template support, event-driven processing, and deduplication capabilities. It provides a unified platform for managing various types of notifications across different channels like Email and Slack.

### Key Features
- **Multi-Channel Support**: Email (file-based mock) and Slack (console-based mock) with extensible channel architecture
- **Template System**: Jinja2-based templating with variable substitution
- **Event Processing**: Real-time and scheduled event handling
- **Deduplication**: Time-based and content-based duplicate prevention
- **Database Persistence**: SQLAlchemy with SQLite/PostgreSQL support
- **Dependency Injection**: FastAPI's built-in DI system
- **Comprehensive Logging**: Structured logging with configurable levels
- **REST API**: Full REST API with OpenAPI documentation

### Technology Stack
- **Framework**: FastAPI 0.104.1
- **Template Engine**: Jinja2 3.1.2
- **Database**: SQLAlchemy 2.0.23 with SQLite (default) or PostgreSQL
- **Scheduler**: APScheduler 3.10.4
- **Server**: Uvicorn 0.24.0
- **Data Validation**: Pydantic 2.5.0
- **Environment**: Python 3.8+

## Project Architecture

### High-Level Architecture

The notification service follows a layered microservice architecture with clear separation of concerns:

```mermaid
graph TD
    A[FastAPI App] --> B[System Routes]
    A --> C[Events Routes]
    A --> D[Registry Routes]
    
    B --> E[Service Layer]
    C --> E
    D --> E
    
    E --> F[Notification Service]
    E --> G[Scheduler Service]
    E --> H[Template Manager]
    
    F --> I[Channel & Event Layer]
    G --> I
    H --> I
    
    I --> J[Channel Manager<br/>Email, Slack]
    I --> K[Event Manager<br/>Real/Schedule]
    I --> L[Deduplication Manager]
    
    J --> M[Repository Layer]
    K --> M
    L --> M
    
    M --> N[Event Repository]
    M --> O[Notification Repository]
    M --> P[Deduplication Repository]
    
    N --> Q[Database Layer<br/>SQLAlchemy 2.0 with SQLite/PostgreSQL]
    O --> Q
    P --> Q
    
    style A fill:#e1f5fe
    style E fill:#f3e5f5
    style I fill:#fff3e0
    style M fill:#e8f5e8
    style Q fill:#fce4ec
```

### Core Components

#### 1. **Application Layer** (`src/app.py`)
- FastAPI application setup and configuration
- Middleware registration (Logging, Health Check)
- Route registration
- Application lifecycle management (startup/shutdown)
- Exception handling setup

#### 2. **Service Layer**
- **NotificationService** (`src/services/notification_service.py`): Core business logic for notification processing
- **NotificationScheduler** (`src/scheduler.py`): Handles scheduled event processing
- **Template Manager** (`src/templates.py`): Manages template loading, registration, and rendering

#### 3. **Channel Layer** (`src/channels/`)
- **Base Channel** (`base_channel.py`): Abstract base class defining channel interface
- **Email Channel** (`email_channel.py`): File-based email notification implementation
- **Slack Channel** (`slack_channel.py`): Console-based Slack notification implementation
- **Channel Manager** (`channel_manager.py`): Factory for creating and managing channels

#### 4. **Event Layer** (`src/events/`)
- **Base Event** (`base_event.py`): Abstract base class for event sources
- **Event Manager** (`event_manager.py`): Manages event registration and processing
- **Signup Event** (`signup_event.py`): Real-time user signup event implementation
- **Schedule Event** (`schedule_event.py`): Scheduled event implementation
- **Daily Stats Event** (`daily_stat_event.py`): Daily statistics reporting event

#### 5. **Repository Layer** (`src/repositories/`)
- **Database Models** (`database.py`): SQLAlchemy ORM models
- **Event Repository** (`event_repository.py`): Event data access layer
- **Notification Repository** (`notification_repository.py`): Notification data access layer
- **Deduplication Repository** (`deduplication_repository.py`): Deduplication data access layer

#### 6. **Deduplication Layer** (`src/deduplications/`)
- **Base Policy** (`base_policy.py`): Abstract deduplication policy interface
- **Time Window Policy** (`time_window_policy.py`): Time-based deduplication implementation
- **Deduplication Manager** (`deduplication_manager.py`): Manages deduplication policies

### Design Patterns

1. **Strategy Pattern**: Notification channels and deduplication policies
2. **Factory Pattern**: Channel and event creation
3. **Repository Pattern**: Data access abstraction
4. **Dependency Injection**: Service configuration and testing
5. **Observer Pattern**: Event-driven notification processing
6. **Template Method Pattern**: Notification processing workflow

## Database Structure

### Entity Relationship Diagram

```mermaid
erDiagram
    Events {
        UUID id PK
        String type
        JSON data
        DateTime created_at
        DateTime processed_at
        Boolean processed
        Boolean deleted
    }
    
    Templates {
        UUID id PK
        String name UK
        String display_name
        String subject
        String path
        JSON variables
    }
    
    Notifications {
        UUID id PK
        UUID event_id FK
        String template_id
        String channel
        String recipient
        String subject
        Text content
        String content_hash
        String status
        DateTime created_at
        DateTime sent_at
    }
    
    DeduplicationLogs {
        UUID id PK
        String content_hash
        DateTime created_at
    }
    
    Events ||--o{ Notifications : "generates"
    Templates ||--o{ Notifications : "uses"
    Notifications ||--o{ DeduplicationLogs : "creates"
```

### Table Schemas

#### Events Table
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid4(),
    type VARCHAR(50) NOT NULL,
    data JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME NULL,
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_events_type ON events(type);
```

#### Templates Table
```sql
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT uuid4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    path VARCHAR(255) NOT NULL,
    variables JSON NOT NULL
);
```

#### Notifications Table
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid4(),
    event_id UUID NOT NULL,
    template_id VARCHAR(255) NOT NULL,
    channel VARCHAR(255) NOT NULL,
    recipient VARCHAR(2048) NULL,
    subject VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at DATETIME NULL,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE INDEX idx_notifications_event_id ON notifications(event_id);
CREATE INDEX idx_notifications_channel ON notifications(channel);
CREATE INDEX idx_notifications_content_hash ON notifications(content_hash);
```

#### Deduplication Logs Table
```sql
CREATE TABLE deduplication_logs (
    id UUID PRIMARY KEY DEFAULT uuid4(),
    content_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Data Models

The service uses both SQLAlchemy ORM models for database operations and Pydantic models for API validation:

```python
# SQLAlchemy Models (src/repositories/database.py)
class Event(Base):
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    # ... other fields

# Pydantic Models (src/models.py)
class NotificationRequest(BaseModel):
    notification_id: str
    event_data: Dict[str, Any]
    override_channels: Optional[List[str]] = None
```

## Development and Deployment Guide

### Prerequisites
- Python 3.8 or higher
- pip or pipenv for package management
- SQLite (included with Python) or PostgreSQL for production

### Local Development Setup

1. **Clone and Navigate to Project**
```bash
cd /path/to/notif_svc
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env file with your configuration
```

5. **Initialize Database**
```bash
python init_database.py
```

6. **Run the Service**
```bash
# Using the main entry point
python main.py

# Or using uvicorn directly
uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
```

The service will be available at `http://localhost:8000`

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Service Configuration
SERVICE_NAME="Python Notification Service"
SERVICE_VERSION="1.0.0"
SERVICE_HOST="0.0.0.0"
SERVICE_PORT=8000
SERVICE_DEBUG=true

# Database Configuration
DATABASE_URL="sqlite:///./notification_service.db"

# Logging Configuration
LOG_LEVEL="INFO"
LOG_FORMAT="json"

# Scheduler Configuration
SCHEDULER_TIMEZONE="UTC"
SCHEDULER_MAX_WORKERS=5
```

### Database Setup

#### SQLite (Default - Development)
```bash
# Database file will be created automatically
python init_database.py
```

#### PostgreSQL (Production)
```bash
# Update DATABASE_URL in .env
DATABASE_URL="postgresql://user:password@localhost:5432/notification_service"

# Initialize database
python init_database.py
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test files (if available)
python test_validation_fix.py

# Run with coverage
python -m pytest --cov=src --cov-report=html
```

### Production Deployment

#### Using Docker (Recommended)

1. **Create Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Build and Run**
```bash
docker build -t notification-service .
docker run -p 8000:8000 -e DATABASE_URL="your_db_url" notification-service
```

#### Using systemd (Linux)

1. **Create Service File**
```bash
sudo nano /etc/systemd/system/notification-service.service
```

```ini
[Unit]
Description=Python Notification Service
After=network.target

[Service]
Type=exec
User=www-data
WorkingDirectory=/opt/notification-service
Environment=PATH=/opt/notification-service/venv/bin
ExecStart=/opt/notification-service/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

2. **Enable and Start**
```bash
sudo systemctl enable notification-service
sudo systemctl start notification-service
```

#### Using Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Performance Optimization

1. **Database Optimization**
```python
# Use connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True
)
```

2. **Async Processing**
```python
# Enable async processing for I/O operations
@router.post("/notifications/send")
async def send_notification(request: NotificationRequest):
    # Async processing
```

3. **Caching**
```python
# Implement Redis caching for templates
from redis import Redis
cache = Redis.from_url("redis://localhost:6379")
```

## API Usage Guide

### Service Information

#### Get Service Status
```bash
GET /
```

**Response:**
```json
{
  "message": "Python Notification Service",
  "version": "1.0.0"
}
```

#### Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-08T00:00:00.000Z"
}
```

### Event Management

#### Create Real-Time Event
```bash
POST /events/real-time
Content-Type: application/json

{
  "source": "user_service",
  "event_type": "signup",
  "data": {
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "service_name": "MyApp",
    "recipient": "john@example.com",
    "slack_channel": "#new-users",
    "join_date": "2025-01-08"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Real-time event processed successfully",
  "event_id": "uuid-event-id"
}
```

#### Create Scheduled Event
```bash
POST /events/scheduled
Content-Type: application/json

{
  "source": "daily_stats_service",
  "cron": "0 9 * * *",
  "data": {
    "query": "SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE",
    "recipients": ["admin@example.com"]
  },
  "enabled": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Scheduled event created successfully",
  "event_id": "uuid-event-id"
}
```

#### List Scheduled Events
```bash
GET /events/scheduled
```

**Response:**
```json
{
  "status": "success",
  "events": [
    {
      "id": "uuid-event-id",
      "type": "scheduled",
      "data": {
        "source": "daily_stats_service",
        "cron": "0 9 * * *",
        "query": "SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE"
      },
      "created_at": "2025-01-08T00:00:00.000Z",
      "processed": false
    }
  ]
}
```

### Registry Management

#### List Event Sources
```bash
GET /registry/event-sources
```

**Response:**
```json
{
  "sources": [
    {
      "id": "realtime",
      "name": "Real-time Event Source",
      "description": "Processes events immediately as they arrive"
    },
    {
      "id": "scheduled",
      "name": "Scheduled Event Source", 
      "description": "Processes events based on cron schedules"
    }
  ]
}
```

#### List Available Channels
```bash
GET /registry/channels
```

**Response:**
```json
{
  "channels": [
    {
      "id": "email",
      "name": "Email Channel",
      "description": "Sends notifications via email (mock: writes to file)",
      "enabled": true
    },
    {
      "id": "slack",
      "name": "Slack Channel",
      "description": "Sends notifications via Slack (mock: prints to console)",
      "enabled": true
    }
  ]
}
```

#### List Templates
```bash
GET /registry/templates
```

**Response:**
```json
{
  "templates": [
    "user_welcome_email",
    "user_welcome_slack_message",
    "daily_statistics_report"
  ]
}
```

### Error Handling

The API returns standardized error responses:

```json
{
  "detail": "Error description",
  "error_code": "NOTIFICATION_NOT_FOUND",
  "timestamp": "2025-01-08T00:00:00Z"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

### API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Configuration

### Configuration Structure

The service uses a hierarchical configuration system defined in `src/config.py`:

```python
@dataclass
class ServiceConfig:
    name: str = "Python Notification Service"
    version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

@dataclass
class DatabaseConfig:
    url: str = "sqlite:///./notification_service.db"

@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "json"

@dataclass
class SchedulerConfig:
    timezone: str = "UTC"
    max_workers: int = 5

@dataclass
class Config:
    service: ServiceConfig
    database: DatabaseConfig
    logging: LoggingConfig
    scheduler: SchedulerConfig
```

### Notification Registry Configuration

Notifications are configured through Python code in the service initialization:

```python
# Register notification configurations
notifications = [
    NotificationRegistryEntry(
        id="user_signup",
        name="User Signup Notification",
        description="Sent when a new user signs up",
        channels=["email", "slack"],
        template_id="user_welcome",
        event_source="realtime",
        deduplication_policy="time_based",
        enabled=True
    ),
    NotificationRegistryEntry(
        id="daily_stats",
        name="Daily Statistics Report",
        description="Daily statistics report",
        channels=["email"],
        template_id="daily_statistics_report",
        event_source="scheduled",
        deduplication_policy=None,
        enabled=True
    )
]
```

### Template Configuration

Templates can be configured via:

1. **File-based Templates** (in `templates/` directory)
2. **Database Templates** (stored in database)
3. **API Registration** (via REST API)

### Channel Configuration

Channels are configured with specific settings:

```python
# Email Channel Configuration
email_config = {
    "output_directory": "outputs/emails/",
    "file_format": "{event_id}_{timestamp}.eml"
}

# Slack Channel Configuration
slack_config = {
    "default_channel": "#notifications",
    "console_output": True
}
```

## Testing

### Test Structure

The project includes comprehensive tests covering:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Database and service integration
- **API Tests**: REST endpoint testing
- **Scheduler Tests**: Event scheduling functionality

### Running Tests

```bash
# Run all tests (if test framework is set up)
python -m pytest

# Run specific test files (if available)
python test_validation_fix.py

# Run with verbose output
python -m pytest -v

# Run with coverage report
python -m pytest --cov=src --cov-report=html
```

### Test Examples

#### Database Integration Test
```python
def test_database_integration():
    """Test database operations"""
    with DatabaseService() as db_service:
        # Test event creation
        event = db_service.create_event("test_event", {"key": "value"})
        assert event.type == "test_event"
        
        # Test notification creation
        notification = db_service.create_notification(
            event_id=event.id,
            template_id="test_template",
            channel="email",
            content="Test content"
        )
        assert notification.channel == "email"
```

#### API Test
```python
def test_send_notification_api():
    """Test notification API endpoint"""
    response = client.post("/events/send", json={
        "notification_id": "user_signup",
        "event_data": {
            "user_name": "Test User",
            "user_email": "test@example.com"
        }
    })
    assert response.status_code == 200
    assert response.json()["success"] is True
```

## Extension Points

### Adding New Notification Channels

1. **Create Channel Class**
```python
from src.channels.base_channel import NotificationChannel

class SMSChannel(NotificationChannel):
    def __init__(self, config=None):
        super().__init__("sms", config)
    
    async def send(self, event, subject, message):
        # Implement SMS sending logic
        pass
    
    def validate_config(self):
        return True
```

2. **Register Channel**
```python
from src.channels.channel_manager import ChannelManager

ChannelManager.register_channel("sms", SMSChannel)
```

### Adding New Event Sources

1. **Create Event Class**
```python
from src.events.base_event import EventSource

class DatabaseEventSource(EventSource):
    def __init__(self, config):
        super().__init__("database", config)
    
    async def get_events(self):
        # Implement database polling logic
        return events
```

2. **Register Event Source**
```python
from src.events.event_manager import EventManager

EventManager.register_event_source("database", DatabaseEventSource)
```

### Adding New Deduplication Policies

1. **Create Policy Class**
```python
from src.deduplications.base_policy import DeduplicationPolicy

class ContentHashPolicy(DeduplicationPolicy):
    def should_send(self, event, notification_id):
        # Implement content-based deduplication
        return not self.is_duplicate(content_hash)
    
    def record_sent(self, event, notification_id):
        # Record sent notification
        pass
```

2. **Register Policy**
```python
from src.deduplications.deduplication_manager import DeduplicationManager

DeduplicationManager.register_policy("content_hash", ContentHashPolicy)
```

### Adding New Template Sources

1. **Create Template Manager**
```python
from src.templates import TemplateManager

class APITemplateManager(TemplateManager):
    def load_template(self, template_id):
        # Load template from external API
        return template_content
    
    def render_template(self, template_id, variables):
        # Render template with variables
        return subject, body
```

### Custom Configuration

1. **Extend Configuration Classes**
```python
@dataclass
class CustomConfig:
    api_key: str
    webhook_url: str

@dataclass
class ExtendedConfig(Config):
    custom: CustomConfig
```

2. **Use in Services**
```python
def get_custom_config():
    return ExtendedConfig(
        service=ServiceConfig(),
        database=DatabaseConfig(),
        custom=CustomConfig(
            api_key="your-api-key",
            webhook_url="https://your-webhook.com"
        )
    )
```

---

This documentation provides a comprehensive overview of the Python Notification Service architecture, implementation, and usage. For specific implementation details, refer to the source code and inline documentation.
