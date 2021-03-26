import json

pprint_json = lambda string: json.dumps(json.loads(string),indent=4)
