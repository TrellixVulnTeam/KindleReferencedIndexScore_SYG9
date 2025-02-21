# coding: utf-8
import os
import math
import sys
import regex
import urllib2
import urllib2
import httplib
import ssl
import multiprocessing as mp
from socket import error as SocketError
import bs4

def html_adhoc_fetcher(url):
    html = None
    for _ in range(3):
        #opener = urllib2.build_opener()
        try:
            TIME_OUT = 1.0
            #print url, _
            req = urllib2.Request(url, headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.63 Safari/537.36'} )
            html = urllib2.urlopen(req, timeout=TIME_OUT).read()
            pass
        except EOFError, e:
            print('[WARN] Cannot access url with EOFError, try number is...', e, _, url, mp.current_process() )
            continue
        except urllib2.URLError, e:
            print('[WARN] Cannot access url with urllib2.URLError, ', e, 'reason', e.reason, 'num', _, url, mp.current_process() )
            continue
        except urllib2.HTTPError, e:
            print('[WARN] Cannot access url with urllib2.httperror, try number is...', e, _, url, mp.current_process() )
            continue
        except ssl.SSLError, e:
            print('[WARN] Cannot access url with ssl error, try number is...', e, _, url, mp.current_process() )
            continue
        except ssl.CertificateError, e:
            print('[WARN] Cannot access url with ssl error, try number is...', e, _, url, mp.current_process() )
            continue 
        except httplib.BadStatusLine, e:
            print('[WARN] Cannot access url with BadStatusLine, try number is...', e, _, url, mp.current_process() )
            continue
        except httplib.IncompleteRead, e:
            print('[WARN] Cannot access url with IncompleteRead, try number is...', e, _, url, mp.current_process() )
            continue
        except SocketError, e:
            print('[WARN] Cannot access url with SocketError, try number is...', e, _, url, mp.current_process() )
            continue
        except UnicodeEncodeError, e:
            print('[WARN] Cannot access url with UnicodeEncodeError, try number is...', e, _, url, mp.current_process() )
            continue
        break
    if html == None:
        return None
    line = html.replace('\n', '^A^B^C')
    line = regex.sub('<!--.*?-->', '',  line)
    line = regex.sub('<style.*?/style>', '',  line)
    html = regex.sub('<script.*?/script>', '', line ).replace('^A^B^C', ' ')
    try: 
        soup = bs4.BeautifulSoup(html)
    except:
        print "HTMLのパースに失敗しました"
        return None
    title = (lambda x:unicode(x.string) if x != None else 'Untitled')( soup.title )
    anchor = ' '.join([a.text for a in soup.findAll('a') ])
    urls = []
    for a in soup.find_all('a', href=True):
        urls.append( a.get('href').encode('utf-8') )
    """ アンカータグ a-tagを削除 """
    for t in soup.findAll("a"):
        t.extract()
    # soup.renderContents()
    body = (lambda x:x.text if x != None else "" )(soup.find('body') )
    return title, anchor, urls, body
#soup = bs4.BeautifulSoup(html)
import feedparser
import sys
import regex
import urllib
# ポジティブIDF辞書作成モード
if '-gq' in sys.argv:
    import json
    import plyvel 
    db = plyvel.DB("正しい日本語.ldb", create_if_missing=True, error_if_exists=False)
    nps = filter(lambda x:x!=('', ), [tuple(l.split('\t') ) for l in open('./negative_positive.dat').read().split('\n')] )
    #print nps
    for line in nps:
        line = line[1] #""" 一番目のインデックスは、用法が含まれたデータになっているはず """
        encoded = urllib.quote(line)
        reses = html_adhoc_fetcher('https://www.google.co.jp/search?q=' + encoded + '&num=50')
        if reses == None:
            continue
        title  = reses[0]
        anchor = reses[1]
        urls   = reses[2]
        urls   = filter(lambda x:'google' not in x and 'pdf' not in x, filter(lambda x: regex.match('^http', x) , urls)  )
        body   = reses[3]
        for enum, url in enumerate(urls):
            if db.get(url) != None:
                print enum, line, "すでに解析済みです"
                continue
            reses2 = html_adhoc_fetcher(url)
            if reses2 == None:
                print "htmlの取得ができませんでした"
                db.put(url, "___error1___")
                continue
            title2  = reses2[0].encode('utf-8')
            anchor2 = reses2[1]
            urls2   = reses2[2]
            body2   = reses2[3].encode('utf-8')
            """ 正しい情報に書き換え """
            for np in nps:
                n, p = np
                body2= regex.sub(n, p, body2)
            if line in body2:
                print enum, line, "scripting 完了です"
                db.put(url, body2.replace(line, "<<<" + line + ">>>") )
if '-gd' in sys.argv:
    import plyvel
    import json
    db = plyvel.DB('正しい日本語.ldb')
    for k, v in db:
        print v

