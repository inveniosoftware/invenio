/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package org.invenio_software.solr;

import java.io.*;
import org.apache.solr.request.SolrQueryRequest;
import org.apache.solr.response.BinaryResponseWriter;
import org.apache.solr.common.SolrException;
import org.apache.solr.core.SolrCore;

import com.jcraft.jzlib.*;
import org.apache.solr.core.SolrResourceLoader;
import org.apache.solr.response.SolrQueryResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
/**
 *
 * @author jluker
 */
public class InvenioBitsetStreamResponseWriter extends BinaryResponseWriter {

    public static final Logger log = LoggerFactory.getLogger(SolrResourceLoader.class);

    @Override
    public void write(OutputStream out, SolrQueryRequest req, SolrQueryResponse rsp) {

        log.info("In the streaming response writer");

        InvenioBitSet bitset = (InvenioBitSet) rsp.getValues().get("bitset");
        log.info("bitset size: " + bitset.size());

        ZOutputStream zOut = new ZOutputStream(out, JZlib.Z_BEST_SPEED);

        try {
            zOut.write(bitset.toByteArray());
            zOut.flush();
            zOut.close();
        }
        catch (IOException e) {
            SolrException.logOnce(SolrCore.log, "Exception during compression/output of bitset", e);
        }
    }
}
