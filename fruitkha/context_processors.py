from datetime import datetime, timedelta
from .models import ContactDetails, Subscription
from django.contrib import messages
from django.shortcuts import redirect

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


 # Footer
def footer_context(request):
    """
    Context processor to add footer data and handle subscriptions dynamically.
    """
    # Fetch ContactDetails for the footer
    footer = ContactDetails.objects.first()

    # Handle subscription in POST request context
    if request.method == 'POST' and request.path == '/':  # Ensure only footer form is processed
        email = request.POST.get('email')
        if email:
            if not Subscription.objects.filter(email=email).exists():
                Subscription.objects.create(email=email)
                messages.success(request, 'Thank you for subscribing!')
            else:
                messages.info(request, 'You are already subscribed.')
        else:
            messages.error(request, 'Please enter a valid email.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    return {
        'footer': footer,
    }
