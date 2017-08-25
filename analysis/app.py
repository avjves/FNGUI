import handlers, json
import pygal, datetime
import io
from flask import Flask, request, redirect, url_for, make_response, render_template, send_file, Response, stream_with_context
app = Flask(__name__)
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

@app.route("/fin_news/analysis/hf")
def analyze_hf():
	analysis_handler = handlers.AnalysisHandler(analysis_type="hf", arguments=request.args, solr_core=core, solr_port=port)
	data = analysis_handler.query_data()
	datadict = analysis_handler.hit_data_to_freq(data)
	pageurls = analysis_handler.generate_pageurls()
	return render_template("hit_freq.html", data=datadict, pageurls=pageurls)

@app.route("/fin_news/analysis/ci")
def analyze_ci():
	analysis_handler = handlers.AnalysisHandler(analysis_type="ci", arguments=request.args, solr_core=core, solr_port=port)
	data = analysis_handler.query_data()
	ids = analysis_handler.get_cluster_ids(data)
	data = analysis_handler.query_clusters(ids, False)
	datadict = analysis_handler.cluster_info_to_dictionary(data)
	pageurls = analysis_handler.generate_pageurls()
	return render_template("clust_info.html", data=datadict, pageurls=pageurls)

@app.route("/fin_news/analysis/cf")
def analyze_cf():
	analysis_handler = handlers.AnalysisHandler(analysis_type="cf", arguments=request.args, solr_core=core, solr_port=port)
	data = analysis_handler.query_data()
	## Let's try: get all hits from the cluster, even if they don't match the query
	ids = analysis_handler.get_cluster_ids(data)
	data = analysis_handler.query_clusters(ids, True)
	print("Q DONE")
	datadict = analysis_handler.cluster_frequency(data)
	pageurls = analysis_handler.generate_pageurls()
	return render_template("clust_freq.html", data=datadict, pageurls=pageurls)
