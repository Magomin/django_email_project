from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import HttpResponse, HttpResponseRedirect
from .models import EmailEvent
import os
from .airtable_config import AIRTABLE_API_KEY, BASE_ID
from pyairtable import Api
import mimetypes
from django.contrib.staticfiles import finders

EMAIL_SCHEDULER_TABLE = "email_scheduler"


api = Api(AIRTABLE_API_KEY)

email_scheduler_table = api.table(BASE_ID, EMAIL_SCHEDULER_TABLE)

# tracking/views.py

def home(request):
     return HttpResponse("Welcome to the Email Tracking App!")


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
    email_id = request.GET.get('email_id', '').strip()
    email_column = request.GET.get('email_column')
    destination = request.GET.get('destination')

    if not email_id or not email_column or not destination:
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
        email_scheduler_table.update(record_id, {email_column: "Clicked"})

        # Redirect to the destination
        return HttpResponseRedirect(destination)
    except Exception as e:
        return HttpResponse(f"Error processing request: {e}", status=500)