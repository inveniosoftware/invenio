# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
RevisionVerifier : Compares the Revision of Record to be uploaded
with the archived Revision and the latest Revision(if any) and
generates a record patch for modified fields alone. This is to
avoid replacing the whole record where changes are minimal
"""

__revision__ = "$Id$"

import zlib
import copy
from pprint import pformat

from invenio.legacy.bibrecord import record_get_field_value, \
                                record_get_field_instances, \
                                record_add_field, \
                                record_delete_field, \
                                create_record, \
                                records_identical

from invenio.legacy.bibupload.config import CFG_BIBUPLOAD_CONTROLFIELD_TAGS, \
                                     CFG_BIBUPLOAD_DELETE_CODE, \
                                     CFG_BIBUPLOAD_DELETE_VALUE

from invenio.legacy.bibedit.db_layer import get_marcxml_of_record_revision, \
                                    get_record_revisions

class RevisionVerifier:
    """
    Class RevisionVerifier contains methods for Revision comparison
    for the given record.
    """

    def __init__(self):
        self.rec_id = ''

    def group_tag_values_by_indicator(self, tag_value_list):
        """
        Groups the field instances of tag based on indicator pairs

        Returns a dictionary of format {(ind1,ind2):[subfield_tuple1, .., subfield_tuplen]}
        """
        curr_tag_indicator = {}

        for data_tuple in tag_value_list:
            ind1 = data_tuple[1]
            ind2 = data_tuple[2]

            if (ind1, ind2) not in curr_tag_indicator:
                curr_tag_indicator[(ind1, ind2)] = [data_tuple]
            else:
                curr_tag_indicator[(ind1, ind2)].append(data_tuple)

        return curr_tag_indicator

    def compare_tags_by_ind(self, rec1_tag_val, rec2_tag_val):
        """
        Groups the fields(of given tag) based on the indicator pairs

        Returns a tuple of lists,each list denoting common/specific indicators
        """
        # temporary dictionary to hold fields from record2
        tmp = copy.deepcopy(rec2_tag_val)

        common_ind_pair = {}
        ind_pair_in_rec1_tag = {}
        ind_pair_in_rec2_tag = {}

        for ind_pair in rec1_tag_val:
            # if indicator pair is common
            if ind_pair in tmp:
                # copying values from record1 tag as this could help
                # at next stage in case of any subfield level modifications
                # this could be directly used.
                common_ind_pair[ind_pair] = rec1_tag_val[ind_pair]
                del tmp[ind_pair]
            else:
                # indicator pair is present only in current tag field
                ind_pair_in_rec1_tag[ind_pair] = rec1_tag_val[ind_pair]

        for ind_pair in rec2_tag_val:
            # indicator pair present only in record2 tag field
            if ind_pair in tmp:
                ind_pair_in_rec2_tag[ind_pair] = rec2_tag_val[ind_pair]

        return (common_ind_pair, ind_pair_in_rec1_tag, ind_pair_in_rec2_tag)

    def find_modified_tags(self, common_tags, record1, record2):
        """
        For each tag common to Record1 and Record2, checks for modifictions
        at field-level, indicator-level and subfield-level.

        Returns a dictionary of tags and corresponding fields from Record1
        that have been found to have modified.
        """

        result = {}
        for tag in common_tags:
            # retrieve tag instances of record1 and record2
            rec1_tag_val = record_get_field_instances(record1, tag, '%', '%')
            rec2_tag_val = record_get_field_instances(record2, tag, '%', '%')
            if rec1_tag_val:
                rec1_ind = self.group_tag_values_by_indicator(rec1_tag_val)
            if rec2_tag_val:
                rec2_ind = self.group_tag_values_by_indicator(rec2_tag_val)

            # NOTE: At this point rec1_ind and rec2_ind will be dictionary
            # Key ==> (ind1, ind2) tuple
            # Val ==> list of data_tuple => [dt1,dt2]
            # dt(n) => ([sfl],ind1,ind2,ctrlfield,fn)

            # Generating 3 different dictionaries
            # common/added/deleted ind pairs in record1 based on record2
            (com_ind, add_ind, del_ind) = self.compare_tags_by_ind(rec1_ind, rec2_ind)

            if add_ind:
                for ind_pair in add_ind:
                    for data_tuple in add_ind[ind_pair]:
                        subfield_list = data_tuple[0]
                        record_add_field(result, tag, ind_pair[0], ind_pair[1], '', subfields=subfield_list)

            # Indicators that are deleted from record1 w.r.t record2 will be added with special code
            if del_ind:
                for ind_pair in del_ind:
                    record_add_field(result, tag, ind_pair[0], ind_pair[1], '', [(CFG_BIBUPLOAD_DELETE_CODE, CFG_BIBUPLOAD_DELETE_VALUE)])

            # Common modified fields. Identifying changes at subfield level
            if com_ind:
                for ind_pair in com_ind:
                    # NOTE: sf_rec1 and sf_rec2 are list of list of subfields
                    # A simple list comparison is sufficient in this scneario
                    # Any change in the order of fields or changes in subfields
                    # will cause the entire list of data_tuple for that ind_pair
                    # to be copied from record1(upload) to result.
                    if tag in CFG_BIBUPLOAD_CONTROLFIELD_TAGS:
                        cf_rec1 = [data_tuple[3] for data_tuple in rec1_ind[ind_pair]]
                        cf_rec2 = [data_tuple[3] for data_tuple in rec2_ind[ind_pair]]
                        if cf_rec1 != cf_rec2:
                            for data_tuple in com_ind[ind_pair]:
                                record_add_field(result, tag, controlfield_value=data_tuple[3])
                    else:
                        sf_rec1 = [data_tuple[0] for data_tuple in rec1_ind[ind_pair]]
                        sf_rec2 = [data_tuple[0] for data_tuple in rec2_ind[ind_pair]]
                        if sf_rec1 != sf_rec2:
                            # change at subfield level/ re-oredered fields
                            for data_tuple in com_ind[ind_pair]:
                                # com_ind will have data_tuples of record1(upload) and not record2
                                subfield_list = data_tuple[0]
                                record_add_field(result, tag, ind_pair[0], ind_pair[1], '', subfields=subfield_list)

        return result

    def compare_records(self, record1, record2, opt_mode=None):
        """
        Compares two records to identify added/modified/deleted tags.

        The records are either the upload record or existing record or
        record archived.

        Returns a Tuple of Dictionaries(For modified/added/deleted tags).
        """
        def remove_control_tag(tag_list):
            """
            Returns the list of keys without any control tags
            """

            cleaned_list = [item for item in tag_list
                    if item not in CFG_BIBUPLOAD_CONTROLFIELD_TAGS]
            return cleaned_list

        def group_record_tags():
            """
            Groups all the tags in a Record as Common/Added/Deleted tags.
            Returns a Tuple of 3 lists for each category mentioned above.
            """
            rec1_keys = record1.keys()
            rec2_keys = record2.keys()

            com_tag_lst = [key for key in rec1_keys if key in rec2_keys]
            # tags in record2 not present in record1
            del_tag_lst = [key for key in rec2_keys if key not in rec1_keys]
            # additional tags in record1
            add_tag_lst = [key for key in rec1_keys if key not in rec2_keys]

            return (com_tag_lst, add_tag_lst, del_tag_lst)

        # declaring dictionaries to hold the identified patch
        mod_patch = {}
        add_patch = {}
        del_patch = {}
        result = {}

        (common_tags, added_tags, deleted_tags) = group_record_tags()
        if common_tags:
            mod_patch = self.find_modified_tags(common_tags, record1, record2)

        if added_tags:
            for tag in added_tags:
                add_patch[tag] = record1[tag]

        # if record comes with correct, it should already have fields
        # marked with '0' code. If not deleted tag list will
        if deleted_tags and \
                opt_mode == 'replace' or opt_mode == 'delete':
            for tag in deleted_tags:
                del_patch[tag] = record2[tag]

        # returning back a result dictionary with all available patches
        if mod_patch:
            result['MOD'] = mod_patch

        if add_patch:
            result['ADD'] = add_patch

        if del_patch:
            # for a tag that has been deleted in the upload record in replace
            # mode, loop through all the fields of the tag and add additional
            # subfield with code '0' and value '__DELETE_FIELDS__'
            # NOTE Indicators taken into consideration while deleting fields
            for tag in del_patch:
                for data_tuple in del_patch[tag]:
                    ind1 = data_tuple[1]
                    ind2 = data_tuple[2]
                    record_delete_field(del_patch, tag, ind1, ind2)
                    record_add_field(del_patch, tag, ind1, ind2, "", [(CFG_BIBUPLOAD_DELETE_CODE, CFG_BIBUPLOAD_DELETE_VALUE)])
            result['DEL'] = del_patch

        return result

    def detect_conflict(self, up_record, up_patch, up_date, orig_record, orig_patch, orig_date):
        """
        Compares the generated patches for Upload and Original Records for any common tags.
        Raises Conflict Error in case of any common tags.

        Returns the upload record patch in case of no conflicts.
        """
        conflict_tags = []

        # if tag is modified in upload rec but modified/deleted in current rec
        if 'MOD' in up_patch:
            for tag in up_patch['MOD']:
                if 'MOD' in orig_patch and tag in orig_patch['MOD'] \
                or 'DEL' in orig_patch and tag in orig_patch['DEL']:
                    conflict_tags.append(tag)

        # if tag is added in upload rec but added in current revision
        if 'ADD' in up_patch:
            for tag in up_patch['ADD']:
                if 'ADD' in orig_patch and tag in orig_patch['ADD']:
                    conflict_tags.append(tag)

        # if tag is deleted in upload rec but modified/deleted in current rec
        if 'DEL' in up_patch:
            for tag in up_patch['DEL']:
                if 'MOD' in orig_patch and tag in orig_patch['MOD'] \
                or 'DEL' in orig_patch and tag in orig_patch['DEL']:
                    conflict_tags.append(tag)

        if conflict_tags:
            ## It looks like there are conflicting tags. However these might
            ## be false positive: we need to filter out those tags which
            ## have been modified in both situation but ends up having
            ## the same change.
            real_conflict_tags = []
            for tag in conflict_tags:
                if tag == '856':
                    ## HACK: FIXME: we are not yet able to preserve the sorting
                    ## of 8564 tags WRT FFT in BibUpload.
                    ## Therefore we implement here a workaround to ignore
                    ## the order of fields in case of 856.
                    ## See ticket #1606.
                    if tag in up_record and tag in orig_record and records_identical({tag: up_record[tag]}, {tag: orig_record[tag]}, ignore_duplicate_subfields=True, ignore_duplicate_controlfields=True, ignore_field_order=False, ignore_subfield_order=False):
                        continue
                elif tag in up_record and tag in orig_record and records_identical({tag: up_record[tag]}, {tag: orig_record[tag]}, ignore_duplicate_subfields=True, ignore_duplicate_controlfields=True):
                    continue
                elif tag not in up_record and tag not in orig_record:
                    continue
                else:
                    real_conflict_tags.append(tag)
            if real_conflict_tags:
                raise InvenioBibUploadConflictingRevisionsError(self.rec_id,
                                                            real_conflict_tags,
                                                            up_date,
                                                            orig_date,
                                                            up_record,
                                                            orig_record)

        return up_patch

    def generate_final_patch(self, patch_dict, recid):
        """
        Generates patch by merging modified patch and added patch

        Returns the final merged patch containing modified and added fields
        """
        def _add_to_record(record, patch):
            for tag in patch:
                for data_tuple in patch[tag]:
                    record_add_field(record, tag, data_tuple[1], data_tuple[2], '', subfields=data_tuple[0])
            return record

        final_patch = {}
        #tag_list = []

        # merge processed and added fields into one patch
        if 'MOD' in patch_dict:
            # tag_list = tag_list + patch_dict['MOD'].items()
            final_patch = _add_to_record(final_patch, patch_dict['MOD'])
        if 'ADD' in patch_dict:
            #tag_list = tag_list + patch_dict['ADD'].items()
            final_patch = _add_to_record(final_patch, patch_dict['ADD'])
        if 'DEL' in patch_dict:
            #tag_list = tag_list + patch_dict['DEL'].items()
            final_patch = _add_to_record(final_patch, patch_dict['DEL'])
        record_add_field(final_patch, '001', ' ', ' ', recid)
        return final_patch


    def retrieve_affected_tags_with_ind(self, patch):
        """
        Generates a dictionary of all the tags added/modified/romoved from
        record1 w.r.t record2 (record1 is upload record and record2 the existing one)

        Returns dictionary containing tag and corresponding ind pairs
        """
        affected_tags = {}

        # ==> Key will be either MOD/ADD/DEL and values will hold another dictionary
        # containing tags and corresponding fields

        for key in patch:
            item = patch[key]
            for tag in item:
                #each tag will have LIST of TUPLES (data)
                affected_tags[tag] = [(data_tuple[1], data_tuple[2]) for data_tuple in item[tag]]

        return affected_tags


    def verify_revision(self, verify_record, original_record, opt_mode=None):
        """
        Compares the upload record with the same 005 record from archive.

        Once the changes are identified, The latest revision of the record is fetched
        from the system and the identified changes are applied over the latest.

        Returns record patch in case of non-conflicting addition/modification/deletion
        Conflicting records raise Error and stops the bibupload process
        """

        upload_rev = ''
        original_rev = ''
        r_date = ''
        record_patch = {}

        # No need for revision check for other operations
        if opt_mode not in ['replace', 'correct']:
            return

        if '001' in verify_record:
            self.rec_id = record_get_field_value(verify_record, '001')

        # Retrieving Revision tags for comparison
        if '005' in verify_record:
            upload_rev = record_get_field_value(verify_record, '005')
            r_date = upload_rev.split('.')[0]

            if r_date not in [k[1] for k in get_record_revisions(self.rec_id)]:
                raise InvenioBibUploadInvalidRevisionError(self.rec_id, r_date)
        else:
            raise InvenioBibUploadMissing005Error(self.rec_id)

        if '005' in original_record:
            original_rev = record_get_field_value(original_record, '005')
        else:
            raise InvenioBibUploadMissing005Error(self.rec_id)

        # Retrieving the archived version
        marc_xml = get_marcxml_of_record_revision(self.rec_id, r_date)
        res = create_record(zlib.decompress(marc_xml[0][0]))
        archived_record = res[0]

        # Comparing Upload and Archive record
        curr_patch = self.compare_records(verify_record, archived_record, opt_mode)

        # No changes in Upload Record compared to Archived Revision
        # Raising Error to skip the bibupload for the record
        if not curr_patch:
            raise InvenioBibUploadUnchangedRecordError(self.rec_id, upload_rev)

        if original_rev == upload_rev:
            # Upload, Archive and Original Records have same Revisions.
            affected_tags = self.retrieve_affected_tags_with_ind(curr_patch)
            return ('correct', self.generate_final_patch(curr_patch, self.rec_id), affected_tags)

        # Comparing Original and Archive record
        orig_patch = self.compare_records(original_record, archived_record, opt_mode)

        # Checking for conflicts
        # If no original patch - Original Record same as Archived Record
        if orig_patch:
            curr_patch = self.detect_conflict(verify_record, curr_patch, upload_rev, \
                                                original_record, orig_patch, original_rev)

        record_patch = self.generate_final_patch(curr_patch, self.rec_id)
        affected_tags = self.retrieve_affected_tags_with_ind(curr_patch)

        # Returning patch in case of no conflicting fields
        return ('correct', record_patch, affected_tags)


class InvenioBibUploadUnchangedRecordError(Exception):
    """
    Exception for unchanged upload records.
    """

    def __init__(self, recid, current_rev):
        self.cur_rev = current_rev
        self.recid = recid

    def __str__(self):
        msg = 'UNCHANGED RECORD : Upload Record %s same as Rev-%s'
        return msg % (self.recid, self.cur_rev)


class InvenioBibUploadConflictingRevisionsError(Exception):
    """
    Exception for conflicting records.
    """

    def __init__(self, recid, tag_list, upload_rev, current_rev, up_record, orig_record):
        self.up_rev = upload_rev
        self.cur_rev = current_rev
        self.tags = tag_list
        self.recid = recid
        self.up_record = up_record
        self.orig_record = orig_record

    def __str__(self):
        msg = 'CONFLICT : In Record %s between Rev-%s and Rev-%s for Tags:\n' % (self.recid, self.up_rev, self.cur_rev)
        for tag in self.tags:
            msg += "  %s ->\n" % tag
            msg += "     original record: %s\n" % pformat(self.orig_record.get(tag))
            msg += "     uploaded record: %s\n" % pformat(self.up_record.get(tag))
        return msg


class InvenioBibUploadInvalidRevisionError(Exception):
    """
    Exception for incorrect revision of the upload records.
    """

    def __init__(self, recid, upload_rev):
        self.upload_rev = upload_rev
        self.recid = recid

    def __str__(self):
        msg = 'INVALID REVISION : %s for Record %s not in Archive.'
        return msg % (self.upload_rev, self.recid)


class InvenioBibUploadMissing005Error(Exception):
    """
    Exception for missing Revision field in Upload/Original records.
    """

    def __init__(self, recid):
        self.recid = recid
