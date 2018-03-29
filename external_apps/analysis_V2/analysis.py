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

''' TSV '''


@app.route("/clusters/analysis/to_tsv")
def to_tsv():
	tsv_handler = TSVHandler(uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, port=port)
	tsv_filename = "query_{}.tsv".format(datetime.datetime.now().isoformat())
	tsv_response = tsv_handler.make_tsv_response()
	strIO = io.BytesIO()
	strIO.write(tsv_response.encode("utf-8"))
	strIO.seek(0)
	return send_file(strIO, as_attachment=True, attachment_filename=tsv_filename)



''' Analysis '''

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
	analysis_handler = AnalysisHandler(uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, analysis_core=analysis_core, port=port, application_name=app_name, domain=domain)
	cluster_start, cluster_end = int(request.args.get("cs")), int(request.args.get("ce"))
	cluster_frequencies = analysis_handler.get_cluster_frequency_data(cluster_start, cluster_end)
	return json.dumps(cluster_frequencies)

@app.route("/clusters/analysis/cluster_spread")
def analyze_cluster_spread():
	analysis_handler = AnalysisHandler(uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, analysis_core=analysis_core, port=port, application_name=app_name, domain=domain)
	page_info = analysis_handler.generate_page_info()
	return render_template("clust_spread.html", page_info = page_info)

@app.route("/clusters/analysis/cluster_spread_data")
def analyze_cluster_spread_data():
	analysis_handler = AnalysisHandler(uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, analysis_core=analysis_core, port=port, application_name=app_name, domain=domain)
	start_year, end_year, languages, style, minimum_count = int(request.args.get("start")), int(request.args.get("end")), request.args.get("languages"), request.args.get("style"), int(request.args.get("minimum_count"))
	languages = languages.split(",")
	spreads = analysis_handler.get_cluster_spread_counts(start_year, end_year, languages, style, minimum_count)
	print(spreads)
	return json.dumps(spreads)

@app.route("/clusters/analysis/single_cluster_spread")
def analyze_single_cluster_spread():
	analysis_handler = AnalysisHandler(uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, analysis_core=analysis_core, port=port, application_name=app_name, domain=domain)
	page_info = analysis_handler.generate_page_info()
	return render_template("single_clust_spread.html", page_info = page_info)

@app.route("/clusters/analysis/single_cluster_spread_data")
def analyze_single_cluster_spread_data():
	analysis_handler = AnalysisHandler(uuid=request.args.get("uuid"), data_core=data_core, uuid_core=uuid_core, analysis_core=analysis_core, port=port, application_name=app_name, domain=domain)
	spreads = analysis_handler.get_single_cluster_data()
	style = request.args.get("style")
	if spreads == None:
		return json.dumps([])
	else:
		return json.dumps(spreads[style])


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=2323)
