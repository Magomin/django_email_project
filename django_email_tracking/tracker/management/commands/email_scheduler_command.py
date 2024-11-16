import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from ...airtable_config import AIRTABLE_API_KEY, BASE_ID
from pyairtable import Api

# Airtable table names
AI_ENRICHED_LEADS_TABLE = "ai_enriched_leads_sheet"
EMAIL_SCHEDULER_TABLE = "email_scheduler"

api = Api(AIRTABLE_API_KEY)
email_scheduler_table = api.table(BASE_ID, EMAIL_SCHEDULER_TABLE)
enriched_leads_table = api.table(BASE_ID, AI_ENRICHED_LEADS_TABLE)

# Check if a date is a weekday
def is_weekday(date):
    return date.weekday() < 5

# Move leads between Airtable tables
def move_leads(origin_table, destination_table):
    try:
        records = origin_table.all()
        for record in records:
            fields = record['fields']
            destination_table.create(fields)
            origin_table.delete(record['id'])
            time.sleep(0.2)  # Respect Airtable rate limits
    except Exception as e:
        print(f"Error moving leads: {e}")

# Define holiday list
holidays = [
    datetime(2023, 12, 25),  # Christmas
    datetime(2023, 1, 1),    # New Year’s Day
    # Add more holidays as needed
]

# Check if a date is a working day
def is_working_day(date):
    return date.weekday() < 5 and date.date() not in [holiday.date() for holiday in holidays]

# Function to add working days to a date
def add_working_days(start_date, days_to_add):
    current_date = start_date
    days_added = 0
    while days_added < days_to_add:
        current_date += timedelta(days=1)
        if is_working_day(current_date):
            days_added += 1
    return current_date

class Command(BaseCommand):
    help = 'Schedules email send dates in Airtable for AI-enriched leads'

    def handle(self, *args, **kwargs):
        # Move leads from enriched table to email scheduler table
        move_leads(origin_table=enriched_leads_table, destination_table=email_scheduler_table)

        # Set email scheduling parameters
        emails_per_day = 400  # Daily email limit
        emails_per_lead = 3   # Emails per lead
        email_interval = 1    # Days between emails
        start_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

        # Initialize send dates with existing dates in Airtable
        all_leads = email_scheduler_table.all(view='Grid view', fields=['Send Date 1', 'Send Date 2', 'Send Date 3'])
        date_email_count = {}

        for lead in all_leads:
            for send_date_field in ['Send Date 1', 'Send Date 2', 'Send Date 3']:
                send_date_str = lead['fields'].get(send_date_field)
                if send_date_str:
                    send_date = datetime.strptime(send_date_str, '%Y-%m-%d')
                    date_str = send_date.strftime('%Y-%m-%d')
                    date_email_count[date_str] = date_email_count.get(date_str, 0) + 1

        # Schedule new leads without assigned dates
        new_leads = email_scheduler_table.all(view='Grid view', formula="AND(NOT({Send Date 1}), {Validated Work Email} != '')")

        for lead in new_leads:
            lead_send_dates = []
            current_date = start_date

            for email_num in range(emails_per_lead):
                # Ensure send date is on a working day
                while not is_working_day(current_date):
                    current_date += timedelta(days=1)

                date_str = current_date.strftime('%Y-%m-%d')
                emails_scheduled = date_email_count.get(date_str, 0)

                # Check if adding an email exceeds daily limit
                while emails_scheduled >= emails_per_day:
                    current_date += timedelta(days=1)
                    while not is_working_day(current_date):
                        current_date += timedelta(days=1)
                    date_str = current_date.strftime('%Y-%m-%d')
                    emails_scheduled = date_email_count.get(date_str, 0)

                # Assign the send date
                lead_send_dates.append(date_str)
                date_email_count[date_str] = emails_scheduled + 1

                # Advance to next working day interval
                current_date = add_working_days(current_date, email_interval)

            # Update Airtable record with assigned send dates
            email_scheduler_table.update(lead['id'], {
                'Send Date 1': lead_send_dates[0],
                'Send Date 2': lead_send_dates[1],
                'Send Date 3': lead_send_dates[2]
            })
