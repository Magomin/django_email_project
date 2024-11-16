from django.db import models

class EmailEvent(models.Model):
    event_type = models.CharField(max_length=50)  # Type of event, e.g., "opened" or "clicked"
    timestamp = models.DateTimeField(auto_now_add=True)  # Automatically set the date/time when created

    def __str__(self):
        return f"{self.event_type} at {self.timestamp}"

