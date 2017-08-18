import handlers
from flask import Flask, request
app = Flask(__name__)
core = "finnish-news"


@app.route("/fin_news/analysis/")
#def reroute():
#	args = request.args
#	function = args.get("func")
#	if func == "to_tsv":
#		
#
@app.route("/fin_news/analysis/to_tsv", methods=["GET"])
def to_tsv():
	tsv_handler = handlers.TSVHandler(arguments=request.args, solr_core=core)
	return tsv_handler.query_to_tsv()
