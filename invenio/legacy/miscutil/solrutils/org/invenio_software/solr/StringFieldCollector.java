/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package org.invenio_software.solr;

import java.io.IOException;
import java.util.ArrayList;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.search.Collector;
import org.apache.lucene.search.FieldCache;
import org.apache.lucene.search.Scorer;
import org.apache.solr.common.SolrException;
import org.apache.solr.core.SolrCore;
import org.apache.solr.response.SolrQueryResponse;

/**
 *
 * @author jluker
 */
public class StringFieldCollector extends FieldCollectorBase {

    private Scorer scorer;
    private IndexReader reader;
    private int docBase;
    private String fieldName;
    private String responseFieldName;

    private ArrayList<String> values;
    private String[] valueMap;

    public StringFieldCollector(String fieldName) {
        this.fieldName = fieldName;
        this.values = new ArrayList<String>();
    }

    @Override
    public void setScorer(Scorer scorer) throws IOException {
        this.scorer = scorer;
    }

    @Override
    public void collect(int doc) throws IOException {
        this.values.add(this.valueMap[doc]);
    }

    @Override
    public void setNextReader(IndexReader reader, int docBase) throws IOException {
		this.reader = reader;
		this.docBase = docBase;
        try {
            this.valueMap = FieldCache.DEFAULT.getStrings(reader, this.fieldName);
		}
		catch (IOException e) {
			SolrException.logOnce(SolrCore.log, "Exception during idMap init", e);
		}
    }

    @Override
    public boolean acceptsDocsOutOfOrder() {
        return true;
    }

    @Override
    public void addValuesToResponse(SolrQueryResponse rsp) {
        rsp.add(this.getResponseFieldName(), this.values);
    }

    @Override
    public String getFieldName() {
        return this.fieldName;
    }

    @Override
    public String getResponseFieldName() {
        if (this.responseFieldName == null) {
            return this.fieldName;
        } else {
            return this.responseFieldName;
        }
    }

    @Override
    public void setResponseFieldName(String responseFieldName) {
        this.responseFieldName = responseFieldName;
    }
}
