from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import HttpResponse,redirect
from .models import EmailEvent
from .airtable_config import AIRTABLE_API_KEY, BASE_ID
from pyairtable import Api
from django.contrib.staticfiles import finders
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from urllib.parse import unquote
import base64
import logging

EMAIL_SCHEDULER_TABLE = "email_scheduler"
api = Api(AIRTABLE_API_KEY)
email_scheduler_table = api.table(BASE_ID, EMAIL_SCHEDULER_TABLE)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def home(request):
     return HttpResponse("Welcome to the Email Tracking App!")
def get_record_by_email(email_id):
    """Helper function to get record from Airtable"""
    try:
        formula = f"{{Validated Work Email}} = '{email_id}'"
        records = email_scheduler_table.all(formula=formula)
        return records[0] if records else None
    except Exception as e:
        logger.error(f"Error fetching record for {email_id}: {e}")
        return None

def update_email_status(record_id, email_column, new_status, retries=3):
    """
    Helper function to update email status in Airtable with retries
    """
    for attempt in range(retries):
        try:
            email_scheduler_table.update(record_id, {
                email_column: new_status
            })
            logger.info(f"Successfully updated record {record_id} status to '{new_status}'")
            return True
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{retries} failed to update Airtable record {record_id}: {e}")
            if attempt == retries - 1:
                return False

@csrf_exempt
@require_GET
def track_open(request):
    """Handle email open tracking with the company logo."""
    try:
        # Extract and validate parameters
        email_id = request.GET.get('email_id')
        email_column = request.GET.get('email_column')

        if not email_id or not email_column:
            logger.error("Missing parameters in track_open request.")
            return HttpResponse("Missing parameters", status=400)

        email_id = email_id.strip().lower()
        email_column = email_column.strip()

        logger.info(f"Processing open tracking for email: {email_id}, column: {email_column}")

        # Search for the record
        formula = f"{{Validated Work Email}} = '{email_id}'"
        records = email_scheduler_table.all(formula=formula)

        if records:
            record = records[0]
            record_id = record['id']
            current_status = record['fields'].get(email_column, '')

            logger.info(f"Record found: ID {record_id}, current status: {current_status}")

            # Update status if it's "Sent"
            if current_status == 'Sent':
                email_scheduler_table.update(record_id, {email_column: "Opened"})
                logger.info(f"Status updated to 'Opened' for email: {email_id}")
            else:
                logger.info(f"No update needed. Current status: {current_status}")
        else:
            logger.warning(f"No record found for email: {email_id}")

    except Exception as e:
        logger.error(f"Error in track_open: {e}")

    # Serve the company logo
    logo_path = finders.find('images/logo.png')
    if not logo_path:
        logger.error("Company logo not found")
        return HttpResponse("Company logo not found", status=404)
    
    return FileResponse(open(logo_path, 'rb'), content_type='image/png')




def track_click(request):
    email_id = request.GET.get('email_id')
    email_column = request.GET.get('email_column')  # Specify which email status column to update
    destination = request.GET.get('destination')  # Final URL to redirect to

    # Check that all required parameters are present
    if not email_id or not email_column or not destination:
        return HttpResponse("Missing parameters", status=400)

    # Search for the record with the matching email_id in "Validated Work Email"
    records = email_scheduler_table.all(formula=f"{{Validated Work Email}} = '{email_id}'")
    if records:
        record_id = records[0]['id']
        # Update the specified email status to "Clicked"
        email_scheduler_table.update(record_id, {email_column: "Clicked"})
        print(f"Click event logged for {email_id} in column {email_column}.")
    else:
        print(f"Record not found for {email_id}.")
        return HttpResponse("Record not found", status=404)

    # Redirect to the destination URL
    return redirect(destination)

@require_GET
def health_check(request):
    """Simple endpoint to verify the tracking server is running"""
    try:
        # Try to connect to Airtable
        email_scheduler_table.all(max_records=1)
        return HttpResponse("Tracking server is healthy", status=200)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HttpResponse("Tracking server error", status=500)
    