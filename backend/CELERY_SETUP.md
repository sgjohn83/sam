# Celery Setup for Fee Payment Reminders

## Overview
The system uses Celery for asynchronous task processing and Celery Beat for periodic tasks (cron jobs). The main periodic tasks are:

1. **Fee Payment Reminders** - Sends reminders 3 days and 1 day before payment deadline (runs daily at 9 AM)
2. **Overdue Fee Notifications** - Sends urgent notifications for overdue payments (runs daily at 10 AM)

## Setup Instructions

### 1. Install Dependencies
```bash
pip install celery==5.3.6 redis
```

### 2. Start Redis (Message Broker)
Celery requires a message broker. Redis is configured as the default.

**On Windows:**
- Download Redis for Windows from: https://github.com/microsoftarchive/redis/releases
- Run `redis-server.exe`

**On Linux/Mac:**
```bash
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                 # Mac
redis-server                       # Start Redis
```

### 3. Configure Environment Variables
Ensure these are in your `.env` file:
```bash
REDIS_URL=redis://localhost:6379/0
```

### 4. Running Celery

#### Start Celery Worker (processes tasks)
```bash
cd backend
celery -A config worker --loglevel=info
```

#### Start Celery Beat (schedules periodic tasks)
```bash
cd backend
celery -A config beat --loglevel=info
```

#### Or run both in one command (development):
```bash
cd backend
celery -A config worker --beat --loglevel=info
```

## Task Details

### `send_fee_payment_reminders()`
- **Schedule:** Daily at 9:00 AM UTC
- **Purpose:** Sends email and push notifications to students whose payment deadline is approaching
- **Reminder schedule:** 3 days before deadline and 1 day before deadline
- **Targets:** Applications with `status=FEE_PENDING`, `fee_paid=False`, and deadline matching target date

### `send_overdue_fee_notifications()`
- **Schedule:** Daily at 10:00 AM UTC
- **Purpose:** Sends urgent notifications for overdue payments
- **Targets:** Applications with `status=FEE_PENDING`, `fee_paid=False`, and deadline in the past
- **Notification type:** `fee_payment_overdue` (separate from regular reminders)

## Testing Tasks

### Manual Testing (Django Shell)
```python
from admissions.tasks import send_fee_payment_reminders, send_overdue_fee_notifications

# Test reminder task
send_fee_payment_reminders.delay()

# Test overdue task
send_overdue_fee_notifications.delay()
```

### Checking Task Status
```bash
# View scheduled tasks
celery -A config inspect scheduled

# View active workers
celery -A config inspect active

# View registered tasks
celery -A config inspect registered
```

## Monitoring

### Logs
Tasks log to Django's logging system with logger name `admissions.tasks`. Check:
- Console output when running Celery
- Django logs in `logs/` directory

### Database
Check `notifications_notificationlog` table for sent notifications:
```sql
SELECT * FROM notifications_notificationlog 
WHERE notification_type IN ('fee_payment_reminder', 'fee_payment_overdue')
ORDER BY created_at DESC;
```

## Troubleshooting

### Common Issues

1. **"No module named 'celery'"**
   ```bash
   pip install celery==5.3.6
   ```

2. **Redis connection error**
   - Ensure Redis is running: `redis-cli ping` should return `PONG`
   - Check `REDIS_URL` in `.env` file

3. **Tasks not running on schedule**
   - Verify Celery Beat is running
   - Check timezone settings in `config/settings.py` and `config/celery.py`

4. **Django model import errors in tasks**
   - Ensure Django is properly initialized
   - Tasks should be run through Celery, not directly imported

### Timezone Configuration
- Django timezone: Set in `config/settings.py` (`TIME_ZONE = 'Asia/Kolkata'`)
- Celery timezone: Set to UTC in `config/celery.py` (`app.conf.timezone = 'UTC'`)
- Schedule times in Celery Beat are in UTC

## Production Deployment

For production, consider:
1. Using `django-celery-beat` for database-backed schedules
2. Running Celery as a system service (systemd, supervisor)
3. Using Redis Sentinel or Redis Cluster for high availability
4. Monitoring with Flower: `pip install flower && celery -A config flower`