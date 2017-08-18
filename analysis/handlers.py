import requests, json

class TSVHandler:

	def __init__(self, arguments, solr_core):
		self.bad_keys = ["stats", "stats.field", "id", "_version_", "ishit"]
		self.arguments = self.validate_arguments(arguments)
		self.core = solr_core

	def validate_arguments(self,arguments):
		args = {}
		for key, value in arguments.items():
			print(key)
			if key in self.bad_keys: continue
			args[key] = value
		args["wt"] = "json"
		args["rows"] = 1000
		return args

	def query_to_tsv(self):
		data = self.query_solr()
		data = self.data_to_tsv_html_blob(data)
		return data
	
	def query_solr(self):
		result = requests.get("http://localhost:8983/solr/{}/select".format(self.core), data=self.arguments)
		return self.format_result_to_json(result.text)
	
	def format_result_to_json(self, text):
		#print(text)
		text = json.loads(text)
		return text["response"]["docs"]
	

	def get_field_keys(self, document):
		keys = []
		for key in document:
			if key in self.bad_keys: continue
			keys.append(key)
		keys.sort()
		return keys

	def data_to_tsv_html_blob(self, data):
		values = ["<table>"]
		blob = []
		keys = self.get_field_keys(data[0])
		values.append("<tr>")
		for key in keys:
			values.append("<td>{}</td>".format(key))
		values.append("</tr>")
		for document in data:
			values.append("<tr>")
			for key in keys:
				#print(key)
				values.append("<td>")
				values.append(str(document[key]))
				values.append("</td>")
			values.append("</tr>")
		
		values.append("</table>")
		
		return "\n".join(values)
	
