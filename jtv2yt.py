import urllib
import urllib2
import json
import datetime
import os
import sys

import gdata.youtube
import gdata.youtube.service
import gdata.media

yt_service = None

def yt_login(email, password):
    global yt_service
    yt_service = gdata.youtube.service.YouTubeService()
    yt_service.developer_key = "AI39si6jmyvGwJAaMZLhJ1vUGormpl7qar2VANYIXrPm452oKVHNz4-06akIR3D28l63Jnje75VArTqtBvpnNa-ilnsdGcFCSg"
    yt_service.client_id = "jtv2yt"
    yt_service.email = email
    yt_service.password = password
    yt_service.source = "jtv2yt"
    yt_service.ProgrammaticLogin()

def yt_upload(filename, jtv_metadata):
    global yt_service
    metadata = gdata.media.Group(
        title = gdata.media.Title(text=jtv_metadata["title"]),
        description = gdata.media.Description(description_type="plain", text=jtv_metadata["description"]),
        category=[gdata.media.Category(text="Tech", scheme="http://gdata.youtube.com/schemas/2007/categories.cat", label="Science & Technology")], # FIXME: Make this a user-specified option.
    )

    video_entry = gdata.youtube.YouTubeVideoEntry(media=metadata)
    return yt_service.InsertVideoEntry(video_entry, filename)

def transfer_videos(jtv_login, yt_email, yt_password, start_date=None, end_date=None):
    all_data = jtv_get_archive_data(jtv_login)
    some_data = []

    for item in all_data:
        if "kind" in item and item["kind"] == "highlight" and "video_file_url" in item and item["video_file_url"]:
            date_created = datetime.datetime.strptime(item["created_on"], "%Y-%m-%d %H:%M:%S %Z").date()

            if start_date and date_created < start_date:
                continue

            if end_date and date_created > end_date:
                continue

            some_data.append(item)

    yt_login(yt_email, yt_password)
    num_items = len(some_data)
    item_counter = 0

    print num_items, "videos to be transfered"

    for item in some_data:
        item_counter += 1
        ctr_string = "[" + str(item_counter) + "/" + str(num_items) + "]"
        print ctr_string, "Downloading video \"" + item["title"] + "\" from Justin.tv, reported size:", item["file_size"], "bytes"
        filename = urllib.urlretrieve(item["video_file_url"])[0]
        file_size = os.stat(filename).st_size
        print ctr_string, "Uploading video \"" + item["title"] + "\" to YouTube, file size:", file_size, "bytes"
        yt_upload(filename, item)

    print num_items, "transfers complete"

def jtv_get_archive_data(login):
    MAX_RESULTS = 100
    params = {"limit": MAX_RESULTS, "offset": 0}
    data = []

    while True:
        databatch = jtv_api_request("channel/archives", login, getdict=params)

        if(len(databatch) > 0):
            params["offset"] += len(databatch)
            data += databatch
        else:
            break

    return data

def jtv_api_request(api, login="", getdict=None, postdict=None):
    BASE_URL = "http://api.justin.tv/api/"
    FORMAT = "json"
    if login != "": login = "/" + login
    url = BASE_URL + api + login + "." + FORMAT

    if getdict:
        getparams = urllib.urlencode(getdict)
        url += "?" + getparams

    if postdict:
        postdata = urllib.urlencode(postdict)
        request = urllib2.Request(url, postdata)
    else:
        request = urllib2.Request(url)

    response = urllib2.urlopen(request)
    
    return json.loads(response.read())

if len(sys.argv) < 6:
    print "Usage:"
    print "  python jtv2yt.py jtv_login yt_email yt_password start_date end_date"
    print
    print "Example:"
    print "  python jtv2yt.py myjtvchannel youtubeuser@example.com MyYouTubePassword 2010-05-28 2011-07-15"
    exit()

jtv_login = sys.argv[1]
yt_email = sys.argv[2]
yt_password = sys.argv[3]
start_date = datetime.datetime.strptime(sys.argv[4], "%Y-%m-%d").date()
end_date = datetime.datetime.strptime(sys.argv[5], "%Y-%m-%d").date()

transfer_videos(jtv_login, yt_email, yt_password, start_date, end_date)
