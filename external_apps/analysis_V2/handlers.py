import json, random, gzip
from collections import defaultdict
from operator import itemgetter
from natsort import natsorted

from solr_interactor import SolrInteractor


class TSVHandler:

	def __init__(self, uuid, data_core, uuid_core, port):
		self.uuid = uuid
		self.data_solr = SolrInteractor(data_core, port)
		self.uuid_solr = SolrInteractor(uuid_core, port)
		self.batch_size = 1000 #How many rows to return per batch from Solr
		self.fields = "count, year, avglength, gap, span, cluster_id, start_location, start_language, first_text, filename, date, location, language, title, url, text, is_hit"
		self.cluster_only_fields = "count,year,avglength,gap,span,cluster_id,start_location,start_language,first_text"
		self.hit_only_fields = "filename,date,location,language,title,url,text"

		## Query solr for data and make a TSV response
	def make_tsv_response(self):
		terms = self.uuid_solr.find_terms(self.uuid)
		terms["fl"] = self.fields
		batches = self.data_solr.query_solr_in_batches(terms, self.batch_size)
		return self.format_response_to_TSV(batches)

		## Format batches into TSV response
	def format_response_to_TSV(self, batches):
		## if only one cluster metadata file (is_hit=0) == looking at cluster hits or just search hits
		## if more than one == Looking at multiple clusters
		hits = self.extract_docs(batches)
		discard_hits = self.contains_multiple_cluster_metadata(hits)
		tsv = []
		if discard_hits:
			columns = self.cluster_only_fields
		else:
			columns = self.hit_only_fields

		tsv.append(columns.replace(",", "\t"))
		columns = columns.split(",")
		for hit in hits:
			values = []
			if discard_hits:
				if hit["is_hit"] == 1:
					continue
				for col in columns:
					values.append(hit[col].replace("\t", " ")) ## Make sure no tab char in any field
			else:
				if hit["is_hit"] == 0:
					continue
				for col in columns:
					values.append(hit[col].replace("\t", " ")) ## Same here

			tsv.append("\t".join(values))

		return "\n".join(tsv)


	def contains_multiple_cluster_metadata(self, hits):
		clusters = 0
		for hit in hits:
			if hit["is_hit"] == 0:
				clusters += 1

		if clusters > 1:
			return True
		else:
			return False


	def extract_docs(self, batches):
		hits = []
		for batch in batches:
			for document in batch["response"]["docs"]:
				hits.append(document)

		return hits

class AnalysisHandler:

	def __init__(self, uuid, data_core, uuid_core, analysis_core, port, application_name, domain):
		self.uuid = uuid
		self.data_solr = SolrInteractor(data_core, port)
		self.uuid_solr = SolrInteractor(uuid_core, port)
		self.analysis_solr = SolrInteractor(analysis_core, port)
		self.application_name = application_name
		self.domain = domain
		self.available_pages = ["hit_freq", "cluster_info", "cluster_freq", "cluster_freq_data", "cluster_info_data", "hit_freq_data", "cluster_spread", "cluster_spread_data", "single_cluster_spread_data", "single_cluster_spread"]
		self.batch_size = 1000
		self.max_boolean_clauses = 500


	''' Common methods '''

	## Generate all available links for different analysis, used in flask templates
	def generate_page_info(self):
		info = {}
		info["application_name"] = self.application_name
		info["domain"] = self.domain
		for available_page in self.available_pages:
			info[available_page] = "/clusters/analysis/{}?uuid={}".format(available_page, self.uuid)
		info["cluster_freq_data"] += "&cs=0&ce=100"
		info["home"] = "/clusters/analysis/?uuid={}".format(self.uuid)
		return info

	## Extract documents from responses
	def extract_docs(self, batches):
		hits = []
		for batch in batches:
			for document in batch["response"]["docs"]:
				hits.append(document)

		return hits


	def get_hits_based_on_uuid(self, fl=None):
		terms = self.uuid_solr.find_terms(self.uuid)
		if fl:
			terms["fl"] = fl
		if "cluster_id" in terms["fq"]:
			terms["q"] += " +is_hit:1"
		elif "is_hit" not in terms["fq"]:
			terms["fq"] += " +is_hit:1"
		batches = self.data_solr.query_solr_in_batches(terms, self.batch_size)
		hits = self.extract_docs(batches)
		return hits

	''' Hit frequency methods '''

	def get_hit_frequency_data(self, scale):
		## Check if hits already exist
		arguments = {"q": "+type:hit_freq +uuid:{}".format(self.uuid)}
		hits = self.analysis_solr.query_solr(arguments)
		if self.analysis_solr.is_empty(hits):
			fl = "date"
			hits = self.get_hits_based_on_uuid(fl)
			counts = self.calculate_hit_frequencies(hits)
			data = {"type":"hit_freq", "uuid":self.uuid, "results": json.dumps(counts)}
			self.analysis_solr.update_solr([data]) ## list of dictionaries
		else:
			counts = json.loads(hits["response"]["docs"][0]["results"])

		return counts[scale]


	def calculate_hit_frequencies(self, hits):
		years, months = defaultdict(int), defaultdict(int)
		for hit in hits:
			date = hit["date"]
			year = date.split("-")[0]
			month = year + "_" + date.split("-")[1]
			years[year] += 1
			months[month] += 1
		frequencies = {"year": {"labels": [], "data": []}, "month": {"labels": [], "data": []}}
		for key in natsorted(list(years.keys())):
			frequencies["year"]["labels"].append(key)
			frequencies["year"]["data"].append(years[key])
		for key in natsorted(list(months.keys())):
			frequencies["month"]["labels"].append(key)
			frequencies["month"]["data"].append(months[key])

		return frequencies

	''' Cluster info methods '''

	def get_cluster_info_data(self):
		arguments = {"q": "+type:cluster_info +uuid:{}".format(self.uuid)}
		hits = self.analysis_solr.query_solr(arguments)
		if self.analysis_solr.is_empty(hits):
			cluster_ids = self.get_cluster_ids()
			clusters = self.get_clusters(cluster_ids, fl="cluster_id, gap, span, avglength, count")
			clusters = self.extract_docs(clusters)
			info = self.format_clusters_into_info(clusters)
			data = {"type":"cluster_info", "uuid":self.uuid, "results":json.dumps(info)}
			self.analysis_solr.update_solr([data]) ## list of dictionaries
		else:
			info = json.loads(hits["response"]["docs"][0]["results"])

		return info


	## Format clusters into dictionary of 5 keys: labels (cluster_id), lengths, counts, span, gaps. values are lists of values. indexes match
	def format_clusters_into_info(self, clusters):
		labels, lengths, counts, gaps, spans = [], [], [], [], []
		random.seed(0)
		random.shuffle(clusters)
		for cluster in clusters:
			labels.append(cluster["cluster_id"])
			lengths.append(cluster["avglength"])
			counts.append(cluster["count"])
			gaps.append(cluster["gap"])
			spans.append(cluster["span"])

		info = {"labels": labels, "lengths": lengths, "counts": counts, "gaps": gaps, "spans": spans}
		return info

	def get_clusters(self, cluster_ids, fl):
		clusters = []
		for i in range(0, len(cluster_ids), self.max_boolean_clauses):
			query = "+cluster_id:({})".format(" OR ".join(cluster_ids[i:i+self.max_boolean_clauses]))
			fq = "+is_hit:0"
			arguments = {"q": query, "fl": fl, "fq": fq}
			response = self.data_solr.query_solr(arguments)
			clusters.append(response)

		return clusters

	def get_cluster_ids(self):
		terms = self.uuid_solr.find_terms(self.uuid)
		terms["fl"] = "cluster_id"
		batches = self.data_solr.query_solr_in_batches(terms, self.batch_size)
		hits = self.extract_docs(batches)
		ids = set()
		for hit in hits:
			ids.add(str(hit["cluster_id"]))

		return list(ids)

	''' Cluster spread methods '''

	def get_cluster_spread_counts(self, start_year, end_year, languages, style, minimum_count):
		arguments = {"q": "+type:cluster_spread +year:[{} TO {}] +language:({})".format(start_year, end_year, " OR ".join(languages)), "rows": 1000}
		hits = self.analysis_solr.query_solr(arguments)
		missing_years = self.get_missing_years(hits, start_year, end_year, languages)
		if len(missing_years) != 0:
			ready_years = self.format_cluster_spread_per_years(hits)
			years_to_add = []
			for missing_year in missing_years:
				year, language = missing_year.split("_")
				years_to_add.append(self.get_year_spread_data(year, language))
			#self.analysis_solr.update_solr(years_to_add)
			new_years = {}
			for year_to_add in years_to_add:
				year, language = year_to_add["year"], year_to_add["language"]
				new_years[year + "_" + language] = json.loads(year_to_add["results"])
			new_years = self.towns_to_lat_lng(new_years)
			toadd = []
			for key, value in new_years.items():
				year, language = key.split("_")
				toadd.append({"type": "cluster_spread", "year": int(year), "language": language, "results": json.dumps(value)})
			self.analysis_solr.update_solr(toadd)
			ready_years.update(new_years)
			#print(ready_years)
			return self.limit_hits(ready_years, style, minimum_count)
		else:
			hits = self.format_cluster_spread_per_years(hits)
			return self.limit_hits(hits, style, minimum_count)

	def format_cluster_spread_per_years(self, hits):
		formatted = {}
		for hit in hits["response"]["docs"]:
			year, language = str(hit["year"]), hit["language"]
			formatted[year + "_" + language] = json.loads(hit["results"])
		return formatted

	def get_missing_years(self, hits, start_year, end_year, languages):
		min_year, max_year = 1771, 1910
		present_years = set()
		missing = set()
		for hit in hits["response"]["docs"]:
			present_years.add(str(hit["year"]) + "_" + hit["language"])
		for i in range(start_year, end_year + 1):
			if i < min_year or i > max_year: continue
			for language in languages:
				if str(i) + "_" + language not in present_years:
					missing.add(str(i) + "_" + language)

		return missing

	def towns_to_lat_lng(self, data):
		lat_lng_dict = self.get_lat_lng_dict()
		rdy = {}
		for year_lng, year_lng_data in data.items():
			rdy[year_lng] = {}
			for linkage_style, linkage_data in year_lng_data.items():
				rdy[year_lng][linkage_style] = {}
				for location, count in linkage_data.items():
						start_town, end_town = location.split("_")
						if start_town == "Unknown" or end_town == "Unknown" or start_town == end_town:
							continue
						rdy[year_lng][linkage_style][location] = {}
				#		rdy[year_lng][linkage_style][location] = [[lat_lng_dict[start_town][0],lat_lng_dict[start_town][1]], [lat_lng_dict[end_town][0], lat_lng_dict[end_town][1]]]
						rdy[year_lng][linkage_style][location]["lat_start"] = lat_lng_dict[start_town][0]
						rdy[year_lng][linkage_style][location]["lng_start"] = lat_lng_dict[start_town][1]
						rdy[year_lng][linkage_style][location]["lat_end"] = lat_lng_dict[end_town][0]
						rdy[year_lng][linkage_style][location]["lng_end"] = lat_lng_dict[end_town][1]
						rdy[year_lng][linkage_style][location]["count"] = count
		return rdy

	def get_lat_lng_dict(self):
		with gzip.open("latlngr.gz", "rt") as gzf:
			data = {}
			for key, value in json.loads(gzf.read()).items():
				data[key] = [value[1], value[0]]
		return data


	def get_hits(self, cluster_ids, fl):
		clusters = {}
		print("HITS", cluster_ids)
		for cluster_id in cluster_ids:
			argument = {"q": "+cluster_id:{}".format(cluster_id), "fq": "+is_hit:1"}
			batches = self.data_solr.query_solr_in_batches(argument, self.batch_size)
			hits = []
			for batch in batches:
				for document in batch["response"]["docs"]:
					hits.append([document["date"], document["location"]])

			hits.sort(key=itemgetter(0))
			clusters[cluster_id] = hits
		return clusters

	def get_year_spread_data(self, year, language):
		arguments = {"q": "+start_year:{} +start_language:{}".format(year, language), "fl": "cluster_id"}
		batches = self.data_solr.query_solr_in_batches(arguments, self.batch_size)
		cluster_ids = [hit["cluster_id"] for batch in batches for hit in batch["response"]["docs"]]
		clusters = self.get_hits(cluster_ids, fl="date, location")
		spreads = {"origin_to_others": defaultdict(int), "other_to_other": defaultdict(int)}
		for cluster_key, cluster_data in clusters.items():
			origin = cluster_data[0][1]
			curr = cluster_data[0][1]
			for hit in cluster_data[1:]:
				spreads["origin_to_others"][origin + "_" + hit[1]] += 1 ## 0 = date, 1 = location
				spreads["other_to_other"][curr + "_" + hit[1]] += 1
				curr = hit[1]

		return {"year": year, "language": language, "results": json.dumps(spreads)}


	def limit_hits(self, hits, style, minimum_count):
		n = {}
		for year, data in hits.items():
			n[year] = {}
			n[year][style] = {}
			for key, value in data[style].items():
				if value["count"] >= minimum_count:
					n[year][style][key] = value
		return n


	''' Single cluster methods '''

	def get_single_cluster_data(self):
		terms = self.uuid_solr.find_terms(self.uuid)
		cluster_id = self.extract_cluster_id(terms)
		if cluster_id == None: return None
		arguments = {"q": "+type:single_cluster_spread +cluster_id:{}".format(cluster_id)}
		hits = self.analysis_solr.query_solr(arguments)
		print(hits)
		if self.analysis_solr.is_empty(hits):
			batches = self.data_solr.query_solr_in_batches({"q": "+cluster_id:{}".format(cluster_id), "fl": "date, location", "fq": "+is_hit:1"}, self.batch_size)
			print(batches)
			hits = []
			for batch in batches:
				for doc in batch["response"]["docs"]:
					hits.append([doc["date"], doc["location"]])
			hits.sort(key=itemgetter(0))
			spread = self.get_single_cluster_spread_data(hits)
			lat_lng_dict = self.get_lat_lng_dict()
			latlng_spread = {}
			for linkage_style, linkage_data in spread.items():
				latlng_spread[linkage_style] = []
				for place in linkage_data:
					start, end = place.split("_")
					start_location = lat_lng_dict[start]
					end_location = lat_lng_dict[end]
					latlng_spread[linkage_style].append({"start_lat": start_location[0], "start_lng": start_location[1], "end_lat": end_location[0], "end_lng": end_location[1], "start_town": start, "end_town": end})
			#self.analysis_solr.update([{"cluster_id": temrs["cluster_id"], "type": "single_cluster_spread", "results": json.dumps(spread)}])
			return latlng_spread
		else:
			return json.loads(hits["response"]["docs"][0]["results"])

	def extract_cluster_id(self, terms):
		if "cluster_id" in terms["fq"]:
			return terms["fq"].split("}")[1]
		else:
			return None

	def get_single_cluster_spread_data(self, hits):
		spread = {"origin_to_others": [], "others_to_others": []}
		origin = hits[0]
		curr = origin
		for hit in hits[1:]:
			spread["origin_to_others"].append("{}_{}".format(origin[1], hit[1]))
			spread["others_to_others"].append("{}_{}".format(curr[1], hit[1]))
			curr = hit
		return spread
