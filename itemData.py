# Copyright 2010 Brian E. Chapman
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# rewrite instantiateFromCSVtoitemData function to allows comments lines and auto-fix empty cells,
# and allows reading from yml files


"""
A module defining the itemData class. itemData objects are the basis tools for text markup.
"""
import platform

import os
import yaml

if platform.python_version_tuple()[0] == '2':

    import unicodecsv as csv
    import urllib2


    def get_fileobj(csvFile):
        p = urllib2.urlparse.urlparse(csvFile)
        if not p.scheme:
            csvFile = "file://" + csvFile
        f0 = urllib2.urlopen(csvFile, 'rU')
        return csv.reader(f0, encoding='utf-8', delimiter="\t"), f0

else:
    import csv
    import urllib.request, urllib.error, urllib.parse
    from io import StringIO


    def get_fileobj(csvFile):
        p = urllib.parse.urlparse(csvFile)
        if not p.scheme:
            csvFile = "file://" + csvFile
        f0 = urllib.request.urlopen(csvFile, data=None)
        return csv.reader(StringIO(f0.read().decode(), newline=None), delimiter="\t"), f0


class contextItem(object):
    __numEnteries = 4

    def __init__(self, args):
        # print(args)
        self.__literal = args[0]
        # now get category(categories)
        cs = args[1].split(",")
        self.__category = []
        for c in cs:
            self.__category.append(c.lower().strip())
        self.__re = args[2]  # I need to figure out how to read this raw string in properly
        self.__rule = args[3]

    def getLiteral(self):
        """return the literal associated with this item"""
        return self.__literal

    def getCategory(self):
        """return the list of categories associated with this item"""
        return self.__category[:]

    def categoryString(self):
        """return the categories as a string delimited by '_'"""
        return '_'.join(self.__category)

    def isA(self, testCategory):
        """test whether testCategory is one of the categories associated with self"""
        try:
            return testCategory.lower().strip() in self.__category
        except:
            for tc in testCategory:
                if (tc.lower().strip() in self.__category):
                    return True
            return False

    def getRE(self):
        return self.__re

    def getRule(self):
        return self.__rule

    def __unicode__(self):
        txt = """literal<<{0}>>; category<<{1}>>; re<<{2}>>; rule<<{3}>>""".format(
            self.__literal, self.__category, self.__re, self.__rule)
        return txt

    def __str__(self):
        return self.__unicode__()  # .encode('utf-8')

    def __repr__(self):
        return self.__str__()


class itemData(list):
    def __init__(self, *args):
        if args:
            for a in args:
                if self.__validate(a):
                    itm = a
                else:
                    try:
                        itm = contextItem(a)
                    except:
                        itm = None
                if itm:
                    super(itemData, self).append(itm)

    def __validate(self, data):
        return isinstance(data, contextItem)

    def append(self, data):
        if self.__validate(data):
            itm = data
        else:
            itm = contextItem(data)
        super(itemData, self).append(itm)

    def insert(self, index, data):
        if self.__validate(data):
            itm = data
        else:
            itm = contextItem(data)
        super(itemData, self).insert(index, itm)

    def prepend(self, iterable):
        for i in iterable:
            if self.__validate(i):
                itm = i
            else:
                itm = contextItem(i)
            super(itemData, self).insert(0, itm)

    def extend(self, iterable):
        for i in iterable:
            if self.__validate(i):
                itm = i
            else:
                itm = contextItem(i)
            super(itemData, self).append(itm)

    def __unicode__(self):
        tmp = """itemData: {0:d} items [""".format(len(self))
        for i in self:
            tmp = tmp + "{0}, ".format(i.getLiteral())
        tmp = tmp + "]"
        return tmp

    def __repr__(self):
        return self.__unicode__()  # .encode('utf-8')

    def __str__(self):
        return self.__repr__()


def get_item_data(file_str):
    file_name = file_str.lower()
    if file_name.endswith(".csv") or file_name.endswith(".tsv") or file_name.endswith(".yml"):
        pwd = os.getcwd()
        if pwd not in file_str:
            file_str = os.path.join(pwd, file_str)
        if not os.path.exists(file_str):
            return itemData()
        if file_name.endswith('csv') or file_name.endswith('tsv'):
            return instantiateFromCSVtoitemData(file_str)
        elif file_name.endswith('yml'):
            return instantiateFromYMLtoitemData(file_str)
        else:
            return itemData()
    elif "Comments:" in file_str:
        return instantiateFromYMLStr(file_str)
    elif ',' in file_str:
        return instantiateFromCSVStr(file_str, ',')
    elif '\t' in file_str:
        return instantiateFromCSVStr(file_str, '\t')
    else:
        print(
            "This input format is not supported. It can be either a path of csv, tsv or yaml file, or a string of corresponding file content.")


def instantiateFromCSVStr(content, splitter):
    reader = csv.reader(content.split('\n'), delimiter=splitter)
    items = itemData()
    for row in reader:
        # print(row)
        tmp = read_row(row)
        if tmp is None:
            continue
        # tmp = [row[literalColumn], row[categoryColumn],
        # 	   row[regexColumn], row[ruleColumn]]
        # tmp[2] = r"{0}".format(tmp[2])  # convert the regular expression string into a raw string
        item = contextItem(tmp)
        items.append(item)
    return items


def instantiateFromYMLStr(content):
    context_items = [contextItem((d["Lex"],
                                  d["Type"],
                                  r"%s" % d["Regex"],
                                  d["Direction"])) for d in yaml.load_all(content)]
    return context_items


def instantiateFromYMLtoitemData(_file):
    def get_fileobj(_file):
        if not urllib.parse.urlparse(_file).scheme:
            _file = "file://" + _file
        return urllib.request.urlopen(_file, data=None)

    f0 = get_fileobj(_file)
    context_items = [contextItem((d["Lex"],
                                  d["Type"],
                                  r"%s" % d["Regex"],
                                  d["Direction"])) for d in yaml.load_all(f0)]
    return context_items


def instantiateFromCSVtoitemData(csvFile, encoding='utf-8', headerRows=1, literalColumn=0, categoryColumn=1,
                                 regexColumn=2, ruleColumn=3):
    items = itemData()  # itemData to be returned to the user
    header = []
    reader, f0 = get_fileobj(csvFile)
    # reader = csv.reader(open(csvFile, 'rU'))
    # first grab numbe rof specified header rows
    for i in range(headerRows):
        row = next(reader)
        header.append(row)
    # now grab each itemData
    for row in reader:
        # print(row)
        tmp = read_row(row)
        if tmp is None:
            continue
        # tmp = [row[literalColumn], row[categoryColumn],
        # 	   row[regexColumn], row[ruleColumn]]
        # tmp[2] = r"{0}".format(tmp[2])  # convert the regular expression string into a raw string
        item = contextItem(tmp)
        items.append(item)
    f0.close()
    return items


def read_row(row):
    tmp = []
    if len(row) < 2 or row[0].startswith('#'):
        return None
    tmp.extend([row[0], row[1]])
    if len(row) == 3:
        tmp.extend([r"{0}".format(row[2]), ''])
    elif len(row) == 2:
        tmp.extend(['', ''])
    else:
        tmp.extend([row[2], row[3]])
    return tmp
