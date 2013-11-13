#!/usr/bin/env python2

import os
import re

class RiffData(object):

    def __init__(self,logger):
        self.logger = logger


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

    allEndTP = time.time()
    print "RiffData Operation Finished [Time Cost:%0.3f Seconds]" % float(allEndTP-allStartTP)


