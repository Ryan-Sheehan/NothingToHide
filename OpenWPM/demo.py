from automation import CommandSequence, TaskManager
from flask import Flask, jsonify, abort, make_response, request, url_for




def analyze_sites(sites):
    # The list of sites that we wish to crawl
    NUM_BROWSERS = 2
    #sites = [
    #    "https://www.cnn.com",
    #    "https://www.tufts.edu"
    #]
    
    # Loads the default manager params
    # and NUM_BROWSERS copies of the default browser params
    manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)
    
    # Update browser configuration (use this for per-browser settings)
    for i in range(NUM_BROWSERS):
        # Record HTTP Requests and Responses
        browser_params[i]["http_instrument"] = True
        # Record cookie changes
        browser_params[i]["cookie_instrument"] = True
        # Record Navigations
        browser_params[i]["navigation_instrument"] = True
        # Record JS Web API calls
        browser_params[i]["js_instrument"] = True
        # Record the callstack of all WebRequests made
        browser_params[i]["callstack_instrument"] = True
        # Record DNS resolution
        browser_params[i]["dns_instrument"] = True
    
    
    # Launch only browser 0 headless
    browser_params[0]["display_mode"] = "headless"
    
    # Update TaskManager configuration (use this for crawl-wide settings)
    manager_params["data_directory"] = "~/Desktop/testing/"
    manager_params["log_directory"] = "~/Desktop/testing/"
    
    manager_params['output_format'] = 's3'
    manager_params['s3_bucket'] = 'ihavenothingtohide'
    manager_params['s3_directory'] = '2020-2'
    
    
    # Instantiates the measurement platform
    # Commands time out by default after 60 seconds
    manager = TaskManager.TaskManager(manager_params, browser_params)
    
    # Visits the sites
    for site in sites:
    
        # Parallelize sites over all number of browsers set above.
        command_sequence = CommandSequence.CommandSequence(
            site,
            reset=True,
            callback=lambda success, val=site: print("CommandSequence {} done".format(val)),
        )
    
        # Start by visiting the page
        command_sequence.get(sleep=3, timeout=60)
    
        # Run commands across the three browsers (simple parallelization)
        manager.execute_command_sequence(command_sequence)
    
    # Shuts down the browsers and waits for the data to finish logging
    manager.close()



app = Flask(__name__)


tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol', 
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web', 
        'done': False
    }
]


def make_public_task(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/todo/api/v1.0/tasks', methods=['GET'])
def get_tasks():
    return jsonify({'tasks': [make_public_task(task) for task in tasks]})

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = [task for task in tasks if task['id'] == task_id]
    if len(task) == 0:
        abort(404)
    return jsonify({'task': task[0]})


@app.route('/todo/api/v1.0/tasks', methods=['POST'])
def create_task():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': tasks[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    tasks.append(task)
    return jsonify({'task': task}), 201

@app.route('/sites/api/v1.0', methods=['POST'])
def site_scanner():
    if not request.json or not 'site' in request.json:
        abort(400)
    sites = [request.json['site']]
    analyze_sites(sites)
    
    return jsonify({'sites': sites}), 201

@app.route('/')
def index():
    return "API Test"

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True)

    