#shooter.cn
#Subtitles service allowed by www.shooter.cn

import io
import os
import hashlib
import json
import urllib
import urllib2
from urllib2 import HTTPError
import httplib
from pyTongwen.conv import TongWenConv
import pysrt
__TONGWEN = TongWenConv()

SHOOTER_API = 'https://www.shooter.cn/api/subapi.php'
# OS_LANGUAGE_CODES = 'http://www.opensubtitles.org/addons/export_languages.php'
SHOOTER_PLEX_USERAGENT = 'plexapp.com v9.0'
subtitleExt       = ['utf','utf8','utf-8','sub','srt','smi','rt','ssa','aqt','jss','ass','idx']

def Start():
  HTTP.CacheTime = 0
  HTTP.Headers['User-agent'] = SHOOTER_PLEX_USERAGENT
  Log.Debug("Shooter Agent Start")

def to_unicode(sub_str):
    encoding = chardet.detect(sub_str).get('encoding')
    if encoding:
        sub_unicode = unicode(sub_str, encoding, 'ignore')
    return sub_unicode

def reset_index(sub_unicode):
    subs = pysrt.from_string(sub_unicode)
    for i in range(1, len(subs) + 1):
        subs[i - 1].index = i

    new_sub = StringIO.StringIO()
    subs.write_into(new_sub)
    new_sub_unicode = new_sub.getvalue()
    new_sub.close()
    return new_sub_unicode

def fetchSubtitle(url):
  Log("fetching subtitle %s" % (url))
  folder, filename = os.path.split(url)
  filename_without_extension, extension = os.path.splitext(filename)

  # check subtitle whether exists or not
  for ext in subtitleExt:
    subtitle = "%s.%s" % (filename_without_extension, ext)
    file_path = os.path.join(folder, subtitle)
    if os.path.exists(file_path):
      Log("subtitle file(s) has already existed.")
      # return

  statinfo = os.stat(url)
  file = io.open(url, "rb")

  file_size = statinfo.st_size

  if (file_size < 8 * 1024):
    Log("It's impossible that video file length is less than 8k")
    return

  positions = []
  positions.append(4 * 1024)
  positions.append(file_size / 3)
  positions.append(file_size / 3 * 2)
  positions.append(file_size - (8 * 1024))

  hashes = []
  for p in positions:
    file.seek(p)
    byte_data = file.read(4 * 1024)
    hashes.append(hashlib.md5(byte_data).hexdigest())

  filehash = ';'.join(hashes)

  post_data = {'filehash' : filehash, 'pathinfo' : filename, 'format' : 'json', 'lang' : 'Chn'}
  # user_agent = "SPlayerX 1.1.8 (Build 1113)"
  headers = {'Content-Type' : 'application/x-www-form-urlencoded', 'User-Agent' : SHOOTER_PLEX_USERAGENT}
  params = urllib.urlencode(post_data)

  req = urllib2.Request(SHOOTER_API, params, headers)
  response = urllib2.urlopen(req)
  json_data = json.load(response)

  if len(json_data) == 0:
    Log('Wrong response from Shooter.cn API')
    return

  subtitles = []
  for json_obj in json_data:
    if len(json_obj['Files']) > 0:
      file_json = json_obj['Files'][0]
      subtitle_link = file_json['Link']
      subtitle_extension = file_json["Ext"]
      subtitle_filename = "%s.%s" % (filename_without_extension, subtitle_extension)
      subtitle_obj = {'ext' : subtitle_extension,
                      'link' : subtitle_link,
                      'subtitle_filename' : subtitle_filename}
      subtitles.append(subtitle_obj)

  if len(subtitles) == 0:
    return

  subtitle_to_download = subtitles[0]
  for subtitle in subtitles:
    if subtitle['ext'] == 'ass':
      subtitle_to_download = subtitle
      break

  try :
    u = urllib2.urlopen(subtitle_to_download['link'])
    fileurl = os.path.join(folder, subtitle_to_download['subtitle_filename'])
    with io.open(fileurl, "wb") as subtitle_file:
      subtitle_string = u.read()
      unicode_subtitle = to_unicode(subtitle_string)
      if subtitle_to_download['ext'] == 'srt':
        unicode_subtitle = reset_index(unicode_subtitle)
      subtitle_file.write(unicode_subtitle)

    Log.Debug("subtitle %s downloaded" % (subtitle_to_download['subtitle_filename']))

  except urllib2.HTTPError, e:
    Log("HTTP Error:", e.code, link)
  except urllib2.URLError, e:
    Log("URL Error:", e.reason, link)


class ShooterAgentMovies(Agent.Movies):
  name = 'Shooter.cn'
  languages = [Locale.Language.Chinese]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb']

  def search(self, results, media, lang):
    Log.Debug("ShooterAgentMovies.search")
    results.Append(MetadataSearchResult(
      id    = "null",
      score = 100
    ))


  def update(self, metadata, media, lang):
    Log.Debug("ShooterAgentMovies.update")
    for i in media.items:
      for part in i.parts:
        fetchSubtitle(part.file)



class ShooterAgentTVShows(Agent.TV_Shows):
  name = 'Shooter.cn'
  languages = [Locale.Language.Chinese]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.thetvdb']

  def search(self, results, media, lang, manual):
    Log.Debug("ShooterAgentTVShows.search")
    results.Append(MetadataSearchResult(
      id    = "null",
      score = 100
    ))


  def update(self, metadata, media, lang, force):
    Log.Debug("ShooterAgentTVShows.update")
    for s in media.seasons:
      # just like in the Local Media Agent, if we have a date-based season skip for now.
      if int(s) < 1900:
        for e in media.seasons[s].episodes:
          for i in media.seasons[s].episodes[e].items:
            for part in i.parts:
              fetchSubtitle(part.file)


