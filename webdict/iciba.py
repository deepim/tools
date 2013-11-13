#!/usr/bin/env python

import BeautifulSoup
import urllib2
import urlparse
import re
import time
import sys
import logging
import codecs

class IcibaWebDict(object):

    def __init__(self,logger):
        self.logger = logger
        self.metaRE = re.compile('<meta[^>]*?url=(.*?)["\']', re.IGNORECASE)

    def removeTag(self,soup, tagname):
        for tag in soup.findAll(tagname):
            #contents = tag.contents
            #parent = tag.parent
            tag.extract()

    def get_hops(self,url):
        redirect_re = self.metaRE
        hops = []
        while url:
            if url in hops:
                url = None
            else:
                hops.insert(0, url)
                try:
                    response = urllib2.urlopen(url)
                except:
                    return None
                if response.geturl() != url:
                    hops.insert(0, response.geturl())
                # check for redirect meta tag
                match = redirect_re.search(response.read())
                if match:
                    url = urlparse.urljoin(url, match.groups()[0].strip())
                else:
                    url = None
        return hops

    def queryHanZi(self,pdom):
        #extract input word
        parts0 = pdom.findAll('div', attrs={'class':'hanzi01'})
        assert len(parts0) == 1
        mnc= parts0[0].string

        #extract traditional character
        parts1 = pdom.findAll('div', attrs={'class':'hanzi02_shang'})
        assert len(parts1) == 1
        blks = parts1[0].findAll('div', attrs={'class':'hanzi022'})
        big5= blks[0].string

        parts2 = pdom.findAll('div', attrs={'class':'jieshi'})
        assert len(parts2) == 1

        #extract pinyin
        py=[]
        blks1 = parts2[0].findAll('div', attrs={'class':'js12'})
        for blk in blks1:
            py.append(blk.string)

        #extract pos
        #notice that: there are several pos for one py on iciba website
        pos=[]
        blks2 = parts2[0].findAll('ul', attrs={'class':'js21'})
        for blk in blks2:
            subblks = blk.findAll('li')
            subposSet=set([])
            for sblk in subblks:
                posline = sblk.contents[-1]
                poslineA = re.split(u'[()\uff08\uff09]',posline)
                if len(poslineA) > 1:
                    subposSet.add(poslineA[1])
            pos.append("|".join(subposSet))

        assert len(py) == len(pos)

        pospy=[]
        for idx in range(len(py)):
            pospy.append("%s-%s" % (py[idx],pos[idx]))

        return mnc,big5,", ".join(pospy)

    def queryCiZu(self,pdom):

        #extract input word
        parts0 = pdom.findAll('div', attrs={'class':'js11'})
        assert len(parts0) == 1
        mnc= parts0[0].string
        #print mnc

        #extract pinyin
        parts1 = pdom.findAll('div', attrs={'class':'js12'})
        assert len(parts1) == 1
        py= "".join(parts1[0].contents[0].contents)
        #print py

        #extract pos
        parts2 = pdom.findAll('ul', attrs={'class':'js21'})
        assert len(parts2) == 1
        blks = parts2[0].findAll('li')
        posBlk= blks[0]
        self.removeTag(posBlk,'span')
        self.removeTag(posBlk,'br')
        poslines = posBlk.contents
        poslines = [pline.strip() for pline in poslines if pline.strip() != '\n' and pline.strip() != '']
        posSet=set([])
        for posline in poslines:
            poslineA = re.split(u'[()\uff08\uff09]',posline)
            if len(poslineA) > 1:
                posSet.add(poslineA[1])
        posStr = "|".join(posSet)
        #print posStr
        return mnc, py, posStr

    def queryChengYu(self,pdom):

        #extract input word
        parts0 = pdom.findAll('div', attrs={'class':'cy11'})
        assert len(parts0) == 1
        mnc= parts0[0].string
        #print mnc

        #extract pinyin
        parts1 = pdom.findAll('div', attrs={'class':'cy12'})
        assert len(parts1) == 1
        py= parts1[0].string

        return mnc,py

    def repeatOpen(self,addr):
        isRedo = True
        page = None
        while isRedo:
            try:
                page = urllib2.urlopen(addr)
                isRedo = False
            except:
                pass
            time.sleep(0.01)
        return page

    def query(self,word):
        urladdr = 'http://hanyu.iciba.com/hy/%s' % word
        urladdr = urladdr.encode('utf8')
        self.logger.info("Input Url:%s" % urladdr)
        realurl = self.get_hops(urladdr)
        if realurl == None:
            self.logger.info("Cannot Found %s" % urladdr)
            return None

        self.logger.info("Real Url:%s" % realurl[0])
        urlA = re.split('/',realurl[0])
        page = self.repeatOpen(realurl[0])
        if page == None:
            self.logger.info("Cannot Open Url %s" % realurl[0])
            return None
        #page = urllib2.urlopen(realurl[0])
        pdom = BeautifulSoup.BeautifulSoup(page.read())

        if urlA[-2] != 'hanzi' and urlA[-2] !='cizu' and urlA[-2] != 'chengyu':
            self.logger.info("Cannot find this word")
            return None

        rstA=[]
        if urlA[-2] == 'hanzi':
            mnc,big5,pospy = self.queryHanZi(pdom)
            self.logger.info("Input:%s, Traditional Charater:%s, Possible PY-POS:%s, Type:HanZi" % (mnc,big5,pospy))
            rstA.append("Type:HanZi")
            rstA.append("MNC:%s" % mnc)
            rstA.append("Big5:%s" % big5)
            rstA.append("POSPY:%s" % pospy)
        elif urlA[-2] == 'cizu':
            mnc,py,pos = self.queryCiZu(pdom)
            self.logger.info("Input:%s, PY:%s, POS:%s, Type:CiZu" % (mnc,py,pos))
            rstA.append("Type:CiZu")
            rstA.append("MNC:%s" % mnc)
            rstA.append("PY:%s" % py)
            rstA.append("POS:%s" % pos)
        elif urlA[-2] == 'chengyu':
            mnc,py = self.queryChengYu(pdom)
            self.logger.info("Input:%s, PY:%s, Type:ChengYu" % (mnc,py))
            rstA.append("Type:ChengYu")
            rstA.append("MNC:%s" % mnc)
            rstA.append("PY:%s" % py)
        else:
            self.logger.info("Unkown URL")

        time.sleep(0.01)
        return rstA

    def queryWordsFromFile(self,finName,foutName):
        f = codecs.open(finName,'r',encoding='utf8')
        fout = codecs.open(foutName,'w',encoding='utf8')
        for line in f:
            line = line.strip()
            rst = self.query(line)
            if rst != None:
                fout.write("%s\n" % ("\t\t".join(rst)))
        f.close()
        fout.close()


if __name__=="__main__":
    if len(sys.argv) != 3:
        print "Usage:./iciba.py inputfile outfile"
        sys.exit(-1)

    logger = logging.getLogger()
    formatter = logging.Formatter('[%(filename)s:%(lineno)d] - [%(asctime)s] : *%(levelname)s* | (%(funcName)s) %(message)s', '%Y-%m-%d %H:%M:%S',)
    file_handler = logging.FileHandler('iciba.log','w')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)

    iciba = IcibaWebDict(logger)
    iciba.queryWordsFromFile(sys.argv[1],sys.argv[2])
