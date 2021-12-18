import os
import marko
import re

base_dir = 'docs'

skipped_files = [
	'docs/search.md',
	'docs/twitter_wall.md',
	'docs/archive'
]

file_list = []
skip_types = [
	marko.block.HTMLBlock
]

def extract_text(parse_node):
	if not hasattr(parse_node, 'children'):
		return ''
	if type(parse_node) in skip_types:
		return ''
	if type(parse_node.children) == type(''):
		return parse_node.children.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
	result = ''
	for child in parse_node.children:
		result += ' ' + extract_text(child)
	return result

def sanitize_input(text):
	return re.sub('\s+', ' ', re.sub('[^\w\s_-]', ' ', text.lower())).strip()

def extract_blurb(text):
	candidate_splits = ['\n', '.', '|']
	candidate_positions = [text.find(candidate) for candidate in candidate_splits]
	best_candidate = None
	best_position = len(text)
	for i in range(len(candidate_splits)):
		if candidate_positions[i] < 0:
			continue
		if candidate_positions[i] < best_position:
			best_position = candidate_positions[i]
			best_candidate = candidate_splits[i]
	if best_candidate is None:
		return ''
	return text.split(best_candidate)[0]

def sanitize_blurb(text):
	return re.sub('\s+', ' ', text.replace('\n', ' ').replace('\r', ' ')).replace('"', '').replace("'", '').strip()

def index_file(fname):
	if fname in skipped_files:
		return
	if not fname.endswith('.md'):
		return
	with open(fname, 'r') as f:
		text = f.read()
	splits = text.split('---', 2)
	if len(splits) != 3:
		print(f"No 3 splits for file '{fname}', missing header?")
		exit(1)
	title = ''
	text = ''
	# parse header info
	lines = splits[1].split('\n')
	for line in lines:
		line = line.strip()
		if len(line) == 0:
			continue
		line_splits = line.split(':', 1)
		if len(line_splits) != 2:
			continue
		if line_splits[0].strip().lower() != 'title':
			continue
		title = line_splits[1].strip()
		break
	if len(title) == 0:
		print(f"No title found for file '{fname}' missing header?")
		exit(1)
	# parse main markdown file
	markdown_result = marko.parse(splits[2])
	text = extract_text(markdown_result)
	blurb = sanitize_blurb(extract_blurb(text))
	text = sanitize_input(text)
	file_list.append({
		'title': title,
		'text': text,
		'category': 'docs',
		'url': '../' + fname.replace('.md', ''),
		'blurb': blurb
	})

def index_dir(dirname):
	if dirname in skipped_files:
		return
	files = os.listdir(dirname)
	for file in files:
		full_path = os.path.join(dirname, file)
		if os.path.isfile(full_path):
			index_file(full_path)
		elif os.path.isdir(full_path):
			index_dir(full_path)

index_dir(base_dir)

# {
# 	"data": [
# 		{
# 			"title": "Select Statement",
# 			"text": "The SELECT statement retrieves rows from the database",
# 			"category": "docs",
# 			"url": "../docs/sql/statements/select"
# 		},
# 		{
# 			"title": "Update Statement",
# 			"text": "The UPDATE statement modifies the values of rows in a table.",
# 			"category": "docs",
# 			"url": "../docs/sql/statements/update.md"
# 		}
# 	]
# }

result_text = """{
	"data": ["""
for i in range(len(file_list)):
	file = file_list[i]
	title = file['title']
	text = file['text']
	category = file['category']
	url = file['url']
	blurb = file['blurb']
	result_text += "\n\t\t{\n"
	result_text += f'\t\t\t"title": "{title}",\n'
	result_text += f'\t\t\t"text": "{text}",\n'
	result_text += f'\t\t\t"category": "{category}",\n'
	result_text += f'\t\t\t"url": "{url}",\n'
	result_text += f'\t\t\t"blurb": "{blurb}"'
	result_text += "\n\t\t}"
	if i + 1 < len(file_list):
		result_text += ","

result_text += """
	]
}
"""

with open('_data/search_data.json', 'w+') as f:
	f.write(result_text)