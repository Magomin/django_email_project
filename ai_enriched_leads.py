# tracker/management/commands/ai_enriched_leads_command.py

import time
import json
import os
import subprocess
from django.core.management.base import BaseCommand
from .django_email_tracking.tracker.airtable_config import AIRTABLE_API_KEY, BASE_ID
from pyairtable import Api

LINKEDIN_ENRICHED_LEADS_TABLE_NAME = "linkedin_Enriched_Leads_sheet"
AI_ENRICHED_LEADS_TABLE_NAME = "ai_enriched_leads_sheet"

api = Api(AIRTABLE_API_KEY)
linkedin_enriched_leads_table = api.table(BASE_ID, LINKEDIN_ENRICHED_LEADS_TABLE_NAME)
ai_enriched_leads_table = api.table(BASE_ID, AI_ENRICHED_LEADS_TABLE_NAME)

def move_leads(origin_table, destination_table):
    try:
        records = origin_table.all()
        for record in records:
            fields = record['fields']
            destination_table.create(fields)
            origin_table.delete(record['id'])
            time.sleep(0.2)
    except Exception as e:
        print(f"Error moving leads: {e}")

def generate_with_ollama(prompt, model="llama3.2:3b", backstory=None, encoding="utf-8"):
    if backstory:
        prompt = f"{backstory}\n\n{prompt}"
    
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            text=True,
            capture_output=True,
            encoding=encoding,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error generating content:\nStdout: {e.stdout}\nStderr: {e.stderr}")
        return ""

def update_records_batch(table, records_to_update):
    try:
        for record in records_to_update:
            table.update(record['id'], record['fields'])
        print("Batch update successful.")
    except Exception as e:
        print(f"Batch update failed. Error: {str(e)}")

class Command(BaseCommand):
    help = 'Processes AI-enriched leads and updates Airtable records accordingly'

    def handle(self, *args, **options):
        move_leads(origin_table=linkedin_enriched_leads_table, destination_table=ai_enriched_leads_table)
        records = ai_enriched_leads_table.all()
        records_to_update = []

        for record in records:
            fields = record['fields']
            record_id = record['id']
            
            # Process Job Title Simplification
            if 'Job Title Simplified' not in fields:
                first_name = fields.get('First Name', "")
                job_title = fields.get('Job Title', "")
                company_location = fields.get('Location', "")
                prompt =(f"""
                Simplify the following job title: "{job_title}". Ensure the output is in the same language spoken in {company_location}.
                just give the output
                """)
                job_title_simplified = generate_with_ollama(prompt)
                fields['Job Title Simplified'] = job_title_simplified
                print(f"{first_name} actualized: added job_title_simplified")
                records_to_update.append({'id': record_id, 'fields': fields})
            
            # Process Latest Post Simplification
            if 'Latest Post Simplified' not in fields:
                first_name = fields.get('First Name', "")
                company_latest_post = fields.get('Company Latest Post', "")
                company_location = fields.get('Location', "")
                prompt = (f"""
                Simplify the company's latest LinkedIn post: "{company_latest_post}". Ensure it's in {company_location}'s language.
                just give the output
                """)
                latest_post_simplified = generate_with_ollama(prompt)
                fields['Latest Post Simplified'] = latest_post_simplified
                print(f" {first_name} actualized: added latest_post_simplified")
                records_to_update.append({'id': record_id, 'fields': fields})

            # Further field processing, similar to above, for 'Challenges Company', 'Challenges Lead', 'Email 1', 'Email 2', 'Email 3'
            # Add other fields as necessary, e.g., Challenges, Email templates, etc.

            if 'Challenges Company' not in fields:
                first_name = fields.get('First Name', "")
                company_name = fields.get('Company Name', "")
                company_about = fields.get('Company About', "")
                job_openings = fields.get('Job Openings', "")
                company_location = fields.get('Location', "")
                prompt = (f"""
                
    Write the following content in a professional tone, suitable for a corporate audience. Ensure it is written in the same language that is spoken in {company_location}. about the challenges that {company_name}
    may be facing in their hiring process. do it thanks to the {company_about} by stating the common challenges that companies in the industry face.
    also, consider that the company has {job_openings} job openings, and how that could be a challenge for the company. make it short, concise, and to the point. 
    In fact, just give the challenges, no need to explain them, just give the challenges that the company may be facing in their hiring process.
    Ensure it is written in the same language that is spoken in {company_location}.         
            


""")
                challenges_company = generate_with_ollama(prompt)
                fields['Challenges Company'] = challenges_company
                print(f" {first_name} actualized: added challenges_company")
                records_to_update.append({'id': record_id, 'fields': fields})

            if 'Challenges Lead' not in fields:
                job_title_simplified = fields.get('Job Title Simplified', "")
                first_name = fields.get('First Name', "")
                company_about = fields.get('Company About', "")
                company_location = fields.get('Location', "")
                company_name = fields.get('Company Name', "")
                job_openings = fields.get('Job Openings', "")
                backstory_fribl = (f"""
                    Fribl is an AI-powered recruitment solution that streamlines
                    hiring for companies of all sizes by understanding both job requirements and candidate profiles.
                    Fribl has proven effective, reducing recruitment costs by 70% and increasing efficiency by 40%.
                    """)
                
                prompt= (f"""
                        
    write in language the same language that is spoken in the company's location: {company_location}. about the challenges that {company_name} may be facing in their hiring process. do it thanks to the {company_about} by stating the common challenges that companies in the industry face.
    also, consider that the company has {job_openings} job openings, and how that could be a challenge for the company. make it short, concise, and to the point. 
    In fact, just give the challenges, no need to explain them, just give the challenges that the company may be facing in their hiring process.
    Be sure to write  it in the same language that is spoken in the company's location: {company_location}.Write the content in a professional tone, suitable for a corporate audience.
    just give the output
                                
                        
                        """)




                challenges_lead = generate_with_ollama(prompt=prompt, backstory=backstory_fribl)
                fields['Challenges Lead'] = challenges_lead
                print(f" {first_name} actualized: added challenges_lead")
                records_to_update.append({'id': record_id, 'fields': fields})

            if 'Email 1' not in fields:
                first_name = fields.get('First Name', "")
                job_title_simplified = fields.get('Job Title Simplified', "")
                company_name = fields.get('Company Name', "")
                company_location = fields.get('Location', "")
                company_about = fields.get('Company About', "")
                latest_post_simplified = fields.get('Latest Post Simplified', "")
                challenges_company = fields.get('Challenges Company', "")
                challenges_lead = fields.get('Challenges Lead', "")

                prompt =(f"""
                        
    Write a brief and personalized sales email to {first_name}, who is a {job_title_simplified} at {company_name}. Be sure to write  it in the same language that is spoken in the company's location: {company_location}.

    The email should be no longer than three line. selvect and Use the following details you see relevant to point out the value of Fribl:
    - About the company: {company_about}
    - A simplified version of the company's latest post: "{latest_post_simplified}"
    - Challenges faced by the company: {challenges_company}
    - Challenges faced by {first_name} in their role: {challenges_lead}

    Start by greeting {first_name} with a comment about {company_name}'s recent activity, 
    such as the latest post or a specific challenge, to show familiarity with the company.
    Clearly state that you are reaching out from Fribl to offer an AI-powered hiring solution that can help address these challenges by reducing time and costs while improving the quality of candidate matches.
    If relevant, mention how Fribl's technology can specifically help overcome {challenges_company} or {challenges_lead}. End with a call to action inviting {first_name} to discuss how Fribl can support {company_name}'s hiring needs.

    make the email really short, it should be no more than 2 sentences just give the output, dont say here the personlised email, just give the email Sign off the email with "Matthieu" and do not include a subject line.
    Be sure to write  it in the same language that is spoken in the company's location: {company_location}.Write the content in a professional tone, suitable for a corporate audience.
    just give the output             
                        
                        
                        
                        """)
                
                
                
                email_1 = generate_with_ollama(prompt)
                fields['Email 1'] = email_1
                print(f"{first_name} actualized: added email_1")
                records_to_update.append({'id': record_id, 'fields': fields})



            if 'Email 2' not in fields:
                email_1 = fields.get('Email 1', "")
                first_name = fields.get('First Name', "")
                job_title_simplified = fields.get('Job Title Simplified', "")
                company_name = fields.get('Company Name', "")
                company_location = fields.get('Location', "")
                company_about = fields.get('Company About', "")
                latest_post_simplified = fields.get('Latest Post Simplified', "")
                challenges_company = fields.get('Challenges Company', "")
                challenges_lead = fields.get('Challenges Lead', "")
                prompt = (f"""
                        
    Write a brief follow-up email to {first_name}, who is a {job_title_simplified} at {company_name}, following up on the previous message:

    "Dear {first_name},

    {email_1}

    Best regards,
    Matthieu"

    In the follow-up:
    - Greet {first_name} warmly, acknowledging that this is a follow-up message.
    - Remind {first_name} briefly of how Fribl’s AI-powered hiring solution can specifically support {company_name} in addressing challenges like {challenges_company} and {challenges_lead}.
    - Keep it very short, with only one call to action, inviting {first_name} to schedule a brief conversation.
    - End the email with "Best regards, Matthieu" and do not include a subject line.

    Be sure to write it in the same language that is spoken in {company_location} .Write the content in a professional tone, suitable for a corporate audience. Just give the output, dont say here the personlised email,
    just give the output

                        
                        """)
                
                
                
                f"Write a follow-up to {first_name} after the message: '{email_1}'. Make it concise, inviting a response."
                email_2 = generate_with_ollama(prompt)
                fields['Email 2'] = email_2
                print(f"{first_name} actualized: added email_2")
                records_to_update.append({'id': record_id, 'fields': fields})



            if 'Email 3' not in fields:
                email_2 = fields.get('Email 2', "")
                first_name = fields.get('First Name', "")
                job_title_simplified = fields.get('Job Title Simplified', "")
                company_name = fields.get('Company Name', "")
                company_location = fields.get('Location', "")
                company_about = fields.get('Company About', "")
                latest_post_simplified = fields.get('Latest Post Simplified', "")
                challenges_company = fields.get('Challenges Company', "")
                challenges_lead = fields.get('Challenges Lead', "")
        
                prompt = (f"""
                        
    Write a brief third follow-up email to {first_name}, who is a {job_title_simplified} at {company_name}, following up on the previous message:

    "Dear {first_name},

    {email_2}

    Best regards,
    Matthieu"

    In this follow-up:
    - Begin with a friendly greeting, acknowledging that this is a final follow-up.
    - Reiterate briefly how Fribl’s AI-driven recruitment solution can address specific challenges like {challenges_company} and {challenges_lead} at {company_name}.
    - Keep it concise, with a single, clear call to action encouraging {first_name} to reach out if interested.
    - Close the email with "Best regards, Matthieu" and omit a subject line.

    Ensure the email is written in the same language spoken in {company_location}. Write the content in a professional tone, suitable for a corporate audience. Just give the output, dont say here the personlised email,
    just give the output.

                                                    
                        """)
                
                

                email_3 = generate_with_ollama(prompt)
                fields['Email 3'] = email_3
                print(f"{first_name} actualized: added email_3")
                records_to_update.append({'id': record_id, 'fields': fields})
            




        # Batch update records
        if records_to_update:
            update_records_batch(ai_enriched_leads_table, records_to_update)
