# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale per casacinema
# ------------------------------------------------------------
import re
import urlparse

from channelselector import thumb, get_thumb
from core import scrapertools, scrapertoolsV2, httptools, tmdb, support
from core.item import Item
from platformcode import logger, config
from specials import autoplay

__channel__ = "casacinema"
host = config.get_channel_url(__channel__)
IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'wstream', 'speedvideo']
list_quality = ['HD', 'SD']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'casacinema')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'casacinema')

headers = [['Referer', '%s/genere/serie-tv' % host]]


def mainlist(item):
    logger.info("kod.casacinema mainlist")

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = [Item(channel=item.channel,
                     title="[B]Film[/B]",
                     action="peliculas",
                     extra="movie",
                     url="%s/category/film" % host),
                Item(channel=item.channel,
                     title="[B]Film - HD[/B]",
                     action="peliculas",
                     extra="movie",
                     url="%s/?s=[HD]" % host),
                Item(channel=item.channel,
                     title="[B] > Categorie[/B]",
                     action="categorias",
                     extra="movie",
                     url="%s/category/film" % host),
                Item(channel=item.channel,
                     title="[B]Film Sub - Ita[/B]",
                     action="peliculas",
                     extra="movie",
                     url="%s/category/sub-ita" % host),
                Item(channel=item.channel,
                     title="[COLOR blue]Cerca Film...[/COLOR]",
                     action="search",
                     extra="movie",),
                Item(channel=item.channel,
                     title="[B]Serie TV[/B]",
                     extra="tvshow",
                     action="peliculas_tv",
                     url="%s/category/serie-tv" % host),
                Item(channel=item.channel,
                     title="[B]Aggiornamenti Serie TV[/B]",
                     action="update_tv",
                     url="%s/aggiornamenti-serie-tv" % host,
                     extra="tvshow"),
                Item(channel=item.channel,
                     title="[COLOR blue]Cerca Serie TV...[/COLOR]",
                     action="search",
                     extra="tvshow")]

    
    autoplay.show_option(item.channel, itemlist)

    # auto thumb
    itemlist=thumb(itemlist) 

    return itemlist


def newest(categoria):
    logger.info("[casacinema.py] newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "film":
            item.url = host + '/genere/film'
            item.extra = "movie"
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def search(item, texto):
    logger.info("[casacinema.py] " + item.url + " search " + texto)

    item.url = host + "/?s=" + texto

    try:
        if item.extra == "tvshow":
            return peliculas_tv(item)
        if item.extra == "movie":
            return peliculas(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def peliculas(item):
    logger.info("kod.casacinema peliculas")
    #import web_pdb;web_pdb.set_trace()
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    logger.info('DATA=' +data)

    # Estrae i contenuti 
    patron = '<li><a href="([^"]+)"[^=]+="([^"]+)"><div>\s*<div[^>]+>(.*?)<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        cleantitle = re.sub(r'[-–]*\s*[Ii]l [Ff]ilm\s*[-–]*?', '', title).strip()
        cleantitle = cleantitle.replace('[HD]', '').strip()

        year = scrapertools.find_single_match(title, r'\((\d{4})\)')
        infolabels = {}
        if year:
            cleantitle = cleantitle.replace("(%s)" % year, '').strip()
            infolabels['year'] = year

        scrapedplot = ""
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 title=title,
                 text_color="azure",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=cleantitle,
                 show=cleantitle,
                 plot=scrapedplot,
                 infoLabels=infolabels,
                 extra=item.extra,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    ## Paginación
    next_page = scrapertools.find_single_match(data, '<li><a href="([^"]+)"\s>Pagina')

    if next_page != "" and not 'HD'in item.title:
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR blue]" + config.get_localized_string(30992) + " >[/COLOR]",
                 url=next_page,
                 extra=item.extra,
                 thumbnail=get_thumb('next.png')))

    return itemlist


def peliculas_tv(item):
    logger.info("kod.casacinema peliculas")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = '<li><a href="([^"]+)"[^=]+="([^"]+)"><div>\s*<div[^>]+>(.*?)<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        cleantitle = re.sub(r'[-–]*\s*[Ss]erie [Tt]v\s*[-–]*?', '', title).strip()
        cleantitle = cleantitle.replace('[HD]', '').replace('[SD]', '').strip()

        year = scrapertools.find_single_match(title, r'\((\d{4})\)')
        infolabels = {}
        if year:
            cleantitle = cleantitle.replace("(%s)" % year, '').strip()
            infolabels['year'] = year

        scrapedplot = ""
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 contentType="tvshow",
                 title=title,
                 text_color="azure",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=cleantitle,
                 show=cleantitle,
                 plot=scrapedplot,
                 infoLabels=infolabels,
                 extra=item.extra,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    ## Paginación
    next_page = scrapertools.find_single_match(data, '<li><a href="([^"]+)"\s>Pagina') ### <- Regex rimosso spazio - precedente <li><a href="([^"]+)" >Pagina

    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas_tv",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 extra=item.extra,
                 thumbnail=get_thumb('next.png')))

    return itemlist

def categorias(item):
    logger.info("kod.casacinema categorias")

    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    # Narrow search by selecting only the combo
    bloque = scrapertools.find_single_match(data, 'Categorie(.*?)</ul>')

    # The categories are the options for the combo
    patron = '<a href="(.*?)">(.*?)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 extra=item.extra,
                 url=urlparse.urljoin(host, scrapedurl)))

    return itemlist

def update_tv(item):
    logger.info("Aggiornamenti serie tv")
    itemlist=[]
    data = httptools.downloadpage(item.url, headers=headers).data
    logger.info('DATA=' + data)

    patron='<h2>([^<]+)</h2>(.*?)</ul'
    matches=re.compile(patron,re.DOTALL).findall(data)
    for sc_date,sc_block in matches:
        itemlist.append(Item(channel=item.channel,
                             title="[B]%s[/B]"%sc_date,
                             text_color="azure"))

        patron1='<li><a href="([^"]+)"\sdata-thumbnail="([^"]+)">.*?class="title">([^<]+)<.*?class="episode".*?>([^<]+)<'
        matches1=re.compile(patron1,re.DOTALL).findall(sc_block)
        for sc_url,sc_thumb,sc_title,sc_newepisode in matches1:
            cleantitle=sc_title.replace("[HD]","").strip()
            infolabels={}
            itemlist.append(Item(channel=item.channel,
                 action="episodios",
                 contentType="tvshow",
                 title="%s (%s)"%(cleantitle,sc_newepisode),
                 url=sc_url,
                 thumbnail=sc_thumb,
                 fulltitle=cleantitle,
                 show=cleantitle,
                 extra=item.extra,
                 infoLabels=infolabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist




def episodios(item):
    def load_episodios(html, item, itemlist, lang_title):
        patron = '.*?<a href="[^"]+"[^o]+ofollow[^>]+>[^<]+</a><(?:b|/)[^>]+>'
        matches = re.compile(patron).findall(html)
        for data in matches:
            # Estrae i contenuti
            scrapedtitle = scrapertoolsV2.htmlclean(re.sub(r'(<a [^>]+>)*(<\/a>.*)*(Speedvideo)*', '', data)).strip()
            if scrapedtitle != 'Categorie':
                scrapedtitle = scrapedtitle.replace('&#215;', 'x')
                scrapedtitle = scrapedtitle.replace('×', 'x')
                scrapedtitle = scrapedtitle.replace(';', '')
                itemlist.append(
                    Item(channel=item.channel,
                         action="findvideos",
                         contentType="episode",
                         title="[COLOR azure]%s[/COLOR]" % (scrapedtitle + " (" + lang_title + ")"),
                         url=data,
                         thumbnail=item.thumbnail,
                         extra=item.extra,
                         fulltitle=scrapedtitle + " (" + lang_title + ")" + ' - ' + item.show,
                         show=item.show))

    logger.info("[casacinema.py] episodios")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    data = scrapertools.decodeHtmlentities(data)
    data = scrapertools.find_single_match(data, '<p>(?:<strong>|)(.*?)<div id="disqus_thread">')

    lang_titles = []
    starts = []
    patron = r"Stagione.*?(?:ITA|\d+)"
    matches = re.compile(patron, re.IGNORECASE).finditer(data)
    for match in matches:
        season_title = match.group()
        if season_title != '':
            lang_titles.append('SUB ITA' if 'SUB' in season_title.upper() else 'ITA')
            starts.append(match.end())

    i = 1
    len_lang_titles = len(lang_titles)

    while i <= len_lang_titles:
        inizio = starts[i - 1]
        fine = starts[i] if i < len_lang_titles else -1

        html = data[inizio:fine]
        lang_title = lang_titles[i - 1]

        load_episodios(html, item, itemlist, lang_title)

        i += 1

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios" + "###" + item.extra,
                 show=item.show))

    return itemlist


def findvideos(item):
    logger.info("kod.casacinema findvideos")

    data = item.url if item.extra == "tvshow" else httptools.downloadpage(item.url, headers=headers).data

    html = httptools.downloadpage(data).data
    patron = '"http:\/\/shrink-service\.it\/[^\/]+\/[^\/]+\/([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(html)

    for url in matches:
        if url is not None:
            data = data
        else:
            continue
    
    return support.server(item, data=data)
