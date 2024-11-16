from django.dispatch import Signal, receiver
from django.core.mail import send_mail
from django.conf import settings

# Create a multifunctional custom signal without providing_args
multi_signal = Signal()

# Define a receiver and connect it using @receiver
@receiver(multi_signal)
def send_email(sender, subject, message, recipient_list, **kwargs):
    """
    Sends an email based on the triggered signal.
    
    Parameters:
        sender: The sender of the signal.
        subject: The subject of the email.
        message: The message body of the email.
        recipient_list: A list of email addresses to send the email to.
    """
    if not isinstance(recipient_list, list):
        recipient_list = [recipient_list]  # Ensure recipient_list is a list
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=recipient_list,
        fail_silently=False,
    )

# # Somewhere in your business logic (e.g., models.py, context_processor.py, forms.py views.py)
# from .signals import multi_signal

# def send_email_func(request):
#     # Trigger the signal with error handling
#     multi_signal.send_robust(
#         sender=request.user.__class__,
#         subject = "Welcome to Fruitkha",
#         message = "Hello!",
#         recipient_list = request.user.email
#     )
