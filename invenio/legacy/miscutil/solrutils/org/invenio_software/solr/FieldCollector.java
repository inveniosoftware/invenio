/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package org.invenio_software.solr;

import java.util.*;
import java.io.IOException;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.search.Collector;
import org.apache.lucene.search.FieldCache;
import org.apache.lucene.search.Scorer;
import org.apache.solr.client.solrj.SolrResponse;
import org.apache.solr.common.SolrException;
import org.apache.solr.core.SolrCore;
import org.apache.solr.core.SolrResourceLoader;
import org.apache.solr.response.SolrQueryResponse;
import org.apache.solr.schema.FieldType;
import org.apache.solr.schema.IndexSchema;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
/**
 *
 * @author jluker
 */
public class FieldCollector extends FieldCollectorBase {

	public static final Logger log = LoggerFactory.getLogger(SolrResourceLoader.class);

    private Scorer scorer;
    private IndexReader reader;
    private int docBase;
    private Set<String> returnFields;
    private ArrayList<FieldCollectorBase> collectors;

    public FieldCollector(IndexSchema schema, Set<String> returnFields) {
        this.returnFields = returnFields;
        this.collectors = new ArrayList<FieldCollectorBase>();

        for (String f : returnFields) {
            FieldType ftype = schema.getFieldType(f);
            log.info("field type: " + ftype.getTypeName());
            if (ftype.getTypeName().equals("string")) {
                this.collectors.add(new StringFieldCollector(f));
            } else if (ftype.getTypeName().equals("int")) {
                this.collectors.add(new IntFieldCollector(f));
            }
        }
    }

    public FieldCollector(IndexSchema schema, String field) {
        this(schema, new HashSet<String>(Arrays.asList(field)));
    }

    public FieldCollector(FieldCollectorBase fc) {
        this.returnFields = new HashSet<String>();
        this.returnFields.add(fc.getFieldName());
        this.collectors = new ArrayList<FieldCollectorBase>();
        this.collectors.add(fc);
    }

    @Override
    public void setNextReader(IndexReader reader, int docBase) throws IOException {
        for (Collector c : this.collectors) {
            c.setNextReader(reader, docBase);
        }
    }

    public void addValuesToResponse(SolrQueryResponse rsp) {
        for (FieldCollectorBase c : this.collectors) {
            log.info("adding values from " + c.getResponseFieldName() + " collector");
            c.addValuesToResponse(rsp);
        }
    }

    @Override
    public void setScorer(Scorer scorer) throws IOException {
        for (Collector c : this.collectors) {
            c.setScorer(scorer);
        }
    }

    @Override
    public void collect(int doc) throws IOException {
        for (Collector c : this.collectors) {
            c.collect(doc);
        }
    }


    @Override
    public boolean acceptsDocsOutOfOrder() {
        return true;
    }

    @Override
    public String getFieldName() {
        throw new UnsupportedOperationException("Not supported yet.");
    }

    @Override
    public String getResponseFieldName() {
        throw new UnsupportedOperationException("Not supported yet.");
    }

    @Override
    public void setResponseFieldName(String responseFieldName) {
        throw new UnsupportedOperationException("Not supported yet.");
    }
}
