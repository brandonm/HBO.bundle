import re

NAME = 'HBO'
ART = 'art-default.jpg'
ICON = 'icon-default.png'
NEXT = 'icon-next.png'

BASE_URL = 'http://hbogo.com'
CATALOG_URL = 'http://catalog.lv3.hbogo.com'

# Main Menu
NAV_URL = CATALOG_URL + '/apps/mediacatalog/rest/navigationBarService/HBO/navigationBar/NO_PC'
# Main category page called from main menu to load landing bar on page
LANDING_URL = CATALOG_URL + '/apps/mediacatalog/rest/landingService/HBO/landing/%s'
# Category pages to filter category page (A-Z, Genre)
QUICKLINKS_URL = CATALOG_URL + '/apps/mediacatalog/rest/quicklinkService/HBO/quicklink/%s'
# HBO uses a couple different XML layouts for pages (ex: Bundle = TV Seasons)
BUNDLE_URL = 'http://catalog.lv3.hbogo.com/apps/mediacatalog/rest/productBrowseService/HBO/bundle/%s'
CATEGORY_URL = 'http://catalog.lv3.hbogo.com/apps/mediacatalog/rest/productBrowseService/HBO/category/%s'

NAMESPACE = {'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

# Page used to pull up video
STREAM_URL = 'http://www.hbogo.com/#series/video&assetID=%s?videoMode=embeddedVideo?showSpecialFeatures=false&provider=%s'

# Dont show this items on the main menu
MENU_SKIP = [ 'Free', 'Home']

# Providers that we have setup.
PROVIDERS = {"Astound":"astound","AT&T U-verse":"att","Atlantic Broadband":"atlantic_broadband","ATMC":"atmc","BendBroadband":"bend","Blue Ridge Communications":"blue_ridge","Bright House Networks":"bright_house","Buckeye CableSystem":"buckeye","Burlington Telecom":"burlington","Cable ONE":"cable_one","CenturyLink Prism":"centrylink","Charter":"charter","Cincinnati Bell Fioptics":"cincinnati","Comcast XFINITY":"comcast","Cox":"cox","DIRECTV":"directv","DIRECTV PUERTO RICO":"directv_pr","DISH":"dish","Easton Cable Velocity":"easton","EPB Fiber Optics":"epb_fiber_optics","GCI":"gci","Grande Communications":"grande","GVTC Communications":"gvtc","Hawaiian Telcom":"hawaiian","HBC":"hbc","Home Telecom":"home_telecom","Home Town Cable Plus":"home_town_cable","Hotwire Communications":"hotwire","HTC Digital Cable":"htc","Insight Communications":"insight","JEA":"jea","Long Lines":"long_limes","LUS Fiber":"lus","Massillon Cable/Clear Picture":"massillon","Mediacom":"mediacom","MetroCast":"metrocast","MI-Connection":"mi_connection","Midcontinent Communications":"midcontinent","Nex-Tech":"nex_tech","OpenBand Multimedia":"openband","Optimum":"optimum","RCN":"rcn","Service Electric Broadband":"service_electric_broadband","Service Electric Cable TV":"service_electric_cable_tv","Service Electric Cablevision":"service_electric_cablevision","Suddenlink":"suddenlink","Time Warner Cable":"timewarner","Verizon FiOS":"verizon","Wave Broadband":"wave","WOW!":"wow"}

####################################################################################################
def Start():

    Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
    Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

    ObjectContainer.title1 = R(NAME)
    ObjectContainer.art = R(ART)
    ObjectContainer.view_group = "InfoList"

    DirectoryObject.art = R(ART)
    DirectoryObject.thumb = R(ICON)

    EpisodeObject.thumb = R(ICON)
    EpisodeObject.art = R(ART)

    #HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:16.0) Gecko/20100101 Firefox/16.0'

####################################################################################################
# Loads HBOGO menu from home page.
@handler('/video/hbo', NAME, art = ART, thumb = ICON)
def MainMenu():

    oc = ObjectContainer(view_group = "List")

    xml = XML.ElementFromURL(NAV_URL)

    for item in xml.xpath('//response/body/navBarelementResponses'):
        title = item.xpath('title')[0].text
        landingTypeCode = item.xpath('landingTypeCode')[0].text

        if not title in MENU_SKIP:
            oc.add(DirectoryObject(
                key = Callback(QuickMenu, title = title, landingTypeCode = landingTypeCode),
                title = title))

    #oc.add(SearchDirectoryObject(identifier="com.plexapp.plugins.showtime", title = "Search", prompt = "Search", thumb = ICON_SEARCH))

    # Preferences
    oc.add(PrefsObject(title = 'Preferences'))

    return oc

####################################################################################################
# Second pages after home page.  This will show filters for the main categories
@route('/video/hbo/{landingTypeCode}')
def QuickMenu(title, landingTypeCode):

    oc = ObjectContainer(title2 = title, view_group = "List")

    xml = XML.ElementFromURL(QUICKLINKS_URL % landingTypeCode)

    # To be added later... They list new stuff etc on main category pages.
    #oc.add(DirectoryObject(
    #    key = Callback(LandingMenu, title = 'Landing', url = LANDING_URL % landingTypeCode),
    #    title = 'Landing'))

    parents = []

    for item in xml.xpath('//response/body/quicklinks/quicklinkElement'):
        itemTitle = item.xpath('displayName')[0].text
        try: itemUrl = item.xpath('uri')[0].text
        except: itemUrl = None

        # If the page has additional options used to filter (Genre: Action, Drama, ...)
        if itemUrl == None:
            oc.add(DirectoryObject(
                key = Callback(SubQuickMenu, title = itemTitle, landingTypeCode = landingTypeCode, parent = itemTitle),
                title = itemTitle))
        else:
            oc.add(DirectoryObject(
                key = Callback(BrowseMenu, title = itemTitle, landingTypeCode = landingTypeCode, url = itemUrl),
                title = itemTitle))

    return oc

####################################################################################################
# Filters with additional options used to filter (Genre: Action, Drama, ...)
@route('/video/hbo/{landingTypeCode}/filter/{parent}')
def SubQuickMenu(title, landingTypeCode, parent):

    oc = ObjectContainer(title2 = title, view_group = "List")

    xml = XML.ElementFromURL(QUICKLINKS_URL % landingTypeCode)

    for item in xml.xpath('//response/body/quicklinks/quicklinkElement/quicklinkElements'):
        itemParent = item.xpath('parentName')[0].text
        itemTitle = item.xpath('displayName')[0].text
        itemUrl = item.xpath('uri')[0].text

        if parent in itemParent:
            oc.add(DirectoryObject(
                key = Callback(BrowseMenu, title = itemTitle, landingTypeCode = landingTypeCode, url = itemUrl),
                title = itemTitle))
    return oc

####################################################################################################
# This function will display the available movies or shows from the filters
@route('/video/hbo/{landingTypeCode}/browse')
def BrowseMenu(title, landingTypeCode, url):

    oc = ObjectContainer(title2 = title)

    xml = XML.ElementFromURL(url)
    type = xml.xpath('//body/@xsi:type', namespaces=NAMESPACE)[0]

    if type == 'productBrowseResponse':
        #Movies
        for item in xml.xpath('//response/body/productResponses/featureResponse'):
            # Can be movies or tv episode not in the normal tv show > season > ep setup.
            movieTKey =  item.xpath('TKey')[0].text
            movieUrl = STREAM_URL % (movieTKey, PROVIDERS[ Prefs['provider']])
            movieTitle = item.xpath('title')[0].text
            movieSummary = item.xpath('summary')[0].text
            movieYear = int(item.xpath('year')[0].text)

            for image in item.xpath('imageResponses'):
                if "SLIDESHOW" in image.xpath('mediaSubType')[0].text:
                    movieThumb = image.xpath('resourceUrl')[0].text

            for video in item.xpath('videoResponses'):
                if "WEB_ADAPTIVE" in video.xpath('mediaSubType')[0].text:
                    if "ENG" in video.xpath('mediaVersion')[0].text:
                        videoTKey = video.xpath('TKey')[0].text
                        videoRuntime = int(video.xpath('runtime')[0].text) * 1000

            oc.add(MovieObject(
                url = movieUrl,
                title = movieTitle,
                summary = movieSummary,
                thumb = movieThumb,
                art = movieThumb,
                duration = videoRuntime,
                year = movieYear
            ))


        # TV Show
        #for item in xml.xpath('//response/body/productResponses/bundleResponse'):
            #list what?

    # Used for main Series menu (TV Show > Seasons > Show)
    elif type == 'categoryBrowseResponse':
        for item in xml.xpath('//response/body/categoryResponses/bundleCategory'):

            showTKey =  item.xpath('TKey')[0].text
            showTitle = item.xpath('title')[0].text
            showSummary = item.xpath('summary')[0].text

            for image in item.xpath('imageResponses'):
                if "SLIDESHOW" in image.xpath('mediaSubType')[0].text:
                    showThumb = image.xpath('resourceUrl')[0].text

            oc.add(TVShowObject(
                key = Callback(SeasonsMenu, title = showTitle, landingTypeCode = landingTypeCode, tkey = showTKey),
                rating_key = showTitle,
                title = showTitle,
                summary = showSummary,
                thumb = showThumb,
                art = showThumb
            ))


    #elif type == 'adminPackageResponse':


    return oc

####################################################################################################
# This function will display the Landing page content (main page for category)
@route('/video/hbo/{landingTypeCode}/landing')
def LandingMenu(title, landingTypeCode, url):

    oc = ObjectContainer(title2 = title)

    return oc

####################################################################################################
# This function will display the show seasons menu
@route('/video/hbo/{landingTypeCode}/{title}/seasons')
def SeasonsMenu(title, landingTypeCode, tkey):

    oc = ObjectContainer(title2 = title)

    xml = XML.ElementFromURL(CATEGORY_URL % tkey)

    for season in xml.xpath('//response/body/productResponses/bundleResponse'):
        # list tv shows
        showTitle = season.xpath('seriesName')[0].text
        seasonTitle = season.xpath('title')[0].text
        seasonSummary = season.xpath('summary')[0].text
        seasonTKey = season.xpath('TKey')[0].text
        seasonNum = int(season.xpath('seasonNbr')[0].text)
        episodeCount = int(season.xpath('episodeCount')[0].text)

        for image in season.xpath('imageResponses'):
            if "SLIDESHOW" in image.xpath('mediaSubType')[0].text:
                seasonThumb = image.xpath('resourceUrl')[0].text

        oc.add(SeasonObject(
            key = Callback(EpisodesList, title = seasonTitle, seasonNum = seasonNum, tkey = seasonTKey, landingTypeCode = landingTypeCode),
            rating_key = seasonTitle,
            show = showTitle,
            title = seasonTitle,
            index = seasonNum,
            thumb = seasonThumb,
            art = seasonThumb,
            episode_count = episodeCount
        ))

    oc.objects.sort(key = lambda obj: obj.index)

    return oc

####################################################################################################
# This function will display the episodes in a season
@route('/video/hbo/{landingTypeCode}/{title}/{seasonNum}/episodes')
def EpisodesList(title, seasonNum, tkey, landingTypeCode):
    oc = ObjectContainer(title2 = title)

    xml = XML.ElementFromURL(BUNDLE_URL % tkey)

    for item in xml.xpath('//response/body/productResponses/bundleResponse'):

        tkey =  item.xpath('TKey')[0].text
        show = item.xpath('seriesName')[0].text
        season = int(item.xpath('seasonNbr')[0].text)
        absolute_index = int(item.xpath('episodeCount')[0].text)

        for art in item.xpath('imageResponses'):
            if "SLIDESHOW" in art.xpath('mediaSubType')[0].text:
                art = art.xpath('resourceUrl')[0].text


        for ep in item.xpath('featureResponses'):
            title = ep.xpath('title')[0].text
            summary = ep.xpath('summary')[0].text
            ep_tkey = ep.xpath('TKey')[0].text
            year = int(ep.xpath('year')[0].text)
            index = int(ep.xpath('episodeInSeason')[0].text)

            url = STREAM_URL % (ep_tkey, PROVIDERS[ Prefs['provider']])

            for image in ep.xpath('imageResponses'):
                if "SLIDESHOW" in image.xpath('mediaSubType')[0].text:
                    thumb = image.xpath('resourceUrl')[0].text

            for video in ep.xpath('videoResponses'):
                if "WEB_ADAPTIVE" in video.xpath('mediaSubType')[0].text:
                    if "ENG" in video.xpath('mediaVersion')[0].text:
                        ep_tkey = video.xpath('TKey')[0].text
                        runtime = int(video.xpath('runtime')[0].text) * 1000

            oc.add(EpisodeObject(
                url = url,
                show = show,
                title = title,
                summary = summary,
                season = season,
                index = index,
                absolute_index = absolute_index,
                duration = runtime,
                thumb = thumb,
                art = art))

    if len(oc) == 0:
        return MessageContainer(title, "No Videos.")

    oc.objects.sort(key = lambda obj: obj.index)

    return oc


