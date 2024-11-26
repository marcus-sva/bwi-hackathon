from tika import parser
from pprint import pprint
import re
import json


def parse_pdf(pdf_filename):
    """
    parses STELLEN-ID, job title and pdf content from pdf file
    """
    raw = parser.from_file(pdf_filename)
    metadata = raw['metadata']
    #pprint(metadata)
    content = raw['content']
    try:
        stellen_id = parse_id(content)
    except:
        stellen_id = -1
    stellen_title = parse_title(content)
    #print("STELLEN_ID: ", stellen_id)
    #print("STELLEN_TITLE: ", stellen_title)
    stellen_dict = {
            "id": stellen_id,
            "title": stellen_title,
            "text": content,
            "file": pdf_filename
            }
    stellen_json = json.dumps(stellen_dict)
    return stellen_json

def parse_id(content):
    stellen_id = re.search('(?:STELLEN.ID:\\s*)(\\d+)', content)
    return stellen_id.group(1)

def parse_title(content):
    stellen_title = "No title"
    content_lines = content.split('\n')
    for line in content_lines:
        if "Stellenanzeige" in line:
            continue
        if "bewerben" in line:
            continue
        if "STELLEN" in line:
            continue
        if len(line) > 10:
            stellen_title = line
            break
    return stellen_title

if __name__ == "__main__":
    #pdf_filename = 'Scrum Master_AgileCoach_11.2024.pdf'
    pdf_filename = 'frontendDeveloper.pdf'
    json_result = parse_pdf(pdf_filename)
    #pprint(json_result)
    print(json_result)
