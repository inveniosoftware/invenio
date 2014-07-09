/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package org.invenio_software.solr;

import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import org.apache.solr.common.params.SolrParams;
import org.apache.solr.handler.component.ResponseBuilder;
import org.apache.solr.handler.component.QueryComponent;
import org.apache.solr.request.SolrQueryRequest; 
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.search.*;
import org.apache.solr.common.SolrException;
import org.apache.solr.common.params.CommonParams;
import org.apache.solr.core.SolrCore;
import org.apache.solr.search.BitDocSet;
import org.apache.solr.search.SolrCache;
import org.apache.solr.search.SolrIndexSearcher;
import org.apache.solr.common.util.ContentStream;
import com.jcraft.jzlib.*;
import java.io.ByteArrayOutputStream;
import org.apache.commons.io.IOUtils;
// JI. deprecated:import org.apache.solr.request.SolrQueryResponse;
import org.apache.solr.response.SolrQueryResponse;

/**
 *
 * @author jluker
 */
public class InvenioFacetComponent extends QueryComponent {

    private HashMap<Integer, Integer> getIdMap(SolrIndexSearcher searcher) {

        Logger log = LoggerFactory.getLogger(QueryComponent.class);
        IndexReader reader = searcher.getReader();

        int cacheKey = reader.hashCode();
        log.info("Using cacheKey: " + cacheKey);

        SolrCache docIdMapCache = searcher.getCache("InvenioDocIdMapCache");
        if (docIdMapCache == null) {
            log.error("Can't access InvenioDocIdMapCache. Did you configure it?");
        }

        // this line generates warnings - it seems to be artifact of using generics
        HashMap<Integer, Integer> idMap = (HashMap<Integer, Integer>)docIdMapCache.get(cacheKey);

        if (idMap == null) {
            log.info("idMap not found in cache; generating");
            idMap = new HashMap<Integer, Integer>();
            try {
                int[] ids = FieldCache.DEFAULT.getInts(reader, "id");
                log.info("ids length: " + ids.length);
                for (int i = 0; i < ids.length; i++) {
                    idMap.put(ids[i], i);
                }
            } catch (IOException e) {
                SolrException.logOnce(SolrCore.log, "Exception during idMap init", e);
            }
            docIdMapCache.put(cacheKey, idMap);
        } else {
            log.info("idMap retrieved from cache");
        }
        log.info("idMap done. size: " + idMap.size());
        return idMap;
    }

    @Override
    public void process(ResponseBuilder rb) throws IOException {

        Logger log = LoggerFactory.getLogger(QueryComponent.class);
        log.info(COMPONENT_NAME);

        SolrQueryRequest req = rb.req;
        SolrQueryResponse rsp = rb.rsp;
        SolrParams params = req.getParams();
        Iterable<ContentStream> streams = req.getContentStreams();

        if (streams == null) {
            throw new IOException("No streams found!");
        }

        SolrIndexSearcher searcher = req.getSearcher();
        HashMap<Integer, Integer> idMap = getIdMap(searcher);
        InvenioBitSet bitset = null;
        BitDocSet docSetFilter = new BitDocSet();

        for (ContentStream stream : streams) {
            log.info("Got stream: " + stream.getName() +
                ", Content type: " + stream.getContentType() +
                ", stream info: " + stream.getSourceInfo());

            if (stream.getName().equals("bitset")) {

                // use zlib to read in the data
                InputStream is = stream.getStream();
                ByteArrayOutputStream bOut = new ByteArrayOutputStream();
                ZInputStream zIn = new ZInputStream(is);

                int bytesCopied = IOUtils.copy(zIn, bOut);
                log.info("bytes copied: " + bytesCopied);

                byte[] bitset_bytes = bOut.toByteArray();
                bitset = new InvenioBitSet(bitset_bytes);

                int i = 0;
                while (bitset.nextSetBit(i) != -1) {
                    int nextBit = bitset.nextSetBit(i);
                    int lucene_id = idMap.get(nextBit);
                    docSetFilter.add(lucene_id);
                    i = nextBit + 1;
                }
                log.info("docSetFilter size: " + docSetFilter.size());
            }
        }

        long timeAllowed = (long)params.getInt( CommonParams.TIME_ALLOWED, -1 );
        SolrIndexSearcher.QueryCommand cmd = rb.getQueryCommand();

        // use our set of doc ids as a filter
        cmd.setFilter(docSetFilter);
        cmd.setTimeAllowed(timeAllowed);

        SolrIndexSearcher.QueryResult result = new SolrIndexSearcher.QueryResult();
        searcher.search(result,cmd);
        rb.setResult( result );

        rsp.add("response",rb.getResults().docList);
        rsp.getToLog().add("hits", rb.getResults().docList.matches());

//        doFieldSortValues(rb, searcher);
//        doPrefetch(rb);
    }
}
