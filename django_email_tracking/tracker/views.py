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
import mimetypes

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
    email_id = request.GET.get('email_id', '').strip()
    email_column = request.GET.get('email_column')

    if not email_id or not email_column:
        return HttpResponse("Missing parameters", status=400)

    try:
        # Query Airtable for the record by email_id
        records = email_scheduler_table.all(
            formula=f"{{Validated Work Email}} = '{email_id}'"
        )
        if not records:
            return HttpResponse("Record not found", status=404)

        # Update the specified column in Airtable
        record_id = records[0]['id']
        email_scheduler_table.update(record_id, {email_column: "Opened"})
    except Exception as e:
        return HttpResponse(f"Error updating Airtable: {e}", status=500)

    # Serve the logo as the tracking pixel
    logo_path = finders.find('images/fribl_logo.png')  # Adjust path if needed
    if not logo_path:
        return HttpResponse("Logo not found", status=404)

    with open(logo_path, 'rb') as logo_file:
        mime_type, _ = mimetypes.guess_type(logo_path)
        response = HttpResponse(logo_file.read(), content_type=mime_type)

    # Set headers to make the image cache-proof
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response



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
    