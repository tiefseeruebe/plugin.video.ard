# -*- coding: utf-8 -*-
# Module: default
# Author: Roman V. M.
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import ast
import json
import sys
import urllib
import urllib2
from urllib import urlencode
from urlparse import parse_qsl

import xbmcgui
import xbmcplugin
import xbmc
from StringIO import StringIO
import gzip
import ssl
# from jsonpath_ng import jsonpath, parse

# Get the plugin url in plugin:// notation.
URL = 'url'
REF_URL = 'ref_url'
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

WIN_ID = 10000
win = xbmcgui.Window(WIN_ID)
WIDGET_PROP_NAME = 'libardjsonparser.widgets'
CATEGORY = 'category'
WIDGET_ID = 'widget_id'
TITLE = 'title'
LISTING = 'listing'
TEASERS = 'teasers'

VARS = {'name': 'home', 'client': 'ard', 'personalized': False}
EXTS = {
    'persistedQuery': {'version': 1, 'sha256Hash': '41ff7fbd45523453c78e2a780a83884ba5b66ce1483bdf1b3a3c3635491923a8'}}
CATEGORIES = {'Overview': {
    'url': 'https://api.ardmediathek.de/public-gateway?' +
           'variables=' + urllib.quote(json.dumps(VARS)) +
           '&extensions=' + urllib.quote(json.dumps(EXTS))
}
}


def log(msg):
    xbmc.log(str(msg))


log("_handle")
log(_handle)


def is_integer(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: 'argument=value' pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def get_categories():
    """
    Get the list of video categories.

    Here you can insert some parsing code that retrieves
    the list of video categories (e.g. 'Movies', 'TV-shows', 'Documentaries' etc.)
    from some site or server.

    .. note:: Consider using `generator functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.

    :return: The list of video categories
    :rtype: types.GeneratorType
    """
    return CATEGORIES.iterkeys()


def list_main_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'ARD Mediathek')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get video categories
    cat_iter = get_categories()
    # Iterate through categories
    for cat_key in cat_iter:
        category = CATEGORIES[cat_key]
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=cat_key)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        if 'thumb' in category:
            list_item.setArt({'thumb': category['thumb'],
                              'icon': category['thumb'],
                              'fanart': category['thumb']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
        # 'mediatype' is needed for a skin to display info for this ListItem correctly.
        list_item.setInfo('video', {TITLE: cat_key,
                                    'genre': cat_key,
                                    'mediatype': 'video'})
        list_item.setInfo(URL, category[URL])
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action=LISTING, category=cat_key)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def url_get(url, use_proxy=False, verify_ssl=True):
    # type: (str, bool, bool) -> str
    log('get_widgets')
    log('url')
    log(url)

    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0')
    req.add_header('Accept-Encoding', 'gzip, deflate')

    if not verify_ssl:
        log('set ssl context')
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        log('set opener ...')
        if use_proxy:
            log('set proxy')
            proxy = urllib2.ProxyHandler({'http': 'http://192.168.178.43:8080',
                                          'https': 'http://192.168.178.43:8080'
                                          })
            opener = urllib2.build_opener(urllib2.HTTPSHandler(context=ctx), proxy)
        else:
            opener = urllib2.build_opener(urllib2.HTTPSHandler(context=ctx))
        log('opener.open ...')
        response = opener.open(req)
    else:
        response = urllib2.urlopen(req)
    compressed = response.info().get('Content-Encoding') == 'gzip'
    body = response.read()
    response.close()
    if compressed:
        buf = StringIO(body)
        f = gzip.GzipFile(fileobj=buf)
        body = f.read()
    return body


def parse_teasers(widgets, widget_id):
    log('parse_teasers')
    log(widget_id)
    log(widgets)

    for widget in widgets:
        if widget['id'] != widget_id:
            continue
        parse_teaser(widget)
        break


def parse_teaser(widget):
    log('parse_teaser')
    log(widget)
    teasers = widget[TEASERS]
    for teaser in teasers:  # type: list
        item = {TITLE: teaser['shortTitle'],
                URL: teaser['links']['target']['href'], '_type': 'dir'}
        # log(teaser['shortTitle'].encode('ascii'))
        add_dir_item(item)


def list_category(params):
    """
    Create the list of playable videos in the Kodi interface.

    :param params:
    :type params: list
    """
    log('list_category')
    log(params)
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    if CATEGORY in params:
        cat_key = params[CATEGORY]
        xbmcplugin.setPluginCategory(_handle, cat_key)
        url = CATEGORIES[cat_key]['url']
    if WIDGET_ID in params:
        widget_id = params[WIDGET_ID]
        widgets_string = win.getProperty(WIDGET_PROP_NAME)
        log("widget_string :")
        log(widgets_string)
        if widget_id > 0 and len(widgets_string) > 0:
            widgets = ast.literal_eval(widgets_string)
            parse_teasers(widgets, widget_id)
    else:
        if URL in params:
            url = params[URL]

        body_str = url_get(url)
        body = json.loads(body_str)

        if URL in params:
            widgets = body['widgets']
            for widget in widgets:
                if widget['type'] == 'player_ondemand':
                    list_item = xbmcgui.ListItem(label=widget[TITLE])
                    list_item.setInfo('video', {'title': widget[TITLE],
                                                'mediatype': 'video'})
                    list_item.setProperty('IsPlayable', 'true')
                    media_stream_list = widget['mediaCollection']['embedded']['_mediaArray'][0]['_mediaStreamArray']
                    auto_idx = get_quality(media_stream_list)
                    log('auto_idx')
                    log(auto_idx)
                    link = media_stream_list[auto_idx]['_stream']
                    if link.startswith('//'):
                        link = 'http:' + link
                    log(link)
                    url = get_url(action='play', video=link)
                    is_folder = False
                    xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
                if TEASERS in widget:
                    parse_teaser(widget)
        else:
            body_str = url_get(url)
            body = json.loads(body_str)
            widgets = body['data']['defaultPage']['widgets']
            win.setProperty(WIDGET_PROP_NAME, repr(widgets))

            # Set plugin content. It allows Kodi to select appropriate views
            # for this type of content.
            xbmcplugin.setContent(_handle, 'videos')
            # Iterate through widgets.
            for widget in widgets:
                item = {TITLE: widget[TITLE], WIDGET_ID: widget['id']}
                add_dir_item(item)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    # xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def get_quality(media_stream_list):
    max_qual = -1
    for i, media_stream in enumerate(media_stream_list):
        if '_quality' in media_stream:
            quality = media_stream['_quality']
            if quality == 'auto':
                return i
            if is_integer(quality) and quality > max_qual:
                max_qual = i
    return max_qual


def add_dir_item(item):
    log('add_dir_item')
    log(item)
    list_item = xbmcgui.ListItem(label=item[TITLE])
    # Set additional info for the list item.
    # 'mediatype' is needed for skin to display info for this ListItem correctly.
    list_item.setInfo('video', {TITLE: item[TITLE],
                                'mediatype': 'video'})
    # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
    # Here we use the same image for all items for simplicity's sake.
    # In a real-life plugin you need to set each image accordingly.
    art = {}
    if 'thumb' in item:
        art['thumb'] = item['thumb']
    if 'icon' in item:
        art['icon'] = item['icon']
    if 'fanart' in item:
        art['fanart'] = item['fanart']
    list_item.setArt(art)
    # Set 'IsPlayable' property to 'true'.
    # This is mandatory for playable items!
    # list_item.setProperty('IsPlayable', 'true')
    # Create a URL for a plugin recursive call.
    # Example:
    # plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4
    if WIDGET_ID in item:
        url = get_url(action=LISTING, widget_id=item[WIDGET_ID])
    elif URL in item:
        url = get_url(action=LISTING, url=item[URL])
    else:
        url = get_url(action=LISTING)
    # Add the list item to a virtual Kodi folder.
    # is_folder = False means that this item won't open any sub-list.
    is_folder = True
    # Add our item to the Kodi virtual folder listing.
    xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(param_string):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param param_string: URL encoded plugin param_string
    :type param_string: str
    """
    log('router')
    log(param_string)
    # Parse a URL-encoded param_string to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(param_string))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == LISTING:
            # Display the list of videos in a provided category.
            list_category(params)
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid param_string: {0}!'.format(param_string))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_main_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
