# Python Notification Service

## Requirements

### Core Functionality
1. **Notification Channels**:
   - Email (mock by writing to files)
   - Slack (mock by printing to console)
   - Design should make it easy to add new channels (SMS, etc.)

2. **Templating**:
   - Use Jinja2 for message templates
   - Templates should support variables from event data

3. **Event Sources**:
   - Real-time: Process lists of dictionaries as events
   - Scheduled: Execute SQL queries (can mock DB results)
   - Queries should support parameterization from event data

4. **Notification Registry**:
   - All system notifications should be easily visible in one place
   - Should show channel, template, and event source configuration

### Design Requirements
- Use clean OOP principles with proper abstractions
- Implement dependency injection for easy testing
- Use modern Python features (type hints, dataclasses, etc.)
- Include clear documentation and example usage
- Design for extensibility (new channels, templates, event sources)

### Implementation Details
1. **Example Notifications**:
   - User Signup:
     - Email: Send welcome email
     - Slack: Post to #new-users channel
   - Daily Stats Report:
     - Email: Send report to admin
     - Source: SQL query (mock with sample data)

2. **Duplicate Prevention**:
   - Design the system to support various deduplication policies
   - Need to implement one example policy.

3. **Configuration**:
   - Can be defined in Python code
   - Should be easy to see all configured notifications

## Evaluation Criteria
1. **Code Quality**:
   - Clean, readable, well-organized
   - Proper use of Python features

2. **Design**:
   - Effective use of OOP principles
   - Appropriate abstractions
   - Extensibility points clear

3. **Completeness**:
   - Core requirements implemented
   - Documentation and examples provided

4. **Modern Python**:
   - Type hints
   - Context managers, decorators where appropriate
   - Proper use of standard library

## Expected Deliverables
1. Working Python implementation
2. Brief documentation:
   - How to add new notifications
   - How to extend channels/templates
   - Example usage
