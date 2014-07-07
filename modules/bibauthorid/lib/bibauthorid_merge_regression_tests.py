from invenio.bibauthorid_logutils import Logger
from invenio.bibauthorid_dbinterface import add_signature
from invenio.bibauthorid_dbinterface import remove_signatures
from invenio.bibauthorid_dbinterface import get_free_author_id
from invenio.bibauthorid_testutils import get_last_recid
from invenio.bibauthorid_testutils import get_last_bibref_value
from invenio.bibauthorid_testutils import claim_test_paper
from invenio.bibauthorid_testutils import reject_test_paper

from invenio.testutils import InvenioTestCase, make_test_suite, run_test_suite

from invenio.bibauthorid_merge import merge_dynamic
from invenio.bibauthorid_merge import merge_static
from invenio.bibauthorid_merge import merge_static_classy

from invenio.dbquery import run_sql

from mock import patch


class BibauthoridBaseMergerTestCase(InvenioTestCase):
    
    def setUp(self):
        self.verbose = 0
        self.logger = Logger(self.__class__.__name__)  # TODO check
        self.logger.log("Setting up regression tests...")

        self.first_author_name = "Testsurname, Firstperson"
        self.second_author_name = "Testsurname, Secondperson"
        
        self.cluster = self.first_author_name.split(',')[0].lower()
       
        self.sigs = list()
        self.author_id_one = get_free_author_id()
        self.author_id_two = self.author_id_one + 1
        
        self.query = """insert into aidRESULTS
        (personid, bibref_table, bibref_value, bibrec)
        values (%s, %s, %s, %s)"""
        
        self.merge_func_to_use = merge_dynamic # TOD abstract in main
        
        
    def merge_func(self):
        
        @patch('invenio.bibauthorid_merge.get_cluster_names') 
        def mocked_merge(mocked_func):
            mocked_func.return_value = self.get_test_cluster_names()
            self.merge_func_to_use()
            
        mocked_merge()
        
    def get_test_cluster_names(self):
        '''
        Mock function replacing get_cluster_names. We only need our test names.
        '''
        return set(run_sql("""select personid
            from aidRESULTS where personid like '%s%%'""" % self.cluster))
            
    def assertMergeResults(self, recs_one, recs_two, non_deterministic=False):
        author_one_res = run_sql("select bibrec from aidPERSONIDPAPERS where personid = %s",
        (self.author_id_one,))
        author_one_res = set([rec[0] for rec in author_one_res])

        author_two_res = run_sql("select bibrec from aidPERSONIDPAPERS where personid = %s",
                (self.author_id_two,))
        author_two_res = set([rec[0] for rec in author_two_res])        

        try:
            self.assertEquals(author_one_res, recs_one)
        except AssertionError,  e:
            if non_deterministic:
                self.assertEquals(author_two_res, recs_one)
                self.assertEquals(author_one_res, recs_two)
            else:
                raise e
        else:
            self.assertEquals(author_two_res, recs_two)
        
        
    def tearDown(self):
        '''
        We clean up everything from aidPERSONIDPAPERS and aidRESULTS.
        '''
        remove_signatures(self.sigs)  # Clean aidPERSONIDPAPERS
        run_sql("DELETE from aidRESULTS where personid like '%s%%' " % self.cluster)


class BibauthoridSymetricMergerTestCase(BibauthoridBaseMergerTestCase):
    '''
    The base test case for Merger regression tests.
    '''

    def setUp(self):
        '''
        We create ten records for two authors of the same surname (cluster).
        Then we create an artificial result that may as well have been created by tortoise.
        '''
        super(BibauthoridSymetricMergerTestCase, self).setUp()
        for i in range(0,10):           
            last_bibref = get_last_bibref_value()
            last_recid = get_last_recid()
            
            sig = ["100", last_bibref +1, last_recid + 1]
            if i < 5: # The first 3 papers to the first author.
                add_signature(sig, self.first_author_name, self.author_id_one)
            else: # The other 7 to the second author.
                add_signature(sig, self.second_author_name, self.author_id_two)
                
            self.sigs.append(sig)
                        
                        
    def test_merge_nothing_case(self):
        '''
        Nothing should happen.
        '''
        for i in range(0,10):  
            if i < 5:  # Assign the last signature to the first person.
                run_sql(self.query, (self.cluster + ".1", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))
            else:
                run_sql(self.query, (self.cluster + ".2", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))
                                
        self.merge_func() 
        first_author_sigs = self.sigs[0:5]
        recs_one = set([sig[2] for sig in first_author_sigs])
        
        second_author_sigs = self.sigs[5:10]
        recs_two = set([sig[2] for sig in second_author_sigs])
        
        self.assertMergeResults(recs_one, recs_two, non_deterministic=True)
        

    def test_inside_case(self):
                
        for i in range(0,10):  
            if i < 3 or i > 7:  # Assign the last signature to the first person.
                run_sql(self.query, (self.cluster + ".1", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))
            else:
                run_sql(self.query, (self.cluster + ".2", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))
                
        self.merge_func()  # Running! TODO Abstract this away!.
        
        first_author_sigs = self.sigs[0:3]
        first_author_sigs.append(self.sigs[-1])
        first_author_sigs.append(self.sigs[-2])
        
        
        recs_one = set([sig[2] for sig in first_author_sigs])
    
        second_author_sigs = self.sigs[3:8]
        recs_two = set([sig[2] for sig in second_author_sigs])
        
        self.assertMergeResults(recs_one, recs_two)
        
    
    def test_all_case(self):
        '''
        Non deterministic test!
        '''
        for i in range(0,10):  
            run_sql(self.query, (self.cluster + ".1", self.sigs[i][0],
                            self.sigs[i][1], self.sigs[i][2]))
                
        self.merge_func()  # Running! TODO Abstract this away!.
        
        first_author_sigs = self.sigs[0:10]
        recs_one = set([sig[2] for sig in first_author_sigs])
    
        recs_two = set()
        
        self.assertMergeResults(recs_one, recs_two, non_deterministic=True)
        
    def test_merge_most_case(self):
                
        for i in range(0,10):  
            if i < 7:  # Assign the last signature to the first person.
                run_sql(self.query, (self.cluster + ".1", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))
            else:
                run_sql(self.query, (self.cluster + ".2", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))
                
        self.merge_func()
        
        first_author_sigs = self.sigs[0:7]
        recs_one = set([sig[2] for sig in first_author_sigs])
    
        second_author_sigs = self.sigs[7:10]
        recs_two = set([sig[2] for sig in second_author_sigs])
                
        self.assertMergeResults(recs_one, recs_two)
        
    def test_merge_subset_case(self):
                
        for i in range(0,10):  
            if i < 3:  # Assign the last signature to the first person.
                run_sql(self.query, (self.cluster + ".1", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))
            elif i > 7:
                run_sql(self.query, (self.cluster + ".2", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))
                
        self.merge_func() 
        
        first_author_sigs = self.sigs[0:5]
        recs_one = set([sig[2] for sig in first_author_sigs])
    
        second_author_sigs = self.sigs[5:10]
        recs_two = set([sig[2] for sig in second_author_sigs])
                
        self.assertMergeResults(recs_one, recs_two)    


    def test_merge_subset_new_recs_case(self):
                
        for i in range(0,10):  
            if i < 3:  # Assign the last signature to the first person.
                run_sql(self.query, (self.cluster + ".1", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))
            elif i > 7:
                run_sql(self.query, (self.cluster + ".2", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))
                                
        # Two extra records one per author!

        last_bibref = get_last_bibref_value()
        last_recid = get_last_recid()
        
        sig = ["100", last_bibref +1, last_recid + 1]
        
        run_sql(self.query, (self.cluster + ".1", "100", last_bibref +1,
                             last_recid + 1))
        run_sql(self.query, (self.cluster + ".2", "100", last_bibref +2,
                             last_recid + 2))
                
        self.merge_func()
        
        first_author_sigs = self.sigs[0:5]
        recs_one = set([sig[2] for sig in first_author_sigs])
    
        second_author_sigs = self.sigs[5:10]
        recs_two = set([sig[2] for sig in second_author_sigs])
                
        self.assertMergeResults(recs_one, recs_two)
        
    def test_merge_swap_case(self):
                
        for i in range(0,10):  
            if i < 4 or i > 8:  # Assign the last signature to the first person.
                run_sql(self.query, (self.cluster + ".1", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))
            else:
                run_sql(self.query, (self.cluster + ".2", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))
                
        self.merge_func()
        
        first_author_sigs = self.sigs[0:4]
        first_author_sigs.append(self.sigs[-1])
        recs_one = set([sig[2] for sig in first_author_sigs])
    
        second_author_sigs = self.sigs[4:9]
        recs_two = set([sig[2] for sig in second_author_sigs])
                
        self.assertMergeResults(recs_one, recs_two)
        

    def test_merge_claim_amphi_case(self):

        claim_test_paper(self.sigs[0][2])
        claim_test_paper(self.sigs[9][2])        
        
        for i in range(0,10):  
            run_sql(self.query, (self.cluster + ".1", self.sigs[i][0],
                            self.sigs[i][1], self.sigs[i][2]))
        
        self.merge_func()
        
        first_author_sigs = self.sigs[0:9]
        recs_one = set([sig[2] for sig in first_author_sigs])
    
        recs_two = set([self.sigs[9][2]])
                
        self.assertMergeResults(recs_one, recs_two, non_deterministic=True)

   
class BibauthoridSplitMergerTestCase(BibauthoridBaseMergerTestCase):
     
    def setUp(self):
        '''
        We create ten records for two authors of the same surname (cluster).
        Then we create an artificial result that may as well have been created by tortoise.
        '''
        super(BibauthoridSplitMergerTestCase, self).setUp()
        for i in range(0,10):           
            last_bibref = get_last_bibref_value()
            last_recid = get_last_recid()
            
            sig = ["100", last_bibref +1, last_recid + 1]
            add_signature(sig, self.first_author_name, self.author_id_one)
            self.sigs.append(sig)

        for i in range(0,10):  
            if i < 5:
                run_sql(self.query, (self.cluster + ".1", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))
            else:
                run_sql(self.query, (self.cluster + ".2", self.sigs[i][0],
                                self.sigs[i][1], self.sigs[i][2]))            
                    
    def test_basic_case_split(self):
        self.merge_func()
        
        first_author_sigs = self.sigs[0:5]
        recs_one = set([sig[2] for sig in first_author_sigs])
    
        second_author_sigs = self.sigs[5:10]
        recs_two = set([sig[2] for sig in second_author_sigs])               
        self.assertMergeResults(recs_one, recs_two)
        
    def test_claim_split(self):
        
        claim_test_paper(self.sigs[0][2])
        claim_test_paper(self.sigs[9][2])
        
        self.merge_func()
        
        first_author_sigs = self.sigs[0:5]
        first_author_sigs.append(self.sigs[-1])
        recs_one = set([sig[2] for sig in first_author_sigs])
    
        second_author_sigs = self.sigs[5:9]
        recs_two = set([sig[2] for sig in second_author_sigs])               
        self.assertMergeResults(recs_one, recs_two, non_deterministic=True)

class BibauthoridAsymetricRejectMergerTestCase(BibauthoridBaseMergerTestCase):
    '''
    Nothing fancy. We just require a different setup for this case.
    '''
    
    def setUp(self):
        super(BibauthoridAsymetricRejectMergerTestCase, self).setUp()
        for i in range(0,10):

            last_bibref = get_last_bibref_value()
            last_recid = get_last_recid()

            sig = ["100", last_bibref +1, last_recid + 1]  
            if i == 0:          
                add_signature(sig, self.second_author_name, self.author_id_two)
                add_signature(sig, self.first_author_name, self.author_id_one)
                run_sql("update aidPERSONIDPAPERS set flag=-2 where bibrec = %s and personid= %s", (sig[2], self.author_id_one))
            elif i == 1:
                add_signature(sig, self.second_author_name, self.author_id_two)
            else:
                add_signature(sig, self.first_author_name, self.author_id_one)
            self.sigs.append(sig)
        
                
    def test_merge_rejected(self):
        
        for i in range(0,10):  
            run_sql(self.query, (self.cluster + ".1", self.sigs[i][0],
                    self.sigs[i][1], self.sigs[i][2]))
                    
        self.merge_func()
        
        first_author_sigs = self.sigs[0:10]
        recs_one = set([sig[2] for sig in first_author_sigs])
        
        recs_two = set([self.sigs[0][2]])
        self.assertMergeResults(recs_one, recs_two)
        
        flag_rejected = run_sql("select flag from aidPERSONIDPAPERS where personid = %s" % (self.author_id_one,))[0][0]
        flag_assigned = run_sql("select flag from aidPERSONIDPAPERS where personid = %s" % (self.author_id_two,))[0][0]

        self.assertEquals(flag_rejected, -2)
        self.assertEquals(flag_assigned, 0)
                    
     
class BibauthoridBibrefMergerTestCase(BibauthoridBaseMergerTestCase):
    
    
    def setUp(self):
        super(BibauthoridBibrefMergerTestCase, self).setUp()
        last_bibref = get_last_bibref_value()
        last_recid = get_last_recid()
        
        # Record 1
        rec_1 = last_recid + 1
        sig = ["100", last_bibref + 1, rec_1]
        self.sigs.append(sig)
        add_signature(sig, self.first_author_name, self.author_id_one)
        sig = ["100", last_bibref + 2, rec_1]
        self.sigs.append(sig)
        add_signature(sig, self.first_author_name, self.author_id_one)

        sig = ["100", last_bibref + 3, rec_1]
        self.sigs.append(sig)       

        rec_2 = rec_1 + 1
        sig = ["100", last_bibref + 3, rec_2]
        self.sigs.append(sig)
        add_signature(sig, self.second_author_name, self.author_id_two)
        
    def test_basic_bibref_merge(self):
        run_sql(self.query ,( self.cluster + ".1" , self.sigs[0][0],
                self.sigs[0][1], self.sigs[0][2]))
        run_sql(self.query , ( self.cluster + ".1" , self.sigs[2][0],
                self.sigs[2][1], self.sigs[2][2]))
        run_sql(self.query , (self.cluster + ".2" , self.sigs[2][0],
                self.sigs[2][1], self.sigs[2][2]))

        self.merge_func()
        
        first_author_sigs = self.sigs[0:2]
        recs_one = set([sig[2] for sig in first_author_sigs])
        
        recs_two = set([self.sigs[3][2]])
        self.assertMergeResults(recs_one, recs_two)
        
        
TEST_SUITE = make_test_suite(BibauthoridBaseMergerTestCase,
                             BibauthoridSymetricMergerTestCase,
                             BibauthoridSplitMergerTestCase,
                             BibauthoridAsymetricRejectMergerTestCase,
                             BibauthoridBibrefMergerTestCase)
       
if __name__ == "__main__":
    run_test_suite(TEST_SUITE)