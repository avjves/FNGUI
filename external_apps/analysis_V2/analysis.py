import json, gzip, os, datetime, io

from flask import Flask, request, redirect, send_file, render_template
from natsort import natsorted

from handlers import TSVHandler, AnalysisHandler


app = Flask(__name__)
app.secret_key="utu"
app_name = "Text Reuse in Finnish Newspapers and Journals, 1771-1910"
data_core = "fngui_v4"
uuid_core = "uuids"
analysis_core = "analysis_results"
port = 8983
domain = "http://comhis.fi/clusters"

@app.route("/clusters/analysis")
def no_function():
    return redirect(domain)


@app.route("/clusters/analysis/to_tsv")
def to_tsv():
    tsv_handler = TSVHandler(uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, port=port)
    tsv_filename = "query_{}.tsv".format(datetime.datetime.now().isoformat())
    tsv_response = tsv_handler.make_tsv_response()
    strIO = io.BytesIO()
    strIO.write(tsv_response.encode("utf-8"))
    strIO.seek(0)
    return send_file(strIO, as_attachment=True, attachment_filename=tsv_filename)





@app.route("/clusters/analysis/")
def analyze_index():
	analysis_handler = AnalysisHandler(uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, analysis_core=analysis_core, port=port, application_name=app_name, domain=domain)
	page_info = analysis_handler.generate_page_info()
	return render_template("index.html", page_info = page_info)

@app.route("/clusters/analysis/hit_freq")
def analyze_hf():
	analysis_handler = AnalysisHandler(uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, analysis_core=analysis_core, port=port, application_name=app_name, domain=domain)
	page_info = analysis_handler.generate_page_info()
	return render_template("hit_freq.html", page_info = page_info)

@app.route("/clusters/analysis/cluster_info")
def analyze_ci():
	analysis_handler = AnalysisHandler(uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, analysis_core=analysis_core, port=port, application_name=app_name, domain=domain)
	page_info = analysis_handler.generate_page_info()
	return render_template("clust_info.html", page_info = page_info)

@app.route("/clusters/analysis/cluster_freq")
def analyze_cf():
	analysis_handler = AnalysisHandler(analysis_type="cf", uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, analysis_core=analysis_core, port=port, application_name=app_name, domain=domain)
	page_info = analysis_handler.generate_page_info()
	return render_template("clust_freq.html", page_info = page_info)


@app.route("/clusters/analysis/hit_freq_data")
def analyze_hf_data():
    analysis_handler = AnalysisHandler(uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, analysis_core=analysis_core, port=port, application_name=app_name, domain=domain)
    scale = request.args.get("scale")
    hit_frequencies = analysis_handler.get_hit_frequency_data(scale)
    return json.dumps(hit_frequencies)


@app.route("/clusters/analysis/cluster_info_data")
def analyze_ci_data():
    analysis_handler = AnalysisHandler(uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, analysis_core=analysis_core, port=port, application_name=app_name, domain=domain)
    cluster_info = analysis_handler.get_cluster_info_data()
    return json.dumps(cluster_info)


@app.route("/clusters/analysis/cluster_freq_data")
def analyze_cf_data():
    analysis_handler = AnalysisHandler(uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, analysis_core=analysis_core, port=port, application_name=app-name, domain=domain)
    cluster_start, cluster_end = int(request.args.get("cs")), int(request.args.get("ce"))
    cluster_frequencies = analysis_handler.get_cluster_frequency_data(cluster_start, cluster_end)
    return json.dumps(cluster_frequencies)
# 	session_key = process_arguments(request.args.get("uuid"), "cfd")
# 	datadict = get_from_db(session_key)
# 	if datadict == None:
# 		analysis_handler = handlers.AnalysisHandler(analysis_type="test", uuid=request.args.get("uuid"), solr_core=core, solr_port=port, application_name=app_name, domain=domain, extra_arguments={"ce": request.args.get("ce"), "cs": request.args.get("cs")})
# 		data = analysis_handler.query_data()
# 		ids = analysis_handler.get_cluster_ids(data)
# 		data = analysis_handler.query_clusters(ids, True)
# 		datadict = analysis_handler.cluster_unix(data)
# 		save_to_db(session_key, datadict)
# 	toreturn = datadict[request.args.get("scale")][int(request.args.get("cs")):int(request.args.get("ce"))]
# 	return json.dumps(toreturn)
#
# @app.route("/clusters/analysis/vi")
# def visualize_cluster():
# 	visualization_handler = handlers.VisualizationHandler(analysis_type="vi", uuid=request.args.get("uuid"), solr_core=core, solr_port=port, application_name=app_name, domain=domain)
# 	page_info = visualization_handler.generate_page_info()
# 	return render_template("clust_map.html", page_info=page_info)
#
# @app.route("/clusters/analysis/vid")
# def visualize_cluster_data():
# 	session_key = process_arguments(request.args.get("uuid"), "vid")
# 	datadict = get_from_db(session_key)
# 	if datadict == None:
# 		visualization_handler = handlers.VisualizationHandler(uuid=request.args.get("uuid"), solr_core=core, solr_port=port, application_name=app_name, domain=domain)
# 		data = visualization_handler.query_data()
# 		datadict = visualization_handler.format_data_for_visualization(data)
# 		#save_to_db(session_key, datadict)
# 	return json.dumps(datadict)
#
































### OLD STUFF

# import handlers, json, uuid, gzip, os
# import datetime, sqlite3
# import io, base64
# from flask import Flask, request, redirect, url_for, make_response, jsonify, render_template, send_file, Response, stream_with_context
# from natsort import natsorted
# from collections import OrderedDict
# app = Flask(__name__)
# app.secret_key="utu"
# app_name = "Text Reuse in Finnish Newspapers and Journals, 1771–​1910"
# core = "fngui_v3"
# port = 8983
# domain = "http://comhis.fi/clusters"
# db = "/Solr/FNGUI/analysis/db"
#
# @app.errorhandler(500)
# def error_500(error):
# 	return "No site to show. Perhaps the UUID is too old?"
#
# @app.route("/clusters/analysis")
# def main():
# 	return redirect(domain)
#
# @app.route("/clusters/analysis/to_tsv")
# def to_tsv():
# 	tsv_handler = handlers.TSVHandler(uuid=request.args.get("uuid"), solr_core=core, solr_port=port)
# 	response = make_response()
# 	filename = "query_{}.tsv".format(datetime.datetime.now().isoformat())
# 	tsv_text = tsv_handler.query_to_tsv_text()
# 	strIO = io.BytesIO()
# 	strIO.write(tsv_text.encode("utf-8"))
# 	strIO.seek(0)
# 	return send_file(strIO, as_attachment=True, attachment_filename=filename)
#
#
#
# ### ''''database''' ...
#
# def save_to_db(key, value):
# 	with gzip.open("{}/{}.gz".format(db, key), "wt") as gzf:
# 		gzf.write(json.dumps(value))
#
# def get_from_db(key):
# 	if os.path.exists("{}/{}.gz".format(db, key)):
# 		with gzip.open("{}/{}.gz".format(db, key), "rt") as gzf:
# 			return json.loads(gzf.read())
# 	else:
# 		return None
#
# def process_arguments(uuid, identifier):
# 	session_key = identifier + "_" + uuid
# 	return session_key

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=2323)
