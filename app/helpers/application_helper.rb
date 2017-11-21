module ApplicationHelper

    def url_to_link args
        raw('<a href="' + args[:document][args[:field]] + '">' + args[:document][args[:field]] + '</a>')
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
        b64 = args.to_json.hash.to_s
        if File.file?("/Solr/FNGUI/analysis/b64/" + b64) == true
          uuid = File.open("/Solr/FNGUI/analysis/b64/" + b64, "r") { |file| file.read()}
        else
          uuid = SecureRandom.uuid
          File.open("/Solr/FNGUI/analysis/b64/" + b64, "w") { |file| file.write(uuid)}
          File.open("/Solr/FNGUI/analysis/uuids/" + uuid, "w") { |file| file.write(args.to_json)}
        end
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
