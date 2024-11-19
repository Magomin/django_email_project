from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import HttpResponse,redirect
from .models import EmailEvent
from .airtable_config import AIRTABLE_API_KEY, BASE_ID
from pyairtable import Api
from django.contrib.staticfiles import finders
from django.http import HttpResponse, HttpResponseRedirect
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
    """Handle email open tracking."""
    tracking_pixel = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')

    try:
        # Extract and validate parameters
        email_id = request.GET.get('email_id')
        email_column = request.GET.get('email_column')

        if not email_id or not email_column:
            logger.error("Missing required parameters: email_id or email_column")
            return HttpResponse(tracking_pixel, content_type='image/gif')

        email_id = unquote(email_id).strip().lower()
        email_column = unquote(email_column).strip()

        logger.info(f"Processing open tracking for email: {email_id}, column: {email_column}")

        # Find the record using dynamic formula
        formula = f"{{Validated Work Email}} = '{email_id}'"
        records = email_scheduler_table.all(formula=formula)

        if not records:
            logger.warning(f"No record found for email: {email_id}")
            return HttpResponse(tracking_pixel, content_type='image/gif')

        # Fetch the first record
        record = records[0]
        validated_email = record['fields'].get('Validated Work Email')

        # Log for debugging
        logger.info(f"Record found: {record['id']} with Validated Work Email: {validated_email}")

        # Check if the record has the expected email
        if validated_email != email_id:
            logger.warning(f"Mismatch between requested email_id ({email_id}) and Validated Work Email ({validated_email})")
            return HttpResponse(tracking_pixel, content_type='image/gif')

        # Process status update
        record_id = record['id']
        current_status = record['fields'].get(email_column, '')

        logger.info(f"Current status for email {email_id}: {current_status}")

        # Update status only if it's 'Sent'
        if current_status == 'Sent':
            if update_email_status(record_id, email_column, 'Opened'):
                logger.info(f"Successfully updated status to 'Opened' for email {email_id}")
            else:
                logger.error(f"Failed to update status to 'Opened' for email {email_id}")

    except Exception as e:
        logger.error(f"Error in track_open: {e}")

    # Always return the tracking pixel
    return HttpResponse(tracking_pixel, content_type='image/gif')

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
    