import uuid, sys, json
sys.path.append("../../analysis_V2")

from flask import Flask, request, redirect, send_file
from natsort import natsorted

from solr_interactor import SolrInteractor


app = Flask(__name__)
app.secret_key="utu"
core = "uuids"
port = 8983
domain = "http://comhis.fi/clusters"

@app.route("/")
def no_function():
	return "TEST"

@app.route("/get_uuid")
def get_uuid():
	print("Req")
	query_hash = request.args.get("query_hash")
	query_terms = json.loads(request.args.get("query_terms"))
	query_terms = validate_terms(query_terms)
	solr = SolrInteractor(core=core, port=port)
	query_uuid = find_uuid(query_hash, solr)
	if query_uuid == None:
		query_uuid = str(uuid.uuid4())
		add_uuid(query_uuid, query_hash, query_terms, solr)
		print(query_uuid, "new")
		return query_uuid
	else:
		print(query_uuid)
		return query_uuid


## See if UUID is in solr already
def find_uuid(query_hash, solr):
	arguments = {"q": 'query_hash:"{}"'.format(query_hash), "wt": "json"}
	response = solr.query_solr(arguments)
	if solr.is_empty(response):
		return None
	else:
		return response["response"]["docs"][0]["query_uuid"]

## Add new uuid to solr
def add_uuid(uuid, query_hash, query_terms, solr):
	uuid_to_add = {"query_uuid": uuid, "query_hash": query_hash, "query_terms": json.dumps(query_terms)}
	solr.update_solr([uuid_to_add]) ## List of dictionaries format


def validate_terms(query_terms):
	terms = {}
	for term, term_value in query_terms.items():
		if term in ["q", "fq", "fl", "start"]:
			terms[term] = term_value

	return terms


if __name__ == "__main__":
	app.run("0.0.0.0")
