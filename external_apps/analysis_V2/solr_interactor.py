import requests, json

class SolrInteractor:

	def __init__(self, core, port, verbose=True):
		self.core = core
		self.port = port
		self.max_rows = 50000
		self.verbose = verbose

	''' Generic solr interaction methods '''

	## Query solr based on arguments
	def query_solr(self, arguments):
		arguments["wt"] = "json" ## Just making sure the data is always in JSON-format
		arguments["hl"] = "false"
		if "rows" not in arguments:
			arguments["rows"] = self.max_rows
		self.log(arguments)
		response = requests.get("http://localhost:{}/solr/{}/select".format(self.port, self.core), data=arguments).text
		try:
			response = json.loads(response)
		except json.decoder.JSONDecodeError:
			print(response)
			raise json.decoder.JSONDecoderError("Couldn't JSONify response.")
		return response

	def log(self, message):
		if self.verbose:
			print(message)

	## Query solr in batches based on arguments.
	def query_solr_in_batches(self, arguments, batch_size):
		arguments["rows"]= batch_size
		current_start = 0
		# if "start" in arguments:
		# 	current_start = arguments["start"]
		batches = []
		while True:
			self.log("Batch start: {}".format(current_start))
			arguments["start"] = current_start
			response = self.query_solr(arguments)
			if self.is_empty(response):
				break
			else:
				batches.append(response)
				current_start += batch_size

		return batches



	## Add 'data' to solr. Data is list of dictionaries
	def update_solr(self, data):
		headers = {"Content-type": "application/json"}
		r = requests.post("http://localhost:{}/solr/{}/update".format(self.port, self.core), json=data, headers=headers)
		r =requests.post("http://localhost:{}/solr/{}/update?commit=true&wt=json".format(self.port, self.core), headers=headers)
		self.log("Updated!")

	## Check if response is empty or invalid
	def is_empty(self, response):
		##TODO check if malformed
		if len(response["response"]["docs"]) == 0:
			return True
		else:
			return False


	## Find query terms based on uuid
	def find_terms(self, uuid):
		arguments = {"q": "query_uuid:{}".format(uuid), "wt": "json"}
		response = self.query_solr(arguments)
		if self.is_empty(response):
			return None
		else:
			return json.loads(response["response"]["docs"][0]["query_terms"])
