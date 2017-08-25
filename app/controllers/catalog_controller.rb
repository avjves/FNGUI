# frozen_string_literal: true
class CatalogController < ApplicationController

  include BlacklightRangeLimit::ControllerOverride

  include Blacklight::Catalog

  configure_blacklight do |config|
    ## Class for sending and receiving requests from a search index
    # config.repository_class = Blacklight::Solr::Repository
    #
    ## Class for converting Blacklight's url parameters to into request parameters for the search index
    # config.search_builder_class = ::SearchBuilder
    #
    ## Model that maps search index responses to the blacklight response model
    # config.response_model = Blacklight::Solr::Response

    ## Default parameters to send to solr for all search-like requests. See also SearchBuilder#processed_parameters
    config.default_solr_params = {
      :"rows" => "10",
      #:"hl.fl" => "text",
      :"f.text.hl.alternateField" => "text",
      :"hl.simple.pre" => '',
      :"hl.simple.post" => '',
      :"hl"=> true,
      :"hl.fragsize" => "0",
      :"fl" => "*"
    }

    # solr path which will be added to solr base url before the other solr params.
    #config.solr_path = 'select'

    # items to show per page, each number in the array represent another option to choose from.
    #config.per_page = [10,20,50,100]

    ## Default parameters to send on single-document requests to Solr. These settings are the Blackligt defaults (see SearchHelper#solr_doc_params) or
    ## parameters included in the Blacklight-jetty document requestHandler.
    #
    #config.default_document_solr_params = {
    #  qt: 'document',
    #  ## These are hard-coded in the blacklight 'document' requestHandler
    #  # fl: '*',
    #  # rows: 1,
    #  # q: '{!term f=id v=$id}'
    #}

    # solr field configuration for search results/index views
    config.index.title_field = 'id'
    config.index.display_type_field = 'format'
    #config.index.thumbnail_field = 'thumbnail_path_ss'

    # solr field configuration for document/show views
    #config.show.title_field = 'title_display'
    #config.show.display_type_field = 'format'
    #config.show.thumbnail_field = 'thumbnail_path_ss'

    # solr fields that will be treated as facets by the blacklight application
    #   The ordering of the field names is the order of the display
    #
    # Setting a limit will trigger Blacklight's 'more' facet values link.
    # * If left unset, then all facet values returned by solr will be displayed.
    # * If set to an integer, then "f.somefield.facet.limit" will be added to
    # solr request, with actual solr request being +1 your configured limit --
    # you configure the number of items you actually want _displayed_ in a page.
    # * If set to 'true', then no additional parameters will be sent to solr,
    # but any 'sniffed' request limit parameters will be used for paging, with
    # paging at requested limit -1. Can sniff from facet.limit or
    # f.specific_field.facet.limit solr request params. This 'true' config
    # can be used if you set limits in :default_solr_params, or as defaults
    # on the solr side in the request handler itself. Request handler defaults
    # sniffing requires solr requests to be made with "echoParams=all", for
    # app code to actually have it echo'd back to see it.
    #
    # :show may be set to false if you don't want the facet to be drawn in the
    # facet bar
    #
    # set :index_range to true if you want the facet pagination view to have facet prefix-based navigation
    #  (useful when user clicks "more" on a large facet and wants to navigate alphabetically across a large set of results)
    # :index_range can be an array or range of prefixes that will be used to create the navigation (note: It is case sensitive when searching values)

    config.add_facet_field 'title', label: 'Title', limit: 10
    config.add_facet_field 'year', label: "Publication year", :range => {
	    :maxlength => 4,
	    :assumed_boundaries => [1775, 1910],
	    :segments => true
	    }
	config.add_facet_field 'occyear', label: "First occurance", :range => {
	   :maxlength => 4,
	    :assumed_boundaries => [1775, 1910],
	    :segments => true
	    }
    config.add_facet_field 'language', label: "Language"
    config.add_facet_field 'location', label: "Location", limit:15
    config.add_facet_field 'start_location', label: "Start location", limit: 15
    config.add_facet_field 'start_language', label: "Start language"

    #config.add_facet_field 'occyear', label: "First occurance"

    #config.add_facet_field 'year', label: "Publication year"

    # Have BL send all facet field names to Solr, which has been the default
    # previously. Simply remove these lines if you'd rather use Solr request
    # handler defaults, or have no facets.
    config.add_facet_fields_to_solr_request!

    # solr fields to be displayed in the index (search results) view
    #   The ordering of the field names is the order of the display

    config.add_index_field 'count', label: "Count"
    config.add_index_field 'occyear', label: "Occurance year"
    config.add_index_field 'avglength', label: "Average length"
    config.add_index_field "max_reprint_time", label: "Max gap (yrs)"
    config.add_index_field 'span', label: "Maximum span (yrs)"
    config.add_index_field 'filename', label: "Filename"
    config.add_index_field 'date', label: "Date"
    config.add_index_field 'year', label: "Year"
    config.add_index_field 'location', label: "Location"
    config.add_index_field 'language', label: "Language"
    config.add_index_field 'cluster_id', label: "Cluster ID", link_to_search: true
    config.add_index_field 'title', label: "Title"
    config.add_index_field 'url', label: "URL", :helper_method => :url_to_link
    config.add_index_field 'text', label: "Text", :highlight => true
    config.add_index_field 'start_location', label: "Start location"
    config.add_index_field 'start_language', label: "Start language"
    config.add_index_field 'first_text', label: "First hit", :helper_method => :first_text_to_none



    config.add_show_field 'filename', label: "Filename"
    config.add_show_field 'date', label: "Date"
    config.add_show_field 'year', label: "Year"
    config.add_show_field 'cluster_id', label: "Cluster ID", link_to_search: true
    config.add_show_field 'title', label: "Title"
    config.add_show_field 'url', label: "URL"
    config.add_show_field 'text', label: "Text"


    config.add_field_configuration_to_solr_request!

    # "fielded" search configuration. Used by pulldown among other places.
    # For supported keys in hash, see rdoc for Blacklight::SearchFields
    #
    # Search fields will inherit the :qt solr request handler from
    # config[:default_solr_parameters], OR can specify a different one
    # with a :qt key/value. Below examples inherit, except for subject
    # that specifies the same :qt as default for our own internal
    # testing purposes.
    #
    # The :key is what will be used to identify this BL search field internally,
    # as well as in URLs -- so changing it after deployment may break bookmarked
    # urls.  A display label will be automatically calculated from the :key,
    # or can be specified manually to be different.

    # This one uses all the defaults set by the solr request handler. Which
    # solr request handler? The one set in config[:default_solr_parameters][:qt],
    # since we aren't specifying it otherwise.


    # Now we see how to over-ride Solr request handler defaults, in this
    # case for a BL "search field", which is really a dismax aggregate
    # of Solr search fields.


    config.add_search_field("Hits") do |field|
        field.solr_parameters = { :"fq" => "ishit:1" }
    end

    config.add_search_field("Clusters") do |field|
        field.solr_parameters = { :"fq" => "ishit:0", :"fl" => "*" }
    end

   config.add_search_field 'all_fields', label: 'All'

    config.add_search_field("No limits") do |field|
       field.solr_parameters = { :"fl" => "*" }
    end

    # "sort results by" select (pulldown)
    # label in pulldown is followed by the name of the SOLR field to sort by and
    # whether the sort is ascending or descending (it must be asc or desc
    # except in the relevancy case).

    config.add_sort_field 'ishit asc, date desc', label: "Date, descending"
    config.add_sort_field 'ishit asc, date asc', label: "Date ascending"
    config.add_sort_field 'ishit asc, count desc', label: "Count, descending"
    config.add_sort_field 'ishit asc, count asc', label: "Count, ascending"
    config.add_sort_field 'ishit asc, avglength desc', label: "Length, descending"
    config.add_sort_field 'ishit asc, avglength asc', label: "Length, ascending"
    config.add_sort_field 'ishit asc, span desc', label: "Span, descending"
    config.add_sort_field 'ishit asc, span asc', label: "Span, ascending"
    config.add_sort_field 'ishit asc, max_reprint_time desc', label: "Reprint time, descending"
    config.add_sort_field 'ishit asc, max_reprint_time asc', label: "Reprint time, ascending"
    config.add_sort_field 'ishit asc, occyear desc', label: "Occurance year, descending"
    config.add_sort_field 'ishit asc, occyear asc', label: "Occurance year, ascending"
  end
end
