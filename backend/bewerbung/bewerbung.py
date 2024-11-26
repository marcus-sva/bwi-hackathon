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

if __name__ == "__main__":
    mail_filename = 'mail.txt'
    json_result = parse_mail(mail_filename)
    pprint(json_result)
