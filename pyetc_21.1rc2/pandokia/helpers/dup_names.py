
class DupNames(object) :

    def __init__( self ) :
        self.all_names = { }
        self.dups = 0

    def saw_name( self, name, note=None ) :
        if not name in self.all_names :
            self.all_names[name] = [ note ]
            return

        self.all_names[name].append(note)
        self.dups += 1

    def had_dups( self ):
        return self.dups > 0

    def list_dups( self ):
        l = [ ]
        for x in self.all_names :
            if len(self.all_names[x]) > 1 :
                l.append( x )
        return l

    def list_dups_with_notes( self ) :
        l = [ ]
        for x in self.all_names :
            if len(self.all_names[x]) > 1 :
                l.append( (x,self.all_names[x]) )
        return l
