import os
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import requests
from jinja2 import Template

# Load env
load_dotenv()

# Setup Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# creds = ServiceAccountCredentials.from_json_keyfile_name(os.getenv("GOOGLE_CREDENTIALS_JSON_PATH"), scope)
creds = ServiceAccountCredentials.from_json_keyfile_name("scheduler/creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID")).sheet1
records = sheet.get_all_records()

# Find entries exactly 2 days old & not notified
today = datetime.date.today()
digest = []
for i, row in enumerate(records, start=2):  # row 1 is header
    sent_date = datetime.datetime.strptime(row['Request Sent Date'], "%Y-%m-%d").date()
    delta = (today - sent_date).days
    if delta == 2:
        accepted = int(row['Number Accepted'])
        total_sent = int(row['Number of Requests Sent'])
        refer_ready = int(row.get('Number - Ready to Refer?', 0))
        digest.append({
            "company": row['Company Name'],
            "accepted": accepted,
            "total": total_sent,
            "refer_ready": refer_ready
        })


# Prepare HTML Email
if digest:
    with open("scheduler/email_template.html") as f:
        template = Template(f.read())
        html = template.render(requests=digest)

    res = requests.post("https://api.resend.com/emails", headers={
        "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}"
    }, json={
        "from": "LinkedIn Tracker <you@resend.dev>",
        "to": os.getenv("MY_EMAIL"),
        "subject": "🔔 Your LinkedIn Follow-Up Digest",
        "html": html
    })
    print("Digest sent:", res.status_code)
    # print(res.)
else:
    print("No new digests to send.")