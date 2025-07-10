"""
Database initialization script for the notification service.
This script creates the database tables and optionally loads sample data.
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.repositories.database import create_tables
from src.db_service import DatabaseService
from src.templates import DatabaseTemplateManager

def create_database_tables():
    """Create all database tables."""
    print("Creating database tables...")
    try:
        create_tables()
        print("✓ Database tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to create database tables: {e}")
        return False

def load_existing_templates():
    """Load existing JSON templates into the database."""
    print("\nLoading existing templates into database...")
    
    template_manager = DatabaseTemplateManager()
    templates_dir = Path("templates")
    
    if not templates_dir.exists():
        print("No templates directory found, skipping template loading")
        return True
    
    loaded_count = 0
    
    for template_file in templates_dir.glob("*.json"):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if template already exists in database
            existing = template_manager.get_template_by_name(data['name'])
            if existing:
                print(f"  Template '{data['name']}' already exists, skipping")
                continue
            
            # Create template in database
            template_data = template_manager.create_template(
                name=data['name'],
                display_name=data.get('display_name', data['name']),
                subject=data.get('subject', ''),
                body=data['body'],
                variables=data.get('variables', [])
            )
            
            print(f"  ✓ Loaded template: {data['name']} (ID: {template_data.id})")
            loaded_count += 1
            
        except Exception as e:
            print(f"  ✗ Failed to load template {template_file}: {e}")
    
    print(f"✓ Loaded {loaded_count} templates into database")
    return True

def create_sample_data():
    """Create sample events and notifications for testing."""
    print("\nCreating sample data...")
    
    try:
        with DatabaseService() as db_service:
            # Create sample events
            events = [
                {
                    "type": "user_signup",
                    "data": {
                        "user_id": "user_123",
                        "username": "john_doe",
                        "email": "john@example.com",
                        "signup_time": "2024-01-15T10:30:00Z"
                    }
                },
                {
                    "type": "daily_stats",
                    "data": {
                        "date": "2024-01-15",
                        "total_users": 1250,
                        "new_signups": 45,
                        "active_users": 890
                    }
                }
            ]
            
            for event_data in events:
                event = db_service.create_event(
                    event_type=event_data["type"],
                    data=event_data["data"]
                )
                print(f"  ✓ Created sample event: {event_data['type']} (ID: {event.id})")
        
        print("✓ Sample data created successfully")
        return True
        
    except Exception as e:
        print(f"✗ Failed to create sample data: {e}")
        return False

def show_database_stats():
    """Show database statistics."""
    print("\nDatabase Statistics:")
    
    try:
        from src.repositories.database import Event
        
        with DatabaseService() as db_service:
            # Count events
            unprocessed_events = db_service.get_unprocessed_events()
            total_events = db_service.db.query(Event).count()
            
            # Count templates  
            templates = db_service.get_all_templates()
            
            # Get notification stats
            notification_stats = db_service.get_notification_stats()
            
            print(f"  Events: {len(unprocessed_events)} unprocessed, {total_events} total")
            print(f"  Templates: {len(templates)} total")
            print(f"  Notifications: {notification_stats}")
        
    except Exception as e:
        print(f"  Error getting stats: {e}")

def main():
    """Main initialization function."""
    print("Notification Service Database Initialization")
    print("=" * 50)
    
    success = True
    
    # Create database tables
    if not create_database_tables():
        success = False
    
    # Load existing templates
    if success and not load_existing_templates():
        success = False
    
    # Create sample data (optional)
    print("\nWould you like to create sample data? (y/n): ", end="")
    try:
        create_samples = input().lower().startswith('y')
        if create_samples:
            if not create_sample_data():
                success = False
    except (KeyboardInterrupt, EOFError):
        print("\nSkipping sample data creation")
    
    # Show statistics
    show_database_stats()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ Database initialization completed successfully!")
        print("\nThe database is ready for use. You can now:")
        print("  - Start the notification service: python -m uvicorn src.app:app --reload")
        print("  - Run tests: python test_database_integration.py")
        return 0
    else:
        print("✗ Database initialization failed!")
        return 1

if __name__ == "__main__":
    exit(main())
