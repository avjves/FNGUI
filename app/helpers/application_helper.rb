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
		text = "analysis/to_tsv?"
		analyze = "analysis/?"
		arguments = ""
		args.each do |key, value|
			arguments.concat("#{key}=#{value}&".gsub('"', "%22").gsub(" ", "%20"))
		end
		text.concat(arguments)
		analyze.concat(arguments)
		tsv = "<a class=\"btn btn-sm btn-text\" id=\"startOverLink\" href=\"#{text}\">Query to TSV</a>".html_safe
    		analyze = "<a class=\"btn btn-sm btn-text\" id=\"startOverLink\" href=\"#{analyze}\">Analyze</a>".html_safe
		return tsv + analyze
	else
		return "" 
	end
    end
	
    def make_header
	link = '<a class="nav-brand" href="/fin_news/"><h2>Finnish News</h2></a>'.html_safe
	return link
    end
end
