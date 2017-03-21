#! /usr/bin/env python2.7
#
# Author: Pat Litke (C) 2013 (when I was young and dumb and didn't know about pprint)
#
# This file is not part of any application. Please use it and adapt it as necessary
#
#       Description: See http://php.net/manual/en/function.print-r.php for a crash-course
#       This code attempts to print in nice, human-readable format Lists and Dictionaries
#

def print_r(haystack, depth=0, inline=False, inline_key=0, inline_max_key=0):

    # Give our first open bracket, depending on what haystack is...
    if isinstance(haystack, dict) and depth == 0:
        print "Dictionary\n{"

    if isinstance(haystack, list) and depth == 0:
        print "List\n["


    # These two IFs check to see if the function is being called from within a routine.. if so, output information accordingly
    if isinstance(haystack, dict) and inline == True:
        print ("      "*(depth))+"["+str(inline_key)+"] "+str(" "*(inline_max_key-len(str(inline_key))))+" =>      DICT()"
        print ("      "*(depth))+"{"

    if isinstance(haystack, list) and inline == True:
        print ("      "*(depth))+"["+str(inline_key)+"] "+str(" "*(inline_max_key-len(str(inline_key))))+" =>      LIST()"
        print ("      "*(depth))+"["


    ## Dictionary
    #       Returns a tuple for each row. Break it up into keypair and do magic with it
    if isinstance(haystack, dict):

        # How many keys are we working with?
        if len(haystack) <= 0:
            max_key = 0
        else:
            max_key = max(len(str(k)) for k in haystack.iterkeys())

        # Traverse (at only the "top" level) the dictionary
        for count, keyValue in enumerate(haystack.iteritems()):

            # Split our tuple up into a key and a value
            key, value = keyValue

            # Basic logic from here out...
            if isinstance(value, dict) or isinstance(value, list):

                print_r(value, depth+1, True, key, max_key)

            else:

                print ("      "*(depth+1))+"["+str(key)+"] "+str(" "*(max_key-len(str(key))))+" =>      "+str(value)

        # Print our closing bracket
        print ("      "*(depth))+"}"

    ## Lists
    #       Returns a tuple for each row in the list with a numerical key
    if isinstance(haystack, list):

        # How many keys are in the shit?
        if len(haystack) <= 0:
            max_key = 0
        else:
            max_key = len(max(haystack))

        # traverse our dictionary
        for count, keyValue in enumerate(haystack):

            if isinstance(keyValue, dict) or isinstance(keyValue, list):
                print_r(keyValue, depth+1, True, count, max_key)

            else:
                print ("      "*(depth+1))+"["+str(count)+"] "+str(" "*(max_key-len(str(count))))+" =>      "+str(keyValue)


        print("      "*(depth))+"]"
