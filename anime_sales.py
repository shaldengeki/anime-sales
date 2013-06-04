#!/usr/bin/env python

import argparse
import datetime
import glob
import os
import pytz
import re
import urllib2

class Sales(object):
  def __init__(self, title=None, data=None):
    self.type = None
    self.sources = None
    self.anime = {}
    self._sales = []
    self.totalSales = []
    if title is not None:
      self.anime[title] = 0
    if data is not None:
      self._sales = [data]
      self.totalSales.append(sum([y['sales'] for x in self._sales for y in x]))
    self.regexes = [
      ('season-volume', re.compile(r"(?P<title>.*?)\ +(?:[Ss]eason(\ )*(?P<season>[0-9]+))\ +(?:[Vv](ol)?\.*\ *\#*(?P<volume>[0-9]+))")),
      ('nth season-volume', re.compile(r"(?P<title>.*?)\ +((?P<season>[0-9]{1})[A-Za-z]{2}\ [Ss]eason)\ +(?:[Vv](ol)?\.*\ *\#*(?P<volume>[0-9]+))")),
      ('nth season', re.compile(r"(?P<title>.*?)\ +((?P<season>[0-9]{1,3})[A-Za-z]{2}\ [Ss]eason)")),
      ('volume-part', re.compile(r"(?P<title>.*?)\ +(([Vv](ol)?\.?\ *\#?(?P<volume>[0-9]+)))\ +(([Pp](ar)?t\.?\ *\#?(?P<part>[0-9]+)))")),
      ('volume', re.compile(r"(?P<title>.*?)\ +(?:[Vv](ol)?(ume)?\.*\ *\#*(?P<volume>[0-9]+))")),
      ('part', re.compile(r"(?P<title>.*?)\ +(([Pp](ar)?t\.?\ *\#?(?P<part>[0-9]+)))")),
      ('season', re.compile(r"(?P<title>.*?)\ +(?:[Ss]eason(\ )*(?P<season>[0-9]+))")),
      ('fallback', re.compile(r"(?P<title>.*)"))
    ]
  def parseTitle(self, title):
    """
    Parses a sales data entry title and attempts to figure out its component parts.
    """
    for pattern in self.regexes:
      result = pattern[1].match(title)
      if result:
        break
    matchedTitle = result.groupdict()
    matchedTitle['regex'] = pattern[0]
    return matchedTitle
  def parseLine(self, line):
    """
    Parses a line of a sales data file and returns a dict of sales numbers.
    """
    matchLine = re.match(r"\(?(\**)(?P<rank>[0-9\,\.]+)?([\(\)-]+)?(\**)\)?(\ +)\(?((\**)(?P<prevRank>[0-9\.\,]+))?(-+)?(\*+)?\)?(\ +)((\**)(?P<unknown>[0-9\.\,]+))?(-+)?(\*+)?\)?(\ +)(\**)(?P<sales>[0-9\,\.]+)(\ +)([\*\,]*)(?P<totalSales>[0-9\,\.]+)(\ +)(\**)(?P<weeks>[0-9]+)(\ +)(?P<title>.+)", line)
    try:
      matchDict = matchLine.groupdict()
      matchDict['sales'] = None if matchDict['sales'] is None else int(matchDict['sales'].replace(",", "").replace(".", ""))
      matchDict['totalSales'] = None if matchDict['totalSales'] is None else int(matchDict['totalSales'].replace(",", "").replace(".", ""))
      matchDict['rank'] = None if matchDict['rank'] is None else int(matchDict['rank'])
      matchDict['prevRank'] = None if matchDict['prevRank'] is None else int(matchDict['prevRank'])
      matchDict['weeks'] = None if matchDict['weeks'] is None else int(matchDict['weeks'])
      matchDict['series'] = None if matchDict['title'] is None else self.parseTitle(matchDict['title'].lower())
      if matchDict['series'] is not None:
        matchDict['title'] = matchDict['series']['title']
        print "Title pattern used:",matchDict['series']['regex']
    except:
      print "Could not read a line of sales data:"
      print line
      return {}
    return matchDict
  def parseFile(self, filename):
    """
    Parses a sales data file and returns a dict of sales numbers.
    """
    anime = {}
    print "Parsing: " + filename
    fileDate = os.path.basename(filename).split("-")[0:3]
    with open(filename, 'r') as f:
      for line in f:
        saleData = self.parseLine(line)
        if 'series' in saleData:
          saleData['date'] = datetime.datetime.strptime("/".join(fileDate), '%Y/%m/%d')
          (saleData['year'], saleData['month'], saleData['day']) ="/".join(fileDate).split("/")
          anime[saleData['series']['title']] = [saleData]
    return anime
  def load(self):
    if self.sources is None:
      print "No sources found; auto-loading from ./data"
      self.sources = os.listdir("data")
    self.anime = {}
    animeId = 0
    for source in self.sources:
      path = os.path.join("data", source)
      print "Loading from " + path
      for filename in os.listdir(path):
        fileData = self.parseFile(os.path.join(path, filename))
        for animeTitle in fileData.keys():
          if animeTitle not in self.anime:
            self.anime[animeTitle] = animeId
            self._sales.append([])
            self.totalSales.append(0)
            animeId += 1
          for x in fileData[animeTitle]:
            x['id'] = self.anime[animeTitle]
          [self._sales[self.anime[animeTitle]].append(x) for x in fileData[animeTitle]]
  def save(self, filenamePrefix):
    """
    Exports time-series sales data for anime.
    """
    with open(filenamePrefix + ".titles", 'wb') as f:
      f.write("title,id\n")
      for title in self.anime:
        f.write(title + "," + str(self.anime[title]) + "\n")
    with open(filenamePrefix + ".sales", 'wb') as f:
      fields = [key for key in self._sales[0][0] if key is not "date" and key is not "series"]
      f.write(",".join(fields) + "\n")
      for title in self.anime:
        for data in self._sales[self.anime[title]]:
          if 'date' in data:
            data['dateStamp'] = data['date'].strftime("%Y/%m/%d")
            del(data['date'])
          if 'series' in data:
            del(data['series'])
          data['title'] = data['title'].replace(",", "")
          point = [str(data[field]) for field in fields]
          f.write(",".join(point) + "\n")
  def search(self, title):
    """
    Returns a list of anime titles beginning with the given string.
    """
    return [x for x in self.anime if title in x]
  def series(self, title):
    """
    Returns a series object for the given series.
    """
    if title not in self.anime:
      print "The provided anime could not be found."
      return
    return Series(title, sales=self._sales[self.anime[title]])
  def sales(self, fields=None):
    if self._sales is None:
      return []
    if fields is None:
      fields = self._sales[0][0].keys()
    return [[{field: y[field] for field in fields} for y in x] for x in self._sales]

class Series(object):
  def __init__(self, title, sales=None):
    self.title = title
    self._sales = sales
  def sales(self, fields=None):
    if self._sales is None:
      return []
    if fields is None:
      fields = self._sales[0].keys()
    return Sales(title=self.title, data=[{desiredKey: salesEntry[desiredKey] for desiredKey in fields} for salesEntry in self._sales])

if __name__ == "__main__":
  salesData = Sales()
  salesData.load()
  print "Anime:",str(len(salesData.anime))