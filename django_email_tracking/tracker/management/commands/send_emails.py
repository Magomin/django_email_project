# tracker/management/commands/email_sender_command.py

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from urllib.parse import quote
from django.core.management.base import BaseCommand
from pyairtable import Api
from ...airtable_config import AIRTABLE_API_KEY, BASE_ID
from ...smtp_config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL
import os
import time

# Airtable setup
EMAIL_SCHEDULER_TABLE = "email_scheduler"
api = Api(AIRTABLE_API_KEY)
email_scheduler_table = api.table(BASE_ID, EMAIL_SCHEDULER_TABLE)


# Placeholder for the server's base URL
BASE_URL = os.getenv("BASE_URL") or "https://matthieu.dontpanic.link"  # Replace with the actual server URL when known

def generate_tracking_urls(email_number, recipient_email):
    """Generate tracking pixel and click tracking URLs for a specific email."""
    encoded_email = quote(recipient_email.strip())
    encoded_column = quote(f"Email {email_number} status")
    
    tracking_pixel_url = f"{BASE_URL}/tracker/track_open/?email_id={encoded_email}&email_column={encoded_column}"
    click_tracking_url = f"{BASE_URL}/tracker/track_click/?email_id={encoded_email}&email_column={encoded_column}&destination={quote('https://fribl.co')}"
    
    print(f"Generated tracking pixel URL: {tracking_pixel_url}")
    print(f"Generated click tracking URL: {click_tracking_url}")
    
    return tracking_pixel_url, click_tracking_url

def send_email_with_tracking(email_number, record):
    try:
        recipient_email = record['fields'].get('Validated Work Email')
        subject = record['fields'].get(f'Subject {email_number}', f"Your Subject for Email {email_number}")
        email_content = record['fields'].get(f'Email {email_number}')
        
        if not recipient_email or not email_content:
            print(f"Skipping email due to missing recipient or content for email number {email_number}")
            return False

        # Generate tracking URLs
        tracking_pixel_url, click_tracking_url = generate_tracking_urls(email_number, recipient_email)

        # Update Airtable with tracking URLs
        email_scheduler_table.update(record['id'], {
            f'Tracking Pixel URL {email_number}': tracking_pixel_url,
            f'Click Tracking URL {email_number}': click_tracking_url
        })

        # HTML email content with tracking pixel and clickable link
        html_content = f"""
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
          </head>
          <body style="margin: 0; padding: 20px; font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto;">
              {email_content}
              
              <p style="margin-top: 20px;">
                <a href="{click_tracking_url}" 
                   style="display: inline-block; 
                          padding: 10px 20px; 
                          background-color: #007bff; 
                          color: white; 
                          text-decoration: none; 
                          border-radius: 5px;">
                  View more details at fribl.co
                </a>
              </p>
              
              <!-- Tracking pixel - invisible -->
              <img src="{tracking_pixel_url}" 
                   alt="" 
                   width="1" 
                   height="1" 
                   style="display: block; width: 1px; height: 1px; border: 0; opacity: 0;">
            </div>
          </body>
        </html>
        """
        
        print(f"HTML content for email {email_number} to {recipient_email}:")
        print(html_content)

        # Prepare the email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email

        # Attach the HTML content
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        # Send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
            print(f"Email {email_number} sent to {recipient_email}")

        # Update status in Airtable
        email_scheduler_table.update(record['id'], {f'Email {email_number} status': "Sent"})
        print(f"Updated status for email {email_number} to 'Sent' in Airtable.")
        return True

    except Exception as e:
        print(f"Error sending email {email_number} to {recipient_email}: {e}")
        email_scheduler_table.update(record['id'], {f'Email {email_number} status': "Failed"})
        print(f"Updated status for email {email_number} to 'Failed' in Airtable.")
        return False

class Command(BaseCommand):
    help = 'Sends scheduled emails with tracking information and updates Airtable statuses'

    def handle(self, *args, **options):
        if BASE_URL == "https://your-server-url.com":
            print("Please set the BASE_URL environment variable or define the server URL in the code.")
            return

        for email_number in [1, 2, 3]:
            formula = f"AND({{Send Date {email_number}}} = TODAY(), {{Email {email_number} status}} != 'Sent')"

            records = email_scheduler_table.all(formula=formula)

            print(f"Processing {len(records)} records for email number {email_number}.")
            for record in records:
                success = send_email_with_tracking(email_number, record)
                if not success:
                    print(f"Failed to process email number {email_number} for record ID {record['id']}")
