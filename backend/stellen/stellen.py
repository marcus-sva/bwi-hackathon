from tika import parser
from pprint import pprint
import re


def parse_pdf(pdf_filename):
    """
    parses STELLEN-ID, job title and pdf content from pdf file
    """
    raw = parser.from_file(pdf_filename)
    metadata = raw['metadata']
    #pprint(metadata)
    content = raw['content']
    stellen_id = parse_id(content)
    stellen_title = parse_title(content)
    print("STELLEN_ID: ", stellen_id)
    print("STELLEN_TITLE: ", stellen_title)

def parse_id(content):
    stellen_id = re.search('(?:STELLEN.ID:\\s*)(\\d+)', content)
    return stellen_id.group(1)

def parse_title(content):
    stellen_title = "No title"
    content_lines = content.split('\n')
    for line in content_lines:
        if "Stellenanzeige" in line:
            continue
        if "STELLEN" in line:
            continue
        if len(line) > 10:
            stellen_title = line
            break
    return stellen_title

if __name__ == "__main__":
    pdf_filename = 'frontendDeveloper.pdf'
    parse_pdf(pdf_filename)
