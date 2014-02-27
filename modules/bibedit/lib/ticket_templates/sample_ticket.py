"""
	Returns template subject and content for:
	a sample ticket
"""
def get_template_data(record):

	queue = "Test"
	subject = "Test ticket"
	content = "This is a test ticket."

	return (queue, subject, content)