import json
from pkg_resources import resource_filename

from flask import Blueprint, request
blueprint = Blueprint('mobileapi', __name__, url_prefix='/api', static_folder='static')

results_wrapper = {}
with open(resource_filename('invenio.modules.mobileapi', 'results.json'), 'r') as results_file:
    results_wrapper = json.loads(results_file.read())

records_list = []
with open(resource_filename('invenio.modules.mobileapi', 'records.json'), 'r') as records_file:
    records_list = json.loads(records_file.read())

records = {int(record['id']): record for record in records_list}

def check_for_access_token(headers):
    if 'Authorization' in headers:
        print headers['Authorization']

## Routes ##

@blueprint.route('/')
def hello_world():
    return "Imposter? Me? Never!"

@blueprint.route('/info')
def get_info():
    check_for_access_token(request.headers)
    with open(resource_filename('invenio.modules.mobileapi', 'info.json'), 'r') as info_file:
        return info_file.read(), 200, {'Content-Type': 'text/json'}

@blueprint.route('/search')
def search():
    check_for_access_token(request.headers)
    args = request.args
    query = args['query']
    sort = args['sort'] if 'sort' in args else 'date'
    pageSize = int(args['pageSize']) if 'pageSize' in args else len(results_wrapper['results'])
    pageStart = int(args['pageStart']) if 'pageStart' in args else 0

    # Sorting
    sort_keys = {
            # Just some random metrics to give different sorts
            'relevance': (lambda result: len(result['title'])),
            'date':      (lambda result: result['date']),
            'citations': (lambda result: len(result['authors'])),
            }
    sort_reverse = {
            'relevance': False,
            'date':      True,
            'citations': True,
            }
    results_wrapper['results'].sort(key=sort_keys[sort], reverse=sort_reverse[sort])

    # Paging
    paged_results_wrapper = results_wrapper.copy()
    paged_results_wrapper['results'] = results_wrapper['results'][pageStart:pageStart+pageSize]
    paged_results_wrapper['paging'] = {
            'pageStart': pageStart,
            'count': len(results_wrapper['results']),
            }

    return json.dumps(paged_results_wrapper), 200, {'Content-Type': 'text/json'}

@blueprint.route('/record/<int:record_id>')
def get_record(record_id):
    check_for_access_token(request.headers)
    if record_id in records:
        return json.dumps(records[record_id]), 200, {'Content-Type': 'text/json'}
    else:
        return "{}", 404  # TODO: an error message?

@blueprint.route('/record/<int:record_id>/files/<file_name>')
def get_record_file(record_id, file_name):
    check_for_access_token(request.headers)

    files_dict = {file_dict['name']: file_dict for file_dict in records[record_id]['files']}

    try:
        file_path = resource_filename('invenio.modules.mobileapi', 'files/' + file_name)
        with open(file_path, 'r') as the_file:
            return the_file.read(), 200, {'Content-Type': files_dict[file_name]['type']}
    except IOError:
        error_message = "404: Record " + str(record_id) + " has no file named " + file_name + "."
        return error_message, 404

