from tika import parser

raw = parser.from_file('frontendDeveloper.pdf')
print(raw['content'])
