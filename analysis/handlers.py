import requests, json, pickle, re
import random
from datetime import datetime
from natsort import natsorted
from collections import OrderedDict

# -*- coding: utf-8 -*-
class BaseHandler:

	def __init__(self):
		self.allowed_keys = ["filename", "date", "year", "location", "language", "cluster_id", "title", "url", "text"]
		self.allowed_fields = ["date", "year", "cluster_id", "span", "gap", "avglength", "count"]
		self.allowed_arguments = ["fl", "fq", "sort", "q", "start"]

	def validate_uuid(self, uuid):
		if "/" in uuid or len(uuid) != 36:
			return 0
		try:
			uuid.encode("ascii")
		except UnicodeEncodeError:
			return 0
		return uuid


	def load_arguments(self, uuid):
		print(uuid)
		with open("uuids/{}".format(uuid), "r", encoding="utf-8") as json_file:
			j = json_file.read()
			return json.loads(j)

	def validate_arguments(self,arguments):
		args = {}
		for key, value in arguments.items():
			if key in self.allowed_arguments:
				args[key] = value
		args["fl"] = ", ".join(self.allowed_fields)
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

	def query_solr(self):
		result = self.request(self.port, self.core, self.arguments)
		return result

	def combine_multiple_reqs(self, reqs):
		return [doc for req in reqs for doc in req]

	def request(self, port, core, arguments, max_rows_per_query=1000):
		begin_row = 0
		if "start" in arguments: begin_row = begin_row = int(arguments["start"])
		end_row = int(arguments["rows"])
		reqs = []
		for i in range(begin_row, end_row, max_rows_per_query):
			print("GOT {}".format(i))
			arguments["start"] = i
			arguments["rows"] = max_rows_per_query
			reqs.append(self.format_result_to_json(requests.get("http://localhost:{}/solr/{}/select".format(port, core), data=arguments).text))
			if len(reqs[-1]) < max_rows_per_query-5:
				break
		return self.combine_multiple_reqs(reqs)


	def format_result_to_json(self, text):
	#	print(text)
		text = json.loads(text)
		return text["response"]["docs"]

''' Get data from SOLR, make a HTML BLOB with the data in TSV format '''


class TSVHandler(BaseHandler):

	def __init__(self, uuid, solr_core, solr_port):
		super().__init__()
		self.max_rows = 100000
		self.uuid = self.validate_uuid(uuid)
		self.arguments = self.validate_arguments(self.load_arguments(uuid))
		self.core = solr_core
		self.port = solr_port

	def validate_arguments(self,arguments):
		args = super(TSVHandler, self).validate_arguments(arguments)
		args["fl"] = "count, year, avglength, gap, span, cluster_id, start_location, start_language, first_text, filename, date, location, language, title, url, text, ishit"
		return args

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
		not_hits = []
		curr_keys = set()
		not_hit_keys = set()
		for document in data:
			values = []
			keys = set()
			for key in sorted(list(document.keys())):
				if key == "ishit": continue
				if key == "text":
					values.append(" ".join(str(document[key]).strip().split()))
				else:
					values.append(" ".join(str(document[key]).strip().split()))
				keys.add(key)
			if document["ishit"] == 0:
				not_hits.append("\t".join(values))
				not_hit_keys = not_hit_keys.union(keys)
			else:
				curr_keys = curr_keys.union(keys)
				rows.append("\t".join(values))

		if len(rows) == 0:
			rows.append("\t".join(sorted(list(not_hit_keys))))
			for not_hit in not_hits:
				rows.append(not_hit)
		else:
			rows.insert(0, "\t".join(sorted(list(curr_keys))))
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

	def __init__(self, analysis_type, uuid, solr_core, solr_port, application_name, domain, extra_arguments=None):
		super().__init__()
		self.application_name = application_name
		self.domain = domain
		self.core = solr_core
		self.port = solr_port
		#self.allowed_arguments, self.allowed_keys = self.read_var()
		self.months = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
		self.available_pages = [("home", ""), ("hf", "hf"), ("ci", "ci"), ("cf", "cf"), ("cf_data", "cfd"), ("test_base", "cfd"), ("info_data", "cid"), ("hf_data", "hfd")]
		self.max_rows = self.decide_max_rows(analysis_type)
		self.uuid = self.validate_uuid(uuid)
		self.arguments = self.validate_arguments(self.load_arguments(uuid))
		self.extra_arguments = extra_arguments
		self.num_of_total_hits = 1 ##38189722
		self.max_boolean_clauses = 500
		self.types = ["year", "month"]

	def decide_max_rows(self, analysis_type):
		if analysis_type in ["cf", "ci"]:
			return 500000
		else:
			return 500000

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
		d = {}
		year_count = self.relative_hit_count(year_count)
		month_count = self.relative_hit_count(month_count)
		d["year_labels"], d["year_data"] = self.seperate_dict(year_count)
		d["month_labels"], d["month_data"] = self.seperate_dict(month_count)

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
			info[avail_page_name] = "/clusters/analysis/{}?uuid={}".format(avail_page_link, self.uuid)
		info["cf_data"] += "&cs=0&ce=100"
		info["start"] = self.domain

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

	def query_clusters(self, ids, ishit):
		arguments = {}
		data = []
		for i in range(0, len(ids), self.max_boolean_clauses):
			clusterids = " OR ".join(ids[i:i+self.max_boolean_clauses])
			print(len(ids[i:i+self.max_boolean_clauses]))
			query = "+ishit:{} AND cluster_id:({})".format(int(ishit), clusterids)
			arguments["q"] = query
			arguments = self.validate_arguments(arguments)
			req = self.request(self.port, self.core, arguments)
			data += req
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
			max_reprint_time.append(int(cluster["gap"]))
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
