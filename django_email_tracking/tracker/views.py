from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import HttpResponse,redirect
from .models import EmailEvent
from .airtable_config import AIRTABLE_API_KEY, BASE_ID
from pyairtable import Api
from django.contrib.staticfiles import finders
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
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


def update_email_status(record_id, email_column, new_status):
    """
    Helper function to update email status in Airtable
    Returns True if update was successful, False otherwise
    """
    try:
        email_scheduler_table.update(record_id, {
            email_column: new_status
        })
        logger.info(f"Successfully updated record {record_id} status to '{new_status}'")
        return True
    except Exception as e:
        logger.error(f"Failed to update Airtable record {record_id}: {e}")
        return False

@csrf_exempt
def track_open(request):
    """Handle email open tracking"""
    try:
        # Get and validate parameters
        email_id = request.GET.get('email_id')
        email_column = request.GET.get('email_column')
        
        if not email_id or not email_column:
            logger.error("Missing required parameters")
            return HttpResponse(status=400)
        
        # Decode parameters
        email_id = unquote(email_id)
        email_column = unquote(email_column)
        
        logger.info(f"Processing open tracking for {email_id} in column {email_column}")
        
        # Find the record
        formula = f"{{Validated Work Email}} = '{email_id}'"
        records = email_scheduler_table.all(formula=formula)
        
        if not records:
            logger.warning(f"No record found for email: {email_id}")
            return HttpResponse(
                base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'),
                content_type='image/gif'
            )
        
        record = records[0]
        current_status = record['fields'].get(email_column, '')
        
        # Update status only if current status is 'Sent'
        if current_status == 'Sent':
            update_email_status(record['id'], email_column, 'Opened')
        else:
            logger.info(f"Status not updated - current status is '{current_status}'")
            
        # Always return tracking pixel
        return HttpResponse(
            base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'),
            content_type='image/gif'
        )
        
    except Exception as e:
        logger.error(f"Error in track_open: {e}")
        # Still return the tracking pixel even if there's an error
        return HttpResponse(
            base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'),
            content_type='image/gif'
        )

@csrf_exempt
def track_click(request):
    """Handle email link click tracking"""
    try:
        # Get and validate parameters
        email_id = request.GET.get('email_id')
        email_column = request.GET.get('email_column')
        destination = request.GET.get('destination')
        
        if not all([email_id, email_column, destination]):
            logger.error("Missing required parameters")
            return HttpResponseRedirect(unquote(destination))
        
        # Decode parameters
        email_id = unquote(email_id)
        email_column = unquote(email_column)
        destination = unquote(destination)
        
        logger.info(f"Processing click tracking for {email_id} in column {email_column}")
        
        # Find the record
        formula = f"{{Validated Work Email}} = '{email_id}'"
        records = email_scheduler_table.all(formula=formula)
        
        if not records:
            logger.warning(f"No record found for email: {email_id}")
            return HttpResponseRedirect(destination)
        
        record = records[0]
        current_status = record['fields'].get(email_column, '')
        
        # Update status to 'Clicked' regardless of current status
        # This ensures we capture clicks even if open tracking failed
        if current_status in ['Sent', 'Opened']:
            update_email_status(record['id'], email_column, 'Clicked')
        else:
            logger.info(f"Status not updated - current status is '{current_status}'")
        
        # Always redirect to destination
        return HttpResponseRedirect(destination)
        
    except Exception as e:
        logger.error(f"Error in track_click: {e}")
        # If there's an error, still redirect to destination
        try:
            return HttpResponseRedirect(unquote(destination))
        except:
            return HttpResponseRedirect('https://fribl.co')  # Fallback destination