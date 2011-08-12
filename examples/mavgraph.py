#!/usr/bin/env python
'''
graph a MAVLink log file
Andrew Tridgell August 2011
'''

import sys, struct, time, os, datetime
import math, re
import pylab, pytz, matplotlib
from math import *

# allow import from the parent directory, where mavlink.py is
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

import mavutil
from mavextra import *

locator = None
formatter = None

def plotit(x, y, fields, colors=[], loc=None):
    '''plot a set of graphs using date for x axis'''
    global locator, formatter
    pylab.ion()
    fig = pylab.figure(num=1, figsize=(12,6))
    ax1 = fig.gca()
    ax2 = None
    xrange = 0.0
    for i in range(0, len(fields)):
        if len(x[i]) == 0: continue
        if x[i][-1] - x[i][0] > xrange:
            xrange = x[i][-1] - x[i][0]
    xrange *= 24 * 60 * 60
    if formatter is None:
        if xrange < 180:
            formatter = matplotlib.dates.DateFormatter('%H:%M:%S')
        else:
            formatter = matplotlib.dates.DateFormatter('%H:%M')
        interval = 1
        intervals = [ 1, 2, 5, 10, 15, 30, 60, 120, 240, 300, 600,
                      900, 1800, 3600, 7200, 5*3600, 10*3600, 24*3600 ]
        for interval in intervals:
            if xrange / interval < 10:
                break
        locator = matplotlib.dates.SecondLocator(interval=interval)
    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(formatter)
    empty = True
    for i in range(0, len(fields)):
        if len(x[i]) == 0:
            print("Failed to find any values for field %s" % fields[i])
            continue
        if i < len(colors):
            color = colors[i]
        else:
            color = 'red'
        (tz, tzdst) = time.tzname
        if axes[i] == 2:
            if ax2 == None:
                ax2 = ax1.twinx()
            ax = ax2
            ax2.xaxis.set_major_locator(locator)
            ax2.xaxis.set_major_formatter(formatter)
        else:
            ax = ax1
        ax.plot_date(x[i], y[i], color=color, label=fields[i],
                     linestyle='-', marker='None', tz=None)
        pylab.draw()
        empty = False
    if empty:
        print("No data to graph")
        return
    if loc is not None:
        pylab.legend(loc=loc)
        pylab.draw()


from optparse import OptionParser
parser = OptionParser("mavgraph.py [options] <filename> <fields>")

parser.add_option("--no-timestamps",dest="notimestamps", action='store_true', help="Log doesn't have timestamps")
parser.add_option("--planner",dest="planner", action='store_true', help="use planner file format")
parser.add_option("--condition",dest="condition", default=None, help="select packets by a condition")
(opts, args) = parser.parse_args()

if len(args) < 2:
    print("Usage: mavlogdump.py [options] <LOGFILES...> <fields...>")
    sys.exit(1)

filenames = []
fields = []
for f in args:
    if os.path.exists(f):
        filenames.append(f)
    else:
        fields.append(f)
msg_types = set()
multiplier = []
field_types = []

colors = [ 'red', 'green', 'blue', 'orange', 'olive', 'black', 'grey' ]

# work out msg types we are interested in
x = []
y = []
axes = []
re_caps = re.compile('[A-Z_]+')
for f in fields:
    caps = set(re.findall(re_caps, f))
    msg_types = msg_types.union(caps)
    field_types.append(caps)
    y.append([])
    x.append([])
    axes.append(1)

def add_data(t, msg, vars):
    '''add some data'''
    mtype = msg.get_type()
    if mtype not in msg_types:
        return
    for i in range(0, len(fields)):
        if mtype not in field_types[i]:
            continue
        f = fields[i]
        if f.endswith(":2"):
            axes[i] = 2
            f = f[:-2]
        v = mavutil.evaluate_expression(f, vars)
        if v is None:
            continue
        y[i].append(v)
        x[i].append(t)

def process_file(filename):
    '''process one file'''
    print("Processing %s" % filename)
    mlog = mavutil.mavlogfile(filename, notimestamps=opts.notimestamps)
    vars = {}
    
    while True:
        msg = mlog.read_match(opts.condition)
        if msg is None: break
        tdays = (msg._timestamp - time.timezone) / (24 * 60 * 60)
        tdays += 719163 # pylab wants it since 0001-01-01
        add_data(tdays, msg, mlog.messages)

for fi in range(0, len(filenames)):
    f = filenames[fi]
    process_file(f)
    plotit(x, y, fields, colors=colors[fi*len(fields):], loc='upper right')
    for i in range(0, len(x)):
        x[i] = []
        y[i] = []
pylab.show()
raw_input('press enter to exit....')
