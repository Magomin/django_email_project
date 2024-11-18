from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import HttpResponse,redirect
from .models import EmailEvent
import os
from .airtable_config import AIRTABLE_API_KEY, BASE_ID
from pyairtable import Api
import mimetypes

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

    # Search for the record with the matching email_id
    records = email_scheduler_table.all(filter_by_formula=f"{{Validated Work Email}} = '{email_id}'")
    if records:
        record_id = records[0]['id']
        # Update the specified email status to "opened"
        email_scheduler_table.update(record_id, {email_column: "Opened"})

    # Load the Fribl logo to serve as the response
    logo_path = os.path.join('static', 'images', 'fribl_logo.png')  # Adjust path as needed
    with open(logo_path, 'rb') as logo_file:
        # Determine the MIME type of the image file
        mime_type, _ = mimetypes.guess_type(logo_path)
        response = HttpResponse(logo_file.read(), content_type=mime_type)
    
    # Set headers to make it cache-proof and ensure it's freshly loaded each time
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