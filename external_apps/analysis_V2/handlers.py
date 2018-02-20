import json, random
from collections import defaultdict
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
        self.available_pages = ["hit_freq", "cluster_info", "cluster_freq", "cluster_freq_data", "cluster_info_data", "hit_freq_data"]
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
            clusters = self.get_clusters(cluster_ids)
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

    def get_clusters(self, cluster_ids):
        clusters = []
        for i in range(0, len(cluster_ids), self.max_boolean_clauses):
            query = "+is_hit:0 +cluster_id:({})".format(" OR ".join(cluster_ids[i:i+self.max_boolean_clauses]))
            arguments = {"q": query, "fl": "cluster_id, gap, span, avglength, count"}
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

    ''' Cluster frequency methods '''

    #def get_cluster_frequency_data(self, cluster_start, cluster_end):
    #    arguments = {"q": "+type:cluster_freq +uuid:{}".format(self.uuid)}
    #    hits = self.analysis_handler.query_solr(arguments)
    #    if self.analysis_handler.is_empty(hits):

    #    else:
    #        cluster_frequencies = json.loads(hits["response"]["docs"][0]["results"])

    #    return cluster_frequencies
