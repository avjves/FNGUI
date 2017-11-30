import handlers, json, uuid, gzip, os
import datetime, sqlite3
import io, base64
from flask import Flask, request, redirect, url_for, make_response, jsonify, render_template, send_file, Response, stream_with_context
from natsort import natsorted
from collections import OrderedDict
app = Flask(__name__)
app.secret_key="utu"
app_name = "Finnish News"
core = "fn-gui"
port = 8983
domain = "http://comhis.fi/clusters"
db = "/Solr/FNGUI/analysis/db"

@app.errorhandler(500)
def error_500(error):
	return "No site to show. Perhaps the UUID is too old?"

@app.route("/clusters/analysis")
def main():
	return redirect(domain)

@app.route("/clusters/analysis/to_tsv")
def to_tsv():
	tsv_handler = handlers.TSVHandler(uuid=request.args.get("uuid"), solr_core=core, solr_port=port)
	response = make_response()
	filename = "query_{}.tsv".format(datetime.datetime.now().isoformat())
	tsv_text = tsv_handler.query_to_tsv_text()
	strIO = io.BytesIO()
	strIO.write(tsv_text.encode("utf-8"))
	strIO.seek(0)
	return send_file(strIO, as_attachment=True, attachment_filename=filename)


@app.route("/clusters/analysis/")
def analyze_index():
	analysis_handler = handlers.AnalysisHandler(analysis_type=None, uuid=request.args.get("uuid"), solr_core=core, solr_port=port, application_name=app_name, domain=domain)
	page_info = analysis_handler.generate_page_info()
	return render_template("index.html", page_info = page_info)

@app.route("/clusters/analysis/hfd")
def analyze_hf_data():
	session_key = process_arguments(request.args.get("uuid"), "hfd")
	datadict = get_from_db(session_key)
	if datadict == None:
		analysis_handler = handlers.AnalysisHandler(analysis_type="hf", uuid=request.args.get("uuid"), solr_core=core, solr_port=port, application_name=app_name, domain=domain, extra_arguments={"scale": request.args.get("scale")})
		data = analysis_handler.query_data()
		datadict = analysis_handler.hit_to_freq(data, unix=False)
		datadict = analysis_handler.seperate(datadict)
		save_to_db(session_key, datadict)
	scale = request.args.get("scale")
	return json.dumps(datadict[scale])

@app.route("/clusters/analysis/hf")
def analyze_hf():
	analysis_handler = handlers.AnalysisHandler(analysis_type="hf", uuid=request.args.get("uuid"), solr_core=core, solr_port=port, application_name=app_name, domain=domain)
	page_info = analysis_handler.generate_page_info()
	return render_template("hit_freq.html", page_info = page_info)

@app.route("/clusters/analysis/ci")
def analyze_ci():
	analysis_handler = handlers.AnalysisHandler(analysis_type="ci", uuid=request.args.get("uuid"), solr_core=core, solr_port=port, application_name=app_name, domain=domain)
	page_info = analysis_handler.generate_page_info()
	return render_template("clust_info.html", page_info = page_info)

@app.route("/clusters/analysis/cid")
def anylze_ci_data():
	session_key = process_arguments(request.args.get("uuid"), "cid")
	datadict = get_from_db(session_key)
	if datadict == None:
		analysis_handler = handlers.AnalysisHandler(analysis_type="ci", uuid=request.args.get("uuid"), solr_core=core, solr_port=port, application_name=app_name, domain=domain)
		data = analysis_handler.query_data()
		ids = analysis_handler.get_cluster_ids(data)
		data = analysis_handler.query_clusters(ids, False)
		datadict = analysis_handler.cluster_info_to_dictionary(data)
		save_to_db(session_key, datadict)
	return json.dumps(datadict)


@app.route("/clusters/analysis/cf")
def analyze_cf():
	analysis_handler = handlers.AnalysisHandler(analysis_type="cf", uuid=request.args.get("uuid"), solr_core=core, solr_port=port, application_name=app_name, domain=domain)
	page_info = analysis_handler.generate_page_info()
	return render_template("clust_freq.html", page_info = page_info)

@app.route("/clusters/analysis/cfd")
def analyze_cf_data():
	session_key = process_arguments(request.args.get("uuid"), "cfd")
	datadict = get_from_db(session_key)
	if datadict == None:
		analysis_handler = handlers.AnalysisHandler(analysis_type="test", uuid=request.args.get("uuid"), solr_core=core, solr_port=port, application_name=app_name, domain=domain, extra_arguments={"ce": request.args.get("ce"), "cs": request.args.get("cs")})
		data = analysis_handler.query_data()
		ids = analysis_handler.get_cluster_ids(data)
		data = analysis_handler.query_clusters(ids, True)
		datadict = analysis_handler.cluster_unix(data)
		save_to_db(session_key, datadict)
	toreturn = datadict[request.args.get("scale")][int(request.args.get("cs")):int(request.args.get("ce"))]
	return json.dumps(toreturn)

### ''''database''' ...

def save_to_db(key, value):
	with gzip.open("{}/{}.gz".format(db, key), "wt") as gzf:
		gzf.write(json.dumps(value))

def get_from_db(key):
	if os.path.exists("{}/{}.gz".format(db, key)):
		with gzip.open("{}/{}.gz".format(db, key), "rt") as gzf:
			return json.loads(gzf.read())
	else:
		return None

def process_arguments(uuid, identifier):
	session_key = identifier + "_" + uuid
	return session_key

if __name__ == "__main__":
	app.run(host="0.0.0.0")
