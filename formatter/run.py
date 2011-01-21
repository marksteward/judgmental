#!/usr/bin/python
"""
Main script to run to generate all static content

Command-line options:

  --no-analyse
       Does not do the analysis phase (and so does not require the judgmental.db file to be deleted in advance)

  --no-crossreference
       Does not do the crossreferencing

  --no-convert
       Does not generate any html output

  --slow
       Refuses to use multiprocessing

  --files
       Works only on the files which follow
"""

import sys
import os

from fakepool import Pool as FakePool
import analyse
import crossreference
import convert
from general import *

# Can we speed things up by using multiple cores?
global multi_enabled
try:
    from multiprocessing.pool import Pool
    print "Multiprocessing enabled (Python 2.6/3 style)"
    multi_enabled = True
except ImportError:
    try:
        from processing.pool import Pool
        print "Multiprocessing enabled (Python 2.5 style)"
        multi_enabled = True
    except ImportError:
        print "Multiprocessing disabled"
        multi_enabled = False

# standard filenames
file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
input_dir = os.path.join(file_dir, "../../bailii")
output_dir = os.path.join(file_dir, "../../public_html/judgments")
logfile_name = os.path.join(file_dir, "../../errors.log")
dbfile_name = os.path.join(file_dir, "../../judgmental.db")

# default options
use_multiprocessing = multi_enabled
do_analyse = True
do_crossreference = True
do_convert = True
run_on_all_files = True
file_list = []

# parse command-line options
arguments = sys.argv[1:]
while len(arguments)>0:
    a = arguments[0]
    arguments = arguments[1:]
    if a == "--no-analyse" or a == "--no-analysis":
        print "Option --no-analyse selected"
        do_analyse = False
    elif a == "--no-crossreference":
        print "Option --no-crossreference selected"
        do_crossreference = False
    elif a == "--no-convert":
        print "Option --no-convert selected"
        do_convert = False
    elif a == "--slow":
        print "Option --slow selected"
        use_multiprocessing = False
    elif a == "--files":
        print "Using file list supplied"
        run_on_all_files = False
        while len(arguments)>0 and (arguments[0][:2] != "--"):
            file_list.append(arguments[0])
            arguments = arguments[1:]
    else:
        print "FATAL: I don't understand those command-line arguments"
        quit()

# one argument combination is stupid
if (do_analyse, do_crossreference, do_convert) == (True,False,True):
    print "FATAL: You're planning to generate a database without crossreferencing information in. That won't work."
    quit()

# default is to use all files
print "Generating file list"
if run_on_all_files:
    for (path,dirs,files) in os.walk(input_dir):
        for f in files:
            if f[-5:] == ".html":
                file_list.append(os.path.join(path,f))

# how should we despatch things in parallel?
def pool(multi=use_multiprocessing):
    if multi:
        print "Using multiprocessing"
        p = Pool()
        p.genuinely_parallel = True
    else:
        print "Not using multiprocessing"
        p = FakePool()
        p.genuinely_parallel = False
    return p

# open logfile
logfile = open(logfile_name,'w')

# some details
broadcast(logfile,"File list contains %d files"%len(file_list))

# analysis stage
if do_analyse:
    analyse.analyse(file_list=file_list,dbfile_name=dbfile_name,logfile=logfile,process_pool=pool())

# crossreference stage
### should we ban multiprocessing?
if do_crossreference:
    crossreference.crossreference(file_list=file_list,dbfile_name=dbfile_name,logfile=logfile,process_pool=pool())

# convert stage
if do_convert:
    convert.convert(file_list=file_list,dbfile_name=dbfile_name,logfile=logfile,output_dir=output_dir,process_pool=pool())

# close logfile
logfile.close()