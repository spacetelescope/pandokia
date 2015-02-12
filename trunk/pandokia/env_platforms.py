#! /bin/env python
"""This module contains mappings to construct platform-specific
identifying information that will be used by the EnvGetter to apply
the appoprirate specific subsections of the pdk_environment files.

By its nature, this information is expected to be site-specific.
Users may need or wish to tailor it for their specific test situation."""

import platform

#Hierarchy: this is an ordered list that specifies the order
#in which the subsections will be applied
hierarchy = ['os',
             'osver',
             'cpu',
             'hostname']

#cpu translation: this dict normalizes non-standard spellings.
#Use it with cpudict.get(processor, processor) to return the key
#unchanged if it's not present in the dictionary.
cpudict = dict(i386='x86',
               i686='x86')

class PlatformType(object):
    """Base class from which specific sub-classes that need special
    handling can be instantiated."""

    def __init__(self):
        """Constructor takes no arguments because it will call platform
        routines."""
        #Items we use directly
        self.os = platform.system().lower()
        self.osver = None
        self.cpu = None
        self.hostname = platform.node().split('.')[0]
        

        #Items that will be used to construct the rest
        self.processor = platform.processor().lower()
        self.uname = [x.lower() for x in platform.uname()]
        self.dist = [x.lower() for x in platform.dist()]
        self.arch = platform.architecture()[0].lower()

        #Construct the cpu
        self.makecpu()

        #Construct the osver
        self.makeosver()

    def makecpu(self):
        self.cpu = cpudict.get(self.processor,
                               self.processor)
        if self.os in ['sunos']:
            self.cpu = ''.join([self.cpu, self.arch])

    def makeosver(self):
        if self.os in ['linux']:
            #Toss subrelease
            ver= self.dist[1].split('.')[0]
            self.osver=''.join([self.dist[0],ver])

        if self.os in ['darwin']:
            #Toss subrelease
            ver=self.uname[2].split('.')[0]
            self.osver=''.join([self.uname[0],ver])

        if self.os in ['sunos']:
            #Toss superrelease
            ver=self.uname[2].split('.')[1]
            self.osver=''.join([self.uname[0],ver])

    def __iter__(self):
        """Iterates through the relevant attributes in the order given by
        the hierarchy, and returns the section name. This is expected to
        be the primary interface used by envgetter."""
        for i, item in enumerate(hierarchy):
            yield self.getsecname(i)
            
    def query(self):
        """For debugging purposes"""
        print self.os
        print self.osver
        print self.cpu
        print self.hostname

    def getsecname(self, index):
        """The real UI: returns the section name corresponding to the ith
        element of the ordered list. This section name will be matched to
        the environment file."""
        item=hierarchy[index]
        secname="%s=%s"%(item,self.__getattribute__(item))
        return secname

if __name__ == '__main__':
    p=PlatformType()
    for i in range(4):
        print p.getsecname(i)
