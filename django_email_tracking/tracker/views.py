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
    """Handle email open tracking"""
    tracking_pixel = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
    
    try:
        # Get and validate parameters
        email_id = request.GET.get('email_id')
        email_column = request.GET.get('email_column')
        
        if not email_id or not email_column:
            logger.error("Missing required parameters")
            return HttpResponse(tracking_pixel, content_type='image/gif')
        
        # Decode parameters
        email_id = unquote(email_id)
        email_column = unquote(email_column)
        
        logger.info(f"Processing open tracking for {email_id} in column {email_column}")
        
        # Find the record
        record = get_record_by_email(email_id)
        if not record:
            logger.warning(f"No record found for email: {email_id}")
            return HttpResponse(tracking_pixel, content_type='image/gif')
        
        current_status = record['fields'].get(email_column, '')
        logger.info(f"Current status for {email_id}: {current_status}")
        
        # Update status only if current status is 'Sent'
        if current_status == 'Sent':
            success = update_email_status(record['id'], email_column, 'Opened')
            if success:
                logger.info(f"Successfully updated {email_id} status to Opened")
            else:
                logger.error(f"Failed to update {email_id} status to Opened after all retries")
        
    except Exception as e:
        logger.error(f"Error in track_open: {e}")
    
    # Always return tracking pixel
    return HttpResponse(tracking_pixel, content_type='image/gif')

@csrf_exempt
@require_GET
def track_click(request):
    """Handle email link click tracking"""
    try:
        # Get and validate parameters
        email_id = request.GET.get('email_id')
        email_column = request.GET.get('email_column')
        destination = request.GET.get('destination', 'https://fribl.co')  # Default fallback
        
        if not all([email_id, email_column]):
            logger.error("Missing required parameters")
            return HttpResponseRedirect(unquote(destination))
        
        # Decode parameters
        email_id = unquote(email_id)
        email_column = unquote(email_column)
        destination = unquote(destination)
        
        logger.info(f"Processing click tracking for {email_id} in column {email_column}")
        
        # Find the record
        record = get_record_by_email(email_id)
        if not record:
            logger.warning(f"No record found for email: {email_id}")
            return HttpResponseRedirect(destination)
        
        current_status = record['fields'].get(email_column, '')
        logger.info(f"Current status for {email_id}: {current_status}")
        
        # Update status to 'Clicked' if current status is 'Sent' or 'Opened'
        if current_status in ['Sent', 'Opened']:
            success = update_email_status(record['id'], email_column, 'Clicked')
            if success:
                logger.info(f"Successfully updated {email_id} status to Clicked")
            else:
                logger.error(f"Failed to update {email_id} status to Clicked after all retries")
        
    except Exception as e:
        logger.error(f"Error in track_click: {e}")
    
    # Always redirect to destination
    try:
        return HttpResponseRedirect(destination)
    except:
        return HttpResponseRedirect('https://fribl.co')

# Add these to check if the tracking endpoints are alive
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