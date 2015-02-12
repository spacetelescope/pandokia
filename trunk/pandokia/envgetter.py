"""Proposed interface:

Initialize:

x=EnvGetter() or
x=EnvGetter(context='irafx') and/or
x=EnvGetter(defdict=something_besides_os_dot_environ)

Get dictionary containing environment,
  including all parent and merged with os.environ:

foo=x.envdir('/some/fully/specified/directory/')

Populate the relevant information without returning a dictionary:
x.populate('/some/fully/specified/directory/')

Write the tcas:
x.export('/some/fully/specified/directory',format='tca',fh=fh, full=False)

Export the environment as a pdk_environment file:
x.export('/some/fully/specified/directory',format='env',fh=fh, full=False)

If either .envdir or .populate have been called, you can also:

Obtain the location of the top of the tree:
top=x.gettop()

The top of the tree is defined by the presence of a file named pandokia_top.
This file is not read; it's just detected. If it is never detected, it will
go all the way to the top of the file system.
"""
import os, sys, re
import ConfigParser
from pandokia.env_platforms import PlatformType

import pandokia.common as common

#Common variables used by both classes:

#Name of default environment files
efname='pdk_environment'

#Filename marking the top of a test tree
ttop='pandokia_top'

#Patterns pertinent to substitutions:

pat={'envpat' : re.compile('\${?([\w]*?)}?(?:[\\/:]|$)'),
     #Matches an environment variable that
     # starts with a $
     # optionally followed by a {
     # contains any number of alphanumerics or _
     # optionally followed by a }
     # terminated by a \ (for windows) / (for *nix) : (for paths)
     #    or the end of the string
     # Only the name of the environment variable will be taken.
     
     'pathkey': re.compile('[\w]*path$',re.I),
     #Anything that ends in path, case-insensitive. Used to match
     #something that was extracted as above.
     
     'pathval': re.compile('(\$\{?[\w]*path\}?)(?:[/:]|$)',re.I) }
     # Matches an environment variable that
     # starts with a $
     # optionally followed by a {
     # contains any number of alphanumerics or _
     # ends with path (case-insensitive)
     # optionally followed by a }
     # terminated by a \ (for windows) or / (for *nix) or :
     # Takes the whole thing, including the ${}.
     
class FakeContainer(object):
    """For testing purposes"""
    def __init__(self, context=None, defdict={}, mock=False):
        self.context=context
        self.defdict=defdict
        self.platform = PlatformType()
        self.MOCK=mock
        
class DirLevel(object):
    """Holds dictionaries and other info about the environment
    at a given directory level"""
    def __init__(self, dirname, container=None, empty=False):
        """ dirname = the name of this level
        container = the parent, usually an EnvGetter
        empty = for test purposes only, to hand-fill the object"""
        
        #Data
        self.name=dirname
        self.container=container

        #Empty structures
        self.istop=False
        self.parent=None
        self.leveldict={}
        self.final={}
        self.missing=set()
        self.tca=[]

        #Fill in empty structures
        if container is None:
            self.container=FakeContainer()

        #Here is where the real work is done.
        if not empty:
            self.processfile()   #read in the local environment to leveldict
            self.apply_parent()  #apply the parent environment to leveldict
            self.merge()         #merge with the default environment to final
            self.substitute()    #apply internal substitutions to final

            
    def processfile(self):
        """Process a pdk_environment file with no substitutions.
        Includes a MOCK functionality for purposes of unit testing."""

        fname=os.path.join(self.name,efname)
        
        if self.container.MOCK: 
            self.leveldict={'name':fname,  
                            self.container.counter:self.container.counter}
            self.container.counter+=1
            if self.container.context is not None:
                print "update with context",self.container.context

        else:

            #Process defaults
            ans=parsefile(fname,self.container.platform)
            #Extend with context
            if self.container.context is not None:
                ans.update(parsefile(".".join([fname,self.container.context]),
                                     self.container.platform))
            #Fill in the answer                           
            self.leveldict=ans

            #Special handling of tca key
            try:
                self.tca=self.leveldict['tca'].split()
                del self.leveldict['tca']
            except KeyError:
                pass
            
    def apply_parent(self):
        """Applies the parent dictionary to this level's dictionary.
        Child keys always override parent keys."""
        
        if self.istop: #we're already at the top
            return

        parent=os.path.dirname(self.name)
        if ((parent == self.name) or
            os.path.isfile(os.path.join(self.name,ttop)) ):
             #discover we're at the top
            self.istop=True
            return 

        else:
            if self.parent is None:
                self.parent=DirLevel(parent, container=self.container)
                self.container.nodes[parent]=self.parent
                
            self.leveldict=dict(self.parent.leveldict,
                                **self.leveldict)
 
    def merge(self):
        """Merge the current level with the default dictionary (typically
        os.environ).
           Local keys override default keys ***except*** for the
        special case of keys in the default dict that end with PATH (case-
        INsensitive), for which internal substitution will be applied."""
        
        self.final=dict(self.container.defdict,
                        **self.leveldict)

        #Apply special path handling
        for key, val in self.leveldict.items():
            try:
                if re.match(pat['pathkey'],key) and ':' in val:
                    m=re.search(pat['pathval'],self.final[key])
                    if m :
                        newval=val.replace(m.group(1),
                                       self.container.defdict[key])
                        self.final[key]=newval

            except TypeError:
                pass


    def substitute(self):
        """Now that the dictionary is completely filled in, go through and
        apply the substitutions from all the values. This produces the final
        dictionary that can be supplied as the environment of a process."""

        for key, val in self.final.items():
            try:
                for sub in re.findall(pat['envpat'],val):
                    self.final[key]=val.replace("$%s"%sub,self.final[sub])
            except TypeError:
                pass #ok to skip non-string values
            except KeyError:
                self.missing.add(sub)


    def export(self, format=None, fh=None, full=False):
        """Export the environment for this directory.

        x.export(format, file, full)

        format is one of
            'sh', 'csh'
                environment setting commands for that shell
            'env'
                as a standard pdk_environment file
            'tca'
                ???

        file is the file to write to, or sys.stdout if None

        If full, then the complete environment (including defdict,
        normally os.environ) will be exported. By default, only the
        locally- specified environment is exported.

        If the format is tca, and the tca keyword was specified in
        the environment, then its values will be used as keys into the
        defdict, and those values will be exported.
        """
        # choose defaults
        if format is None:
            format='tca'

        if fh is None:
            fh=sys.stdout

        # pick out the list of interesting names that should be exported
        if not full:
            klist = [k for k in self.final if k not in self.container.defdict]
        else:
            klist = self.final.keys()

        klist.sort()

        # output csh format commands
        if format == 'csh' :
            for x in klist :
                fh.write('setenv %s %s ;\n'% ( x, common.csh_quote(self.final[x]) ) )
            return

        # output sh format commands
        elif format == 'sh' :
            for x in klist :
                fh.write('%s=%s ; \n'% ( x, common.sh_quote(self.final[x]) ) )
            for x in klist :
                fh.write('export %s ;\n'%x)
            return

        # not quite sure what the rest of this is about
        rec=dict(tca="tca_%s=%s\n",
                 env="%s = %s\n")

        hdr=dict(tca='',
                 env="[default]\n")

        fh.write(hdr[format])
        for key in klist:
            fh.write(rec[format]%(key,self.final[key]))

        #Now add the special tcas from os.environ
        if format=='tca' and not full and len(self.tca)>0:
            for key in self.tca:
                try:
                    fh.write(rec[format]%(key,self.final[key]))
                except KeyError:
                    fh.write(rec[format]%(key,"TCA requested but not found"))


class EnvGetter(object):
    """Container class and user interface."""
    def __init__(self, defdict=None, context=None,mock=False):
        #By default, environment will be merged with os.environ.
        if defdict is None:
            self.defdict=os.environ.copy()
            # bug: hack: windows sets PROMPT=$P$G which totally hoses up envgetter
            if 'PROMPT' in self.defdict :
                del self.defdict['PROMPT']
        else:
            self.defdict=defdict
            
        
        self.nodes=dict()        #dictionary of DirLevel objects
        self.context=context     #contexts modify default environment
        
        #Platform info
        self.platform=PlatformType()

        #for testing purposes
        self.MOCK=mock           
        self.counter=0
        
        
        
    def populate(self,dirname):
        """Populates the specified level and all parents.
        If already populated, exits immediately."""
        if dirname in self.nodes:
            return
        else:
            self.nodes[dirname]=DirLevel(dirname,container=self)
            self.nodes[dirname].merge()
            self.nodes[dirname].substitute()
            
    def envdir(self,dirname):
        """User interface to obtain a dictionary containing a
        completely specified environment to be passed to a
        subprocess."""
        #Populate in case it hasn't been done yet
        self.populate(dirname)
        #Check for missing values.

        if len(self.nodes[dirname].missing) > 0:
            raise KeyError("Missing values for %s. A complete environment cannot be provided for %s."%(self.nodes[dirname].missing, dirname))
        else:
            return self.nodes[dirname].final
        

    def gettop(self):
        """Return remembered "top" of environment.
        Raise exception if more than one node thinks it is the top."""
        
        tlist=[v.name for v in self.nodes.values() if v.istop]
        if len(tlist) == 1:
            return tlist.pop()
        else:
            raise(ValueError("More than one toplevel dectected: %s"%str(tlist)))

    def export(self,dirname,format=None,fh=None,full=False):
        """User interface to export an environment. Delegates to
        DirLevel."""
        self.populate(dirname)
        #delegate:
        self.nodes[dirname].export(format=format,fh=fh,full=full)
                

def parsefile(fname,platform=''):
    """Helper function: Make a configparser, parse the file,
    return the dictionary."""
    cfg=ConfigParser.SafeConfigParser()
    cfg.optionxform=str #retain case sensitivity!!
    cfg.read(fname)
    ans={}
    #Process defaults
    try:
        for key,val in cfg.items('default'):
            ans[key]=val
    except ConfigParser.NoSectionError:
        pass #ok to have no defaults
    #Apply any platform-specific overrides
    
    for section in platform:
        try:
            for key,val in cfg.items(section):
                ans[key]=val
        except ConfigParser.NoSectionError:
            pass #defaults are OK
        except TypeError:
            pass #we didn't get a platform
    return ans
        
            
