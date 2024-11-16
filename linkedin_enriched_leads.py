
import time
import json
from django.core.management.base import BaseCommand
from .linkedinscraperscript import LinkedinScraperScript
from .django_email_tracking.tracker.airtable_config import AIRTABLE_API_KEY, BASE_ID
from pyairtable import Api

NEW_LEADS_TABLE_NAME = "New_Leads_sheet"         
ENRICHED_LEADS_TABLE_NAME = "linkedin_Enriched_Leads_sheet"
AI_ENRICHED_LEADS_TABLE_NAME = "ai_enriched_leads_sheet"


api = Api(AIRTABLE_API_KEY)
new_leads_table = api.table(BASE_ID, NEW_LEADS_TABLE_NAME)
enriched_leads_table = api.table(BASE_ID, ENRICHED_LEADS_TABLE_NAME)
ai_enriched_leads_table = api.table(BASE_ID, AI_ENRICHED_LEADS_TABLE_NAME)

def move_leads(origin_table, destination_table):
    try:
        records = origin_table.all()
        for record in records:
            fields = record['fields']
            # Create a new record in the destination table
            destination_table.create(fields)
            # Delete the record from the origin table
            origin_table.delete(record['id'])
            time.sleep(0.2)  # Respect rate limits
    except Exception as e:
        print(f"Error moving leads: {e}")

# Move new leads to the Enriched Leads table
move_leads(origin_table=new_leads_table, destination_table=enriched_leads_table)

# Initialize the scraper
scraper = LinkedinScraperScript()
scraper.login_to_linkedin()



# Fetch all records from the Enriched Leads table
try:
    records = enriched_leads_table.all()
except Exception as e:
    print(f"Error fetching records: {e}")
    records = []

# Iterate over the records
for record in records:
    record_id = record['id']
    fields = record['fields']
    
    linkedin_url = fields.get('LinkedIn Profile')  # Adjust to match your field name

    if linkedin_url:
        try:
            profile_data = scraper.scrap_company(
                linkedin_url, latest_post=True, about=True, job_openings=True
            )

            # Prepare data to update
            latest_post_data = profile_data.get('Company Latest Post', [])
            formatted_latest_post = (
                json.dumps(latest_post_data)
                if latest_post_data
                else 'No latest post available'
            )

            company_about = profile_data.get('Company About', [])
            formatted_company_about = (
                json.dumps(company_about)
                if company_about
                else 'No about data available'
            )

            job_openings = profile_data.get('Job Openings', [])
            formatted_job_openings = (
                json.dumps(job_openings)
                if job_openings
                else 'No job opening data available'
            )

            # Update the record in Airtable
            enriched_leads_table.update(
                record_id,
                {
                    'Company About': formatted_company_about,  # Adjust field names
                    'Company Latest Post': formatted_latest_post,
                    'Company Job Openings': formatted_job_openings,
                },
            )
            time.sleep(0.2)  # Respect rate limits
        except Exception as e:
            print(f"Error processing record {record_id}: {e}")
