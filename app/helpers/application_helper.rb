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

    def generate_to_tsv_link
        args = @document_list[0].solr_response["responseHeader"]["params"]
	found = @document_list[0].solr_response["response"]["numFound"]
	args["rows"] = found
	text = "analysis/to_tsv?"
	args.each do |key, value|
		text.concat("#{key}=#{value}&".gsub('"', ''))
	end
	return "<a href=\"#{text}\">TO TSV </a>".html_safe
     end
end
