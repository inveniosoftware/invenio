/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package org.invenio_software.solr;

import java.io.IOException;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.search.Query;
import org.apache.solr.common.params.ModifiableSolrParams;
import org.apache.solr.handler.component.QueryComponent;
import org.apache.solr.handler.component.ResponseBuilder;
import org.apache.solr.request.SolrQueryRequest;
import org.apache.solr.search.SolrIndexSearcher;

import org.apache.solr.common.params.SolrParams;
import org.apache.solr.core.SolrResourceLoader;
//import org.apache.solr.request.SolrQueryResponse;
import org.apache.solr.response.SolrQueryResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 *
 * @author jluker
 */
public class InvenioQueryComponent extends QueryComponent {

   public static final Logger log = LoggerFactory.getLogger(SolrResourceLoader.class);

  /**
   * Actually run the query
   */
  @Override
  public void process(ResponseBuilder rb) throws IOException
  {
    SolrQueryRequest req = rb.req;
    SolrQueryResponse rsp = rb.rsp;
    SolrIndexSearcher searcher = req.getSearcher();
    IndexReader reader = searcher.getReader();

    SolrParams params = req.getParams();
    ModifiableSolrParams modParams = new ModifiableSolrParams(params);
    modParams.set("wt", "bitset_stream");
    req.setParams(modParams);

    
//JIdisable as it produces: 
//May 20, 2011 5:48:04 PM org.apache.solr.common.SolrException log
//SEVERE: java.lang.NoSuchFieldError: rsp
//        at org.ads.solr.InvenioQueryComponent.process(InvenioQueryComponent.java:48)
//    log.info("wt: " + req.getParams().get("wt"));

    BitSetFieldCollector bsfc = new BitSetFieldCollector("id");
    bsfc.setResponseFieldName("bitset");
    FieldCollector fc = new FieldCollector(bsfc);

    SolrIndexSearcher.QueryCommand cmd = rb.getQueryCommand();
    Query query = cmd.getQuery();

    searcher.search(query, fc);

    log.info("Adding bitset to response");
    fc.addValuesToResponse(rsp);
   }
}
