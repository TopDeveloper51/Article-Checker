
# Online Python - IDE, Editor, Compiler, Interpreter

from googleapiclient.discovery import build
from google.oauth2 import service_account
import re
import requests

SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]
DOCUMENT_ID = '1s0fZsDcXJtiwrqUT1fVInS6q1yCZwVKkyCEGcxUiIYY'
SERVICE_ACCOUNT_FILE = 'service_account.json'

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("docs", 'v1', credentials=credentials)

def extract_body_content(document_id):
    document = service.documents().get(documentId=document_id).execute()
    content = document.get('body').get('content')
    return content
    
body_content = extract_body_content(DOCUMENT_ID)

def parse_paragraph(paragraph):
    html_output = "<p>"
    for element in paragraph.get('elements', []):
        text_run = element.get('textRun')
        if text_run:
            content = text_run.get('content', '')
            html_output += content
    html_output += "</p>"
    return html_output

def parse_table(table):
    html_output = "<table>"
    for row in table.get('tableRows', []):
        html_output += "<tr>"
        for cell in row.get('tableCells', []):
            html_output += "<td>"
            for content in cell.get('content', []):
                if 'paragraph' in content:
                    html_output += parse_paragraph(content['paragraph'])
            html_output += "</td>"
        html_output += "</tr>"
    html_output += "</table>"
    return html_output

def convert_to_html(content):
    html_output = ""

    for element in content:
        if 'paragraph' in element:
            html_output += parse_paragraph(element['paragraph'])
        elif 'table' in element:
            html_output += parse_table(element['table'])

    print('HTML output----------', html_output)
    return html_output

html_content = convert_to_html(body_content)
print(html_content)

def analyze_content(content):
    meta_title = ''
    meta_description = ''
    text = ''
    num_images = 0
    num_links = 0
    triger = 1

    for element in content:
        if 'paragraph' in element:
            for text_run in element['paragraph']['elements']:
                if 'textRun' in text_run:
                    currentText = text_run['textRun']['content']
                    print('Current Text:', text_run['textRun'])
                    text += text_run['textRun']['content']
                    
                    if triger == 1:
                        meta_title = currentText.strip()
                        triger = 0
                    if currentText.startswith('Meta Title'):
                        triger = 1
                    if triger == 2:
                        meta_description = currentText.strip()
                        triger = 0
                    if currentText.startswith('Meta Description'):
                        triger = 2
                
                if 'textRun' in text_run and 'link' in text_run['textRun']:
                    num_links += 1
        if 'inlineObjectElement' in element:
            num_images += 1                

    basic_formatting_issues = check_basic_formatting(text)
    return num_images, num_links, basic_formatting_issues, meta_title, meta_description

def check_basic_formatting(text):
    issues = []
    if len(re.findall(r'\n\n\n', text)) > 0:
        issues.append('Too many blank lines')
    if len(re.findall(r'\*\*.*?\*\*', text)) == 0:
        issues.append('No bold text found')
    return issues
    
num_images, num_links, formatting_issues, meta_title, meta_description = analyze_content(body_content)

print('meta title:', meta_title)
print('meta descirption:', meta_description)
print('number of images:', num_images)
print('number of links:', num_links)
print('formatting issues', formatting_issues)

AIRTABLE_API_KEY = 'path2jOW60n6g5GW2.45fa94260cc890f923ae9f9e1b1d03cb6dd78f7f2718c8e0a0dcf26c9840f42e'
BASE_ID = 'appzqKDYxyqTHjcmT'
TABLE_NAME = 'Articles'

def create_airtable_record(meta_title, meta_description, article_title, article_html):
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}'
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'fields': {
            'Meta Title': meta_title,
            'Meta Description': meta_description,
            'Article Title': article_title,
            'Article HTML': article_html,
            'Number of Images': num_images,
            'Number of Links': num_links,
            'Formatting Issues': ', '.join(formatting_issues),
        }
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

response = create_airtable_record('Sample Meta Title', 'Sample Meta Description', 'Sample Article Title', '<html>Sample Article HTML</html>')
print(response)