import requests, json, pickle, re
import random
from dateutil import parser
from datetime import datetime
from natsort import natsorted
from collections import OrderedDict

''' Get data from SOLR, make a HTML BLOB with the data in TSV format '''

class BaseHandler:
	
	def validate_arguments(self,arguments):
		args = {}
		for key, value in arguments.items():
			if key in self.allowed_arguments:
				args[key] = value
		
		args["fl"] = "date, year, cluster_id, span, max_reprint_time, avglength, count"
		if "fq" in args:
			args["fq"] = self.fix_fq(args["fq"])
		args["wt"] = "json" ## Need json!
		args["hl"] = "false"
		args["rows"] = self.max_rows ## Setting a max for now, may kill Solr/browser if too high
		return args
	
	## broken blacklight format :<
	
	def fix_fq(self, fq):
		if "[" not in fq and "]" not in fq: return fq
		values = json.loads(fq)
		new_fq = [values.pop(0)]
		for val in values:
			field = val.split("f=")[1].split("}")[0]
			value = '"{}"'.format(val.split("}")[1])
			new_fq.append("{}:{}".format(field, value))
		return " AND ".join(new_fq)
		
	#def fix_fq(self, fq):
	#	if "[" not in fq and "]" not in fq: return fq
	#	fq = fq[1:-1] ##remove starting and ending brackets
	#	terms = fq.split('", "{')
	#	new_fq = [terms.pop(0)]
	#	for term in terms:
	#		field = term.split("f=")[1].split("}")[0]
	#		value = '"{}"'.format(term.split("}")[1])
	#		new_fq.append("{}:{}".format(field, value))
	#	return " AND ".join(new_fq)
	
	def query_solr(self):
		result = self.request(self.port, self.core, self.arguments)
		return self.format_result_to_json(result)
	
	def request(self, port, core, arguments):
		print(arguments)
		return requests.get("http://localhost:{}/solr/{}/select".format(port, core), data=arguments).text

	def format_result_to_json(self, text):
		text = json.loads(text)
		return text["response"]["docs"]

	def read_var(self):
		allowed_arguments = ["fl", "fq", "sort", "q", "start"]
		allowed_keys = ["filename", "date", "year", "location", "language", "cluster_id", "title", "url", "text"]
		return allowed_arguments, allowed_keys


class TSVHandler(BaseHandler):

	def __init__(self, arguments, solr_core, solr_port):
		#self.bad_keys = ["stats", "stats.field", "id", "_version_", "ishit"] ## These keys are useless information for us
		#self.keys = ["filename", "date", "year", "location", "language", "cluster_id", "title", "url", "text"]
		self.max_rows = 50000
		self.allowed_arguments, self.allowed_keys = self.read_var()
		self.arguments = self.validate_arguments(arguments)
		self.core = solr_core
		self.port = solr_port



	def query_to_tsv(self):
		data = self.query_solr()
		data = self.data_to_tsv_html_blob(data)
		return data
	

	def query_to_tsv_text(self):
		data = self.query_solr()
		data = self.data_to_tsv_text(data)
		return data
		
	def data_to_tsv_text(self, data):
		rows = []
		rows.append("\t".join(self.allowed_keys))
		for document in data:
			if document["ishit"] == 0: continue
			values = []
			for key in self.allowed_keys:
				if key not in document: continue
				values.append(str(document[key]))
			rows.append("\t".join(values))
		#return rows
		return "\n".join(rows)

	def get_field_keys(self, documents):
		keys = set()
		for document in documents:
			for key in document:
				if key in self.bad_keys: continue
				keys.add(key)
		keys = list(keys)
		keys.sort()
		return keys

	def data_to_tsv_html_blob(self, data):
		values = ["<table>"]
		blob = []
		keys = self.allowed_keys
		values.append("<tr>")
		for key in keys:
			values.append("<td>{}</td>".format(key))
		values.append("</tr>")
		for document in data:
			values.append("<tr>")
			for key in keys:
				if key not in document: continue
				values.append("<td>")
				values.append(str(document[key]))
				values.append("</td>")
			values.append("</tr>")
		
		values.append("</table>")
		
		return "\n".join(values)

class AnalysisHandler(BaseHandler):
	
	def __init__(self, analysis_type, arguments, solr_core, solr_port, application_name):
		self.application_name = application_name
		self.allowed_arguments, self.allowed_keys = self.read_var()
		self.months = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
		self.available_pages = [("home", ""), ("hf", "hf"), ("ci", "ci"), ("cf", "cf"), ("cfd", "cfd"), ("test_base", "cfd"), ("info_data", "cid"), ("hf_data", "hfd")]
		self.max_rows = self.decide_max_rows(analysis_type)
		self.arguments = self.validate_arguments(arguments)
		self.core = solr_core
		self.port = solr_port
		self.num_of_total_hits = 1 ##38189722
		self.max_boolean_clauses = 1000
		self.types = ["year", "month"]

	def decide_max_rows(self, analysis_type):
		if analysis_type in ["cf", "ci"]:
			return 50000
		else:
			return 50000

	def query_data(self):
		data = self.query_solr()
		return data
		
	def seperate_dict(self, dictionary):
		l, d = [], []
		keys = natsorted(list(dictionary.keys()))
		for key in keys:
			l.append(key)
			d.append(dictionary[key])
		return l, d
	
	def hit_data_to_freq(self, data):
		year_count, month_count, day_count = {}, {}, {}
		for value in data:
			if "date" not in value: continue
			year, month, day = value["date"].split("T")[0].split("-")
			year_count[year] = year_count.get(year, 0) + 1
			month_count[year + "_" + month] = month_count.get(year + "_" + month, 0) + 1
			day_count[year + "_" + month + "_" + day] = day_count.get(year + "_" + month + "_" + day, 0) + 1
		d = {}
		year_count = self.relative_hit_count(year_count)
		month_count = self.relative_hit_count(month_count)
		day_count = self.relative_hit_count(day_count)
		d["year_labels"], d["year_data"] = self.seperate_dict(year_count)
		d["month_labels"], d["month_data"] = self.seperate_dict(month_count)
		d["day_labels"], d["day_data"] = self.seperate_dict(day_count)
		
		return d
	
	def hit_to_freq(self, data, unix=True):
		counts = {}
		for type in self.types: counts[type] = {}
		for value in data:
			if "date" not in value: continue
			year, month, day = value["date"].split("T")[0].split("-")
			if unix:
				time_year = int(datetime(int(year), 1, 1).strftime("%s") + "000")
				time_month = int(datetime(int(year), int(month), 1).strftime("%s") + "000")
			else:
				time_year = year
				time_month = year + "_" + month
			counts["year"][time_year] = counts["year"].get(time_year, 0) + 1
			counts["month"][time_month] = counts["month"].get(time_month, 0) + 1
		
		values = {}
		for type in self.types:
			type_values = []
			for key in natsorted(list(counts[type].keys())):
				value = counts[type][key]
				type_values.append([key, value])
			values[type] = type_values
		return values
	
	def seperate(self, data):
		d = {}
		for type, type_data in data.items():
			d[type] = {}
			labels = []
			data = []
			for value in type_data:
				labels.append(value[0])
				data.append(value[1])
			d[type]["labels"] = labels
			d[type]["data"] = data
		return d

	def relative_hit_count(self, count):
		#for key, value in count.items():
		#	count[key] = value / self.num_of_total_hits
		return count
	
	def generate_page_urls(self, info):
		for avail_page_name, avail_page_link in self.available_pages:
			args = []
			for arg, val in self.arguments.items():
				args.append("{}={}".format(arg, val))
			info[avail_page_name] = "/fin_news/analysis/{}?{}".format(avail_page_link, "&".join(args)).replace('"', '%22')
			
		info["cfd"] += "&scale=year&cs=0&ce=100"
		
	def generate_page_info(self):
		info = {}
		self.generate_page_urls(info)
		info["application_name"] = self.application_name
		return info
		
	def get_cluster_ids(self, data):
		ids = set()
		for value in data:
			ids.add(str(value["cluster_id"]))
		return list(ids)
	
	def query_clusters(self, ids, is_hit):
		arguments = {}
		data = []
		for i in range(0, len(ids), self.max_boolean_clauses):
			print(i)
			clusterids = " OR ".join(ids[i:i+self.max_boolean_clauses])
			query = "+ishit:{} AND cluster_id:({})".format(int(is_hit), clusterids)
			arguments["q"] = query
			arguments = self.validate_arguments(arguments)
			data += self.format_result_to_json(self.request(self.port, self.core, arguments))
		return data
	
	def cluster_info_to_dictionary(self, data):
		labels = []
		lengths = []
		counts = []
		max_reprint_time = []
		span = []
		random.seed(0)
		random.shuffle(data)
		for cluster in data:
			labels.append(cluster["cluster_id"])
			lengths.append(int(cluster["avglength"]))
			counts.append(int(cluster["count"]))
			span.append(int(cluster["span"]))
			max_reprint_time.append(int(cluster["max_reprint_time"]))
		d = {}
		d["labels"] = labels
		d["lengths"] = lengths
		d["counts"] = counts
		d["spans"] = span
		d["gaps"] = max_reprint_time
		
		return d
	
	def hits_to_clusters(self, data):
		clusters = {}
		for hit in data:
			clustid = hit["cluster_id"]
			clusters[clustid] = clusters.get(clustid, [])
			clusters[clustid].append(hit)
		return clusters	

	def cluster_unix(self, data):
		clusters = self.hits_to_clusters(data)
		data = {}
		for cluster_key, cluster_data in clusters.items():
			d = self.hit_to_freq(cluster_data)
			data[cluster_key] = d
		
		datadict = {}
		for type in self.types:
			datadict[type] = []
			series = []
			## Ordered, only thing that matters
			for cluster_key in natsorted(list(data.keys())):
				cluster_data = data[cluster_key]
				d = {}
				d["series"] = cluster_data[type]
				d["label"] = cluster_key
				series.append(d)
			datadict[type] = series
		return self.stock_format(datadict)
	
	def stock_format(self, datadict):
		d = {}
		for type, data in datadict.items():
			d[type] = []
			for cluster in data:
				series = {}
				series["name"] = cluster["label"]
				series["data"] = cluster["series"]
				d[type].append(series)
		return d
			
	
		