# -*- coding: utf-8 -*-
#
# The following code is authored by Duncan McGreggor and is licensed
# under PSF license.  It was taken from
# <http://code.activestate.com/recipes/410469/>.

import six
import xml.etree.ElementTree as ElementTree


class XmlListConfig(list):
    def __init__(self, aList):
        for element in aList:
            if element:
                # treat like dict
                if len(element) == 1 or element[0].tag != element[1].tag:
                    self.append(XmlDictConfig(element))
                # treat like list
                elif element[0].tag == element[1].tag:
                    self.append(XmlListConfig(element))
            elif element.text:
                text = element.text.strip()
                if text:
                    self.append(text)


class XmlDictConfig(dict):
    '''
    Example usage:

    >>> tree = ElementTree.parse('your_file.xml')
    >>> root = tree.getroot()
    >>> xmldict = XmlDictConfig(root)

    Or, if you want to use an XML string:

    >>> root = ElementTree.XML(xml_string)
    >>> xmldict = XmlDictConfig(root)

    And then use xmldict for what it is... a dict.
    '''
    def __init__(self, parent_element):
        if parent_element.items():
            self.update(dict(parent_element.items()))

        for element in parent_element:
            if element:
                # treat like dict - we assume that if the first two tags
                # in a series are different, then they are all different.
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = XmlDictConfig(element)
                # treat like list - we assume that if the first two tags
                # in a series are the same, then the rest are the same.
                else:
                    # here, we put the list in dictionary; the key is the
                    # tag name the list elements all share in common, and
                    # the value is the list itself
                    aDict = {element[0].tag: XmlListConfig(element)}
                # if the tag has attributes, add those to the dict
                if element.items():
                    aDict.update(dict(element.items()))
                self.update({element.tag: aDict})
            # this assumes that if you've got an attribute in a tag,
            # you won't be having any text. This may or may not be a
            # good idea -- time will tell. It works for the way we are
            # currently doing XML configuration files...
            elif element.items():

                # this assumes that if we got a single attribute
                # with no children the attribute defines the type of the text
                if len(element.items()) == 1 and not list(element):
                    # check if its str or unicode and if the text is empty,
                    # otherwise the tag has empty text, no need to add it
                    if isinstance(element.text, six.string_types) and element.text.strip() != '':
                        # we have an attribute in the tag that specifies
                        # most probably the type of the text
                        tag = element.items()[0][1]
                        self.update({element.tag: dict({tag: element.text})})
                else:
                    self.update({element.tag: dict(element.items())})
                    if not list(element) and isinstance(element.text, six.string_types)\
                        and element.text.strip() != '':
                        self[element.tag].update(dict({"text": element.text}))
            # finally, if there are no child tags and no attributes, extract
            # the text
            else:
                self.update({element.tag: element.text})

