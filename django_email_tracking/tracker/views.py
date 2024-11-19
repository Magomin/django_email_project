from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import HttpResponse,redirect
from .models import EmailEvent
import os
from .airtable_config import AIRTABLE_API_KEY, BASE_ID
from pyairtable import Api
from django.contrib.staticfiles import finders
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import unquote
import base64

EMAIL_SCHEDULER_TABLE = "email_scheduler"
api = Api(AIRTABLE_API_KEY)
email_scheduler_table = api.table(BASE_ID, EMAIL_SCHEDULER_TABLE)

# tracking/views.py

def home(request):
     return HttpResponse("Welcome to the Email Tracking App!")

@csrf_exempt
def track_open(request):
    """Handle email open tracking"""
    try:
        # Get parameters from the request
        email_id = request.GET.get('email_id')
        email_column = request.GET.get('email_column')
        
        if not email_id or not email_column:
            return HttpResponse(status=400)
            
        # Decode the URL-encoded parameters
        email_id = unquote(email_id)
        email_column = unquote(email_column)
        
        # Find the record in Airtable
        formula = f"{{Validated Work Email}} = '{email_id}'"
        records = email_scheduler_table.all(formula=formula)
        
        if records:
            record = records[0]
            current_status = record['fields'].get(email_column, '')
            
            # Update the status to include "Opened" if not already present
            new_status = 'Opened'
            if current_status and current_status != 'Opened':
                new_status = f"{current_status}, Opened"
                
            email_scheduler_table.update(record['id'], {
                email_column: new_status
            })
            
        # Return a 1x1 transparent GIF
        return HttpResponse(
            base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'),
            content_type='image/gif'
        )
        
    except Exception as e:
        print(f"Error tracking email open: {e}")
        return HttpResponse(status=500)

@csrf_exempt
def track_click(request):
    """Handle email link click tracking"""
    try:
        # Get parameters from the request
        email_id = request.GET.get('email_id')
        email_column = request.GET.get('email_column')
        destination = request.GET.get('destination')
        
        if not all([email_id, email_column, destination]):
            return HttpResponse(status=400)
            
        # Decode the URL-encoded parameters
        email_id = unquote(email_id)
        email_column = unquote(email_column)
        destination = unquote(destination)
        
        # Find the record in Airtable
        formula = f"{{Validated Work Email}} = '{email_id}'"
        records = email_scheduler_table.all(formula=formula)
        
        if records:
            record = records[0]
            current_status = record['fields'].get(email_column, '')
            
            # Update the status to include "Clicked" if not already present
            new_status = 'Clicked'
            if current_status:
                if 'Clicked' not in current_status:
                    new_status = f"{current_status}, Clicked"
                else:
                    new_status = current_status
                    
            email_scheduler_table.update(record['id'], {
                email_column: new_status
            })
        
        # Redirect to the destination URL
        return HttpResponseRedirect(destination)
        
    except Exception as e:
        print(f"Error tracking email click: {e}")
        return HttpResponse(status=500)