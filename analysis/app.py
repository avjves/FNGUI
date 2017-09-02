import handlers, json
import pygal, datetime
import io, base64
from flask import Flask, request, redirect, url_for, make_response, jsonify, render_template, send_file, Response, stream_with_context
from natsort import natsorted
from collections import OrderedDict
app = Flask(__name__)
app.secret_key="utu"
core = "finnish-news"
port = 8983

@app.route("/fin_news/analysis")
def main():
	redirect("http://evex.utu.fi/fin_news")

def stream_text(tsv_text):
	for line in tsv_text:
		yield(line + "\n")


@app.route("/fin_news/analysis/to_tsv")
def to_tsv():
	tsv_handler = handlers.TSVHandler(arguments=request.args, solr_core=core, solr_port=port)
	response = make_response()
	filename = "query_{}.tsv".format(datetime.datetime.now().isoformat())
	tsv_text = tsv_handler.query_to_tsv_text()
	strIO = io.BytesIO()
	strIO.write(tsv_text.encode("utf-8"))
	strIO.seek(0)
	return send_file(strIO, as_attachment=True, attachment_filename=filename)
	return response


@app.route("/fin_news/analysis/")
def analyze_index():
	analysis_handler = handlers.AnalysisHandler(analysis_type=None, arguments=request.args, solr_core=core, solr_port=port)
	pageurls = analysis_handler.generate_pageurls()
	return render_template("index.html", pageurls=pageurls)
	
@app.route("/fin_news/analysis/hfd")
def analyze_hf_data():
	arguments, session_inf, session_key = process_arguments(request.args, "hfd")
	db = open_db()
	if session_key not in db:
		analysis_handler = handlers.AnalysisHandler(analysis_type="hf", arguments=arguments, solr_core=core, solr_port=port)
		data = analysis_handler.query_data()
		datadict = analysis_handler.hit_to_freq(data, unix=False)
		datadict = analysis_handler.seperate(datadict)
		db[session_key] = datadict
	else:
		datadict = db[session_key]
	toreturn = datadict[session_inf["scale"]]
	return json.dumps(toreturn)
	
@app.route("/fin_news/analysis/hf")
def analyze_hf():
	analysis_handler = handlers.AnalysisHandler(analysis_type="hf", arguments=request.args, solr_core=core, solr_port=port)
	pageurls = analysis_handler.generate_pageurls()
	return render_template("hit_freq.html", pageurls=pageurls)

@app.route("/fin_news/analysis/ci")
def analyze_ci():
	analysis_handler = handlers.AnalysisHandler(analysis_type="ci", arguments=request.args, solr_core=core, solr_port=port)
	pageurls = analysis_handler.generate_pageurls()
	return render_template("clust_info.html", pageurls=pageurls)

@app.route("/fin_news/analysis/cid")
def anylze_ci_data():
	analysis_handler = handlers.AnalysisHandler(analysis_type="ci", arguments=request.args, solr_core=core, solr_port=port)
	data = analysis_handler.query_data()
	ids = analysis_handler.get_cluster_ids(data)
	data = analysis_handler.query_clusters(ids, False)
	datadict = analysis_handler.cluster_info_to_dictionary(data)
	return json.dumps(datadict)


@app.route("/fin_news/analysis/cf")
def analyze_cf():
	analysis_handler = handlers.AnalysisHandler(analysis_type="cf", arguments=request.args, solr_core=core, solr_port=port)
	pageurls = analysis_handler.generate_pageurls()
	return render_template("clust_freq_dev_2.html", pageurls=pageurls)
	#arguments=request.args

@app.route("/fin_news/analysis/cfd")
def analyze_cf_data():
	arguments, session_inf, session_key = process_arguments(request.args, "cfd")
	print(session_key)
	db = open_db()
	if session_key not in db:
	#if session_key not in session:
		analysis_handler = handlers.AnalysisHandler(analysis_type="test", arguments=arguments, solr_core=core, solr_port=port)
		data = analysis_handler.query_data()
		ids = analysis_handler.get_cluster_ids(data)
		data = analysis_handler.query_clusters(ids, True)
		datadict = analysis_handler.cluster_unix(data)
		db[session_key] = datadict
	else:
		datadict = db[session_key]
	toreturn = datadict[session_inf["scale"]][session_inf["cs"]:session_inf["ce"]]
	#return json.dumps(toreturn)
	return json.dumps(toreturn)

def open_db():
	import shelve
	db = shelve.open("test.db")
	return db

def process_arguments(arguments, identifier):
	session_args = {}
	scale = arguments.get("scale", None)
	cs, ce = arguments.get("cs", None), arguments.get("ce", None)
	if scale == "month" or scale == "year":
		session_args["scale"] = scale
	else:
		session_args["scale"] = None
	if cs != None:
		session_args["cs"] = int(cs)
	if ce != None:
		session_args["ce"] = int(ce)
	
	arguments = validate_arguments(arguments)
	session_key = str(base64.b64encode((identifier + json.dumps(arguments)).encode()))
	return arguments, session_args, session_key

	
def validate_arguments(arguments):
		allowed_keys = ["filename", "date", "year", "location", "language", "cluster_id", "title", "url", "text"]
		allowed_arguments = ["fl", "fq", "sort", "q", "start"]
		args = OrderedDict()
		for key in natsorted(list(arguments.keys())):
			value = arguments[key]
			if key in allowed_arguments:
				args[key] = value
		args["fl"] = "date, year, cluster_id, span, max_reprint_time, avglength, count"
		return args
