import urllib.parse, urllib.request, urllib.error, json, random, jinja2, os
from flask import Flask, render_template, request
from sightengine.client import SightengineClient

JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(
    os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

app = Flask(__name__)

@app.route("/")
def main_handler():
    return render_template('submitform.html',page_title="Homepage")

@app.route("/gresponse")
def image_response_handler():
    imageurl = request.args.get('image')
    if imageurl:
        title = eng_title(imageurl)
        animepics = related_pics(imageurl, 5)
        animepics.append(imageurl)
        stockpics = findphotos(imageurl, max=6)
        pics = animepics + stockpics
        if len(pics) < 12:
            return render_template('not_enough.html', page_title='Stumped')
        random.shuffle(pics)
        pics = makecolumns(pics, 3)
    return render_template('animepics.html',title=title, pics=pics)
#
#
#
@app.errorhandler(Exception)
def error(error):
    return render_template('no_anime.html',page_title="Oops")

def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)
#
#
#Returns MyAnimeList ID for inputed anime image or GIF
def find_id(imageurl):
        return pic_data_safe(imageurl)['docs'][0]['mal_id']
#
#
#Returns English title for inputed image or GIF
def eng_title(imageurl):
       return pic_data_safe(imageurl)['docs'][0]['title_english']
#
#
#Accesses JIKAN API to return more json data on an anime based on inputed image or GIF
def anime_data(imageurl = None, request = None, baseurl = 'https://api.jikan.moe/v3/anime'):
    id = find_id(imageurl)
    url = baseurl + '/' + str(id) + '/' + str(request or '')
    result = urllib.request.urlopen(url)
    result = result.read()
    jsonresult = json.loads(result)
    return jsonresult
#
#
#Safe version of anime_data
def anime_data_safe(imageurl = None, request = None, baseurl = 'https://api.jikan.moe/v3/anime'):
    try:
        return anime_data(imageurl, request)
    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print('Error trying to retrieve data. HTTP Error code ', e.code, ': ', e.reason, sep='')
        elif hasattr(e, 'reason'):
            print("We failed to reach a server")
            print("Reason: ", e.reason)
        return None
#
#
#Accesses 'What Anime' API to identify anime from inputed screenshot or GIF, returns json data
def pic_data(imageurl, baseurl = 'https://trace.moe/api/search', params = {}):
    params['url'] = imageurl
    url = baseurl + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': "Magic Browser"})
    result = urllib.request.urlopen(req)
    result = result.read().decode("utf-8")
    jsonresult = json.loads(json.dumps(result))
    jsonresult = json.loads(jsonresult)
    return jsonresult
#
#
#Safe version of pic_data
def pic_data_safe(imageurl):
    try:
        return pic_data(imageurl)
    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print('Error trying to retrieve data. HTTP Error code ', e.code, ': ', e.reason, sep='')
        elif hasattr(e, 'reason'):
            print("We failed to reach a server")
            print("Reason: ", e.reason)
            return None
#
#
#Finds related images based on the inputed picture
def related_pics(imageurl, max = None):
    pics = []
    list = anime_data_safe(imageurl, request='pictures')
    for size in list['pictures']:
       if len(pics) < max:
           pics.append(size.get('small'))
    return pics
#
#
# Finding dominant color of input image
def findcolor(imageurl):
    client = SightengineClient('1735422858', '3rCkijpPF2KaNLdyyPTS')
    output = client.check('properties').set_url(imageurl)
    return output['colors']['dominant']['hex'][1:]

#
#
# Convert RBG color into Pantone color name
def colorname(imageurl, baseurl = 'http://thecolorapi.com/id?hex='):
    url = baseurl + findcolor(imageurl)
    result = urllib.request.urlopen(url)
    result = result.read()
    jsonresult = json.loads(result)
    color = jsonresult['name']['value']
    if ' ' in color:
        color = color.replace(' ', '-')
    return color
#
#
# Getting photos from Unsplash
def findphotos(imageurl, baseurl = 'https://api.unsplash.com/search/photos?page=1&query=', max = None):
    url = baseurl + colorname(imageurl) + '&client_id=eflbp7YWT-tdtY43j95fw9_0RSeOE1DcTX0QrBUFrGA'
    print(url)
    result = urllib.request.urlopen(url)
    result = result.read()
    jsonresult = json.loads(result)
    photos = []
    for photo in jsonresult['results']:
        if len(photos) < max:
            photos.append(photo['urls']['regular'])
    return photos
#
#
#
# Prepping list of pics for html layout
def makecolumns(pics, n):
    for i in range(0, len(pics), n):
        yield pics[i:i + n]

if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)
