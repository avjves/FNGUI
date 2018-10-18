
module ApplicationHelper

		def not_facet
				if request.original_url.include? "catalog"
					return false
				else
					return true
				end
		end


	## This currently also fixes the URL if it's a hit from the 1911-1920 set. If this is ever changed, remember to fix this method.
    def url_to_link args
        query_words = extract_query_words(args)
        url = args[:document][args[:field]]
	url = fix_url_page_nmbr(url, args)
        for item in query_words
          url = url + "&term=" + item
        end
        return raw('<a target="_blank" href="' + url + '">' + url + '</a>')
    end

    def fix_url_page_nmbr (url, args)
	fn = args[:document]._source["filename"]
	if fn.end_with? ".txt"
	    pagen = fn.split(".txt")[0].split("_")[-1]
	    url = url.split("?page=")[0] + "?page=" + pagen
	    return url
	else
	    return url
	end
    end

    def round_viral args
        viral_score = args[:document][args[:field]]
	return (viral_score*100).round / 100.0
    end

    def extract_query_words args
        doc_id = args[:document]._source["id"]
        hl = args[:document].solr_response["highlighting"][doc_id]["text"][0]
        splits = hl.split("<em>")
        splits.shift
        words = []
        for item in splits
          w = item.split("</em>")[0]
          w = w.gsub(/[^0-9a-z]/i, '')
          words.push(w)
        end
        return words
    end

    def first_text_to_none args
        if args[:document].solr_response["responseHeader"]["params"]["fq"].include? "{!term f=cluster_id}"
            "-"
        else
            args[:document][args[:field]]
        end
    end

    def text_clean args
        args[:document][args[:field]].gsub!('<', ' ')
    end

    ## Wow, great stuff here
    ## TODO make sure json is in same order to get same hash :)
    def generate_links
        if @document_list[0] != nil
            	args = @document_list[0].solr_response["responseHeader"]["params"]
    		if @search_state.params["page"] != nil
    			page = Integer(@search_state.params["page"])
    		else
    			page = 1
    		end
    		if @search_state.params["per_page"] != nil
    			per_page = Integer(@search_state.params["per_page"])
    		else
    			per_page = 10
    		end
    		args["start"] = (page-1) * per_page
    		args["wt"] = "json"
        require 'securerandom'
        require 'json'
        require "cgi"
				require 'open-uri'
        query_terms = args.to_json
        query_hash = query_terms.hash.to_s
        query_terms = CGI.escape(query_terms.to_s)
				response = open("http://127.0.0.1:12345/get_uuid?query_hash=" + query_hash + "&query_terms=" + query_terms).read
        uuid = response

        text = "analysis/to_tsv?uuid=" + uuid
    		analyze = "analysis/?uuid=" + uuid

    		tsv = "<a class=\"btn btn-sm btn-text\" id=\"TSVLink\" href=\"#{text}\">Query to TSV</a>".html_safe
        		analyze = "<a class=\"btn btn-sm btn-text\" id=\"AnalyzeLink\" href=\"#{analyze}\">Analyze</a>".html_safe
    		return tsv + analyze
    	else
    		return ""
    	end
    end

    def make_header
	link = '<a class="nav-brand" href="/clusters/"><h2>Finnish News</h2></a>'.html_safe
	return link
    end
end
