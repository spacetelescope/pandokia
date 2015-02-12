import pandokia.helpers.pycode as pycode
import pandokia.helpers.dict_comp as dict_comp
import pandokia.helpers.display as display

dict_a = {
            'a' : 'a',
            'b' : 'b',
            'c' : {
                'x' : 1,
                'y' : 2,
                },
            'd' : [ 10, 11, 12 ],
        }

dict_b = {
        'a' : 'a',
        'b' : 'b',
        'c' : {
            'x' : 1,
            'y' : 2,
            },
        'd' : [ 10, 11, 12 ],
        'e' : [ 20, { 'el2a' : 'el2av', 'el2b' : 'el2bv' }, 21 ],
        }

dict_c = {
        'a' : 'a',
        'b' : 'b',
        'c' : {
            'x' : 1,
            'y' : 2,
            },
        'd' : [ 10, 11, 12 ],
        'e' : [ 20, { 'el2a' : 
                        [ 1, 2, 3 ],
                        'el2b' : 'el2bv' 
                     }, 
                21, 22, 23
            ],
        'f' : [ [ [ 1, 2 ], 2 ], 2 ],
        'g' : { 'a' : { 'b' : { 'c' : 1 } },
                'b' : { 'x' : 1 }
             },
        }

dict_d = dict_c.copy()
dict_d['h'] = [ 1.1, 1.2, 1.2001 ]
 
with pycode.test('flatten') :
    def doit( name, dict_in ) :
        with pycode.test(name) as t :
            dict_out = dict_comp.flatten(dict_in)
            
            print "IN"
            print display.dprint(dict_in)
            print "OUT"
            print display.dprint(dict_out)

            print t.full_name

    doit( 'a', dict_a)

    doit( 'b', dict_b)

    doit( 'c', dict_c)

    with pycode.test('exc') as t :
        try :
            dict_comp.flatten( { 'a' : [ 0, 1 ], 'a.1' : 2, } )
        except dict_comp.DuplicateIndexException :
            pass
        except Exception as e :
            raise
        else :
            assert "did not raise exception"


with pycode.test('compare') :

    with pycode.test('a') as t :
        okfh = dict_comp.open_okfile( t.full_name )
        dict_comp.dictionary_comp( 
            data_dict = dict_a, 
            file_base = t.full_name + '.a', 
            tda = t.tda, tra = t.tra, print_info = True ,
            okfh = okfh)

    with pycode.test('bc') as t :
        okfh = dict_comp.open_okfile( t.full_name )
        dict_comp.dictionary_comp( 
            data_dict = dict_b, 
            file_base = t.full_name + '.b', 
            tda = t.tda, tra = t.tra, print_info = True ,
            okfh = okfh)
        dict_comp.dictionary_comp( 
            data_dict = dict_c, 
            file_base = t.full_name + '.c', 
            tda = t.tda, tra = t.tra, print_info = True ,
            okfh = okfh)

    with pycode.test('d') as t :
        okfh = dict_comp.open_okfile( t.full_name )
        dict_comp.dictionary_comp( 
            data_dict = dict_d, 
            file_base = t.full_name, 
            fp_tolerance = 1e-5,
            tda = t.tda, tra = t.tra, print_info = True,
            okfh = okfh )
