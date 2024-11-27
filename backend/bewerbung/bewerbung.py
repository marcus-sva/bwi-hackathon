from tika import parser
from pprint import pprint
import json
import email
import re


def parse_mail(mail_filename):
    """
    parses subject sender and text from eml file
    """
    with open(mail_filename, 'r') as mail_file:
        file_content = mail_file.read()
        mail = email.message_from_string(file_content)

        header_end = re.search(':.*?\\n\\n+', file_content).span()[1]
        text = file_content[header_end:]

        application_dict = {
                "subject": mail['Subject'],
                "from": mail['From'],
                "text": text 
                }
        application_json = json.dumps(application_dict)
    return application_json

def parse_document(pdf_filename):
    """
    gets text from document
    """
    raw = parser.from_file(pdf_filename)
    metadata = raw['metadata']
    #pprint(metadata)
    content = raw['content']
   
    doc_dict = {
            "file" :  pdf_filename,
            "text": content
            }
    doc_json = json.dumps(doc_dict)
    return doc_json


if __name__ == "__main__":
    mail_filename = 'mail.txt'
    doc_filename = 'Monster_Lebenslauf_muster_Softwareentwickler.pdf'
    json_result = parse_mail(mail_filename)
    #json_result = parse_document(doc_filename)
    #pprint(json_result)
    print(json_result)
