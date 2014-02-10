/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package org.invenio_software.solr;

import java.util.ArrayList;
import org.apache.lucene.search.Collector;
import org.apache.solr.response.SolrQueryResponse;

/**
 *
 * @author jluker
 */
public abstract class FieldCollectorBase extends Collector {
    public abstract void addValuesToResponse(SolrQueryResponse rsp);
    public abstract String getFieldName();
    public abstract String getResponseFieldName();
    public abstract void setResponseFieldName(String responseFieldName);
}
