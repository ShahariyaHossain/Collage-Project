from datetime import datetime, timedelta

def countdown_timer(request):
    # Set a fixed start date
    start_date = datetime(2024, 11, 9, 23, 59, 59)  # Fixed start date
    target_date = start_date + timedelta(days=10)  # Target date is 10 days after start date

    # Check if the countdown should be active
    if datetime.now() >= start_date:
        return {
            'start_date': start_date,
            'target_date': target_date
        }
    else:
        # Before the countdown starts
        return {
            'start_date': start_date,
            'target_date': None
        }
