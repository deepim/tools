#!/usr/bin/env python2

import os
import re
import struct

class RiffData(object):

    def __init__(self,logger):
        self.logger = logger
        self.alignSize = 4

    def validate(self,content):
        fpos=0
        flen = len(content)

        #check file fourcc
        fourcc = struct.unpack_from('<4s',content,fpos)[0]
        fpos +=4
        if fourcc.lower() != "rif4":
            self.logger.error("Not RIF4 File!")
            #return False

        #check file size
        fsize = struct.unpack_from('<I',content,fpos)[0]
        fpos +=4
        if fsize != flen - fpos:
            self.logger.error("Invalid File Size, Wanted:%d, Real:%d" % (fsize,flen-fpos))
            return False

        #check file type
        ftype = struct.unpack_from('<4s',content,fpos)[0]
        fpos +=4

        self.logger.info("File Type FourCC is:%s,File Size:%d,File Type:%s" % (fourcc,fsize,ftype))

        listArray=[]
        listSize = 0
        while fpos < flen:
            subcc = struct.unpack_from('<4s',content,fpos)[0]
            fpos +=4
            subsize = struct.unpack_from('<I',content,fpos)[0]
            fpos +=4
            if subcc.lower() == "list":
                subtype = struct.unpack_from('<4s',content,fpos)[0]
                self.logger.info("LIST FourCC:%s,Size:%d,Type:%s" % (subcc,subsize,subtype))

                listArray.append((fpos,subsize))
                listSize = subsize - 4
                fpos += 4
            else:
                ### Notice: RIF4's Chunk is different with RIFF
                ### No Chunk Type in RIF4
                if subsize % self.alignSize != 0:
                    subalign = self.alignSize - subsize % self.alignSize
                else:
                    subalign = 0

                if len(listArray) > 0:
                    prefix = "|" + len(listArray) * '-'
                else:
                    prefix = ""
                self.logger.info("%sCHUNK FourCC:%s,Size:%d,Align:%d" % (prefix,subcc,subsize,subalign))
                fpos += subsize + subalign
                listSize -= subsize + subalign + 8
            if listSize <= 0 and len(listArray) > 0:
                if listSize != 0:
                    assert(False)
                last = listArray.pop()
                fpos = last[0] + last[1]

        if fpos!=flen:
            self.logger.error("Invalid CHUNK or LIST, Wanted:%d, Reached:%d" % (flen,fpos))


    def process(self,options):
        fh = open(options['input'],'rb')
        content = fh.read()
        fh.close()
        if not self.validate(content):
            return

if __name__=="__main__":

    import sys
    import time
    import logging
    from argparse import ArgumentParser

    parser = ArgumentParser(description='RiffData Tools')
    parser.add_argument("--version",action="version", version="RiffData 0.1")
    parser.add_argument("-i", "--input",action="store", dest="input", default="", help="Input File")
    parser.add_argument("-o", "--output",action="store", dest="output", default="", help="Output File")

    args = parser.parse_args()
    options = vars(args)

    if (options['input'] == ""):
        print "You have to set input file via -i!"
        sys.exit(-1)

    if (options['output'] == ""):
        print "You have to set output file via -o!"
        sys.exit(-1)

    logger = logging.getLogger()
    formatter = logging.Formatter('[%(filename)s:%(lineno)d] - [%(asctime)s] : *%(levelname)s* | (%(funcName)s) %(message)s', '%Y-%m-%d %H:%M:%S',)
    file_handler = logging.FileHandler('riff.log','w')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)

    allStartTP = time.time()
    riffObj = RiffData(logger)
    riffObj.process(options)

    allEndTP = time.time()
    print "RiffData Operation Finished [Time Cost:%0.3f Seconds]" % float(allEndTP-allStartTP)


