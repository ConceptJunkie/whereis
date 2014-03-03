#!/usr/bin/env python

import argparse
import codecs
from datetime import datetime
import fnmatch
import locale
import os
from os.path import join, getsize
import platform
import reprlib                      # prevents barfing on weird characters in filenames
import subprocess
import sys
import threading
import time
import re
import win32con
import win32file

noBlessings = False

#try:
#import colorama
#import blessings
#except:
#    noBlessings = True

#print( "********** " + str( noBlessings ) )


#//**********************************************************************
#//
#//  globals/constants
#//
#//**********************************************************************

PROGRAM_NAME = "whereis"
VERSION = "3.6.2"
COPYRIGHT_MESSAGE = "copyright (c) 2012 (1997), Rick Gutleber (rickg@his.com)"

currentDir = ""
currentDirCount = 1

defaultLineLength = 80                   
defaultFileCountLength = 9
defaultLineCountLength = 9
defaultFileSizeLength = 14 

dateLength = 19
attributesLength = 7

lineLength = 0

outputLock = threading.Lock( )

stopEvent = threading.Event( )

argumentPrefixLinux = '-'
argumentPrefixWindows = '/'

prefixListLinux = '-'
prefixListWindows = '/-'

outputAccessed = 0
outputCreated = 1
outputModified = 2
outputSize = 3
outputLineCount = 4
outputAttributes = 5


#//**********************************************************************
#//
#//  printRevisionHistory
#//
#//**********************************************************************

def printRevisionHistory( ):
    print( 'Python Version: ' + platform.python_version( ) )
    print( 'Python Compiler: ' + platform.python_compiler( ) )
    print( 'Python Built: ' + platform.python_build( )[ 1 ] )
    print( )
    print( '''
revision history:
    1.3.0: added command (/c)
    1.4.0: added character count (/h)
    1.4.1: character count bug fix
    1.5.0: added grep (/g, /G)
    1.5.1: fixed character ranges and added "!r"
           removed unnecessary "!A", "!I", "!O", and "!P"
    1.5.2: fixed blatant memory leak and filename output,
           added compression ratio output (/O)
    1.5.3: switched to DirectoryEnt standard wild cards rather than
           translating them myself; correctly reports when it cannot open a
           file
    1.5.4: completely rewrote GFileName class
    1.5.4.1: outputs total number of files
    1.5.4.2: minor workaround related to GFileName
    1.5.4.3: now uses RDirIterator
    1.6.0: now uses a cleaner, simpler GDirIterator and fixed wildcard compare
    1.6.0.1: converted from VC5 to VC6
    1.7.0: added duplicate searching (/u)
    1.7.1: /u now sorts much faster
    1.7.2: better output for /u
    1.7.3: file compare now works for binary files, also duplicate detection
           is now much more efficient (eliminated unnecessary file
           comparisons)
    1.7.4: added unqiue file searching (/q)
    1.7.4.1: modified to use RickLib
    1.7.4.2: many, many RickLib fixes
    1.7.4.3: added "%*" support to GString in RickLib
    1.7.4.4: more bugfixes related to RickLib
    1.7.4.5: modified to use the new GIterator class
    1.7.4.6: many RickLib fixes
    1.7.4.7: updated to RickLib 1.2.1
    1.8.0: added size and date filtering of files, updated to RickLib.1.2.5
    1.9.0: added /b for backing up, removed untested options from docs
    1.9.1: added /r for displaying relative paths
    1.9.2: added /m for comparing found files against another directory tree
    1.9.3: finished and fixed grep, fixed "!p", cleaned up output slightly,
           GArray fixes
    1.9.4: merged 1.9.x branch with 1.8.0 (that\'ll teach me to leave my
           harddrive at home!)
    1.9.5: added /C for executing commands on file contents
    1.9.6: added /fm, /fM and new /fd, /fD usage
    1.9.7: added /fa and /fA (Thanks for the idea, Jake!)
    1.9.8: added /a
    1.9.9: added /zFILE
    1.9.9.1: rebuilt with latest RickLib 1.2.6 with latest bugfixes
    1.10.0: update to latest RickLib (1.2.10)
    1.11.0: added /e and /E
    1.11.0.1: updated to RickLib 1.3.0
    1.11.1: BackUp (/b) now uses OS-level calls rather than shelling out,
            added totals for various statistics, file copy shows percent
            progress for large files
    1.11.2: Added Syntax check (/y) for doing very basic C/C++ format checking
    1.11.2.1: RickLib 1.3.0 final and a few cosmetic things
    1.11.3: Added !d and !D
    1.11.4: updated to latest RickLib (1.3.1 dev) and a few performance
            enhancements
    1.11.5: updated to latest RickLib (1.3.1 dev, still), fixed a time zone
            problem with GTime that caused /f not to work right
    1.12.0: added /v (version check)... renamed old /v to /@ (verbose)
    1.12.1: brought up to date with latest RickLib (1.4.0 dev)
    2.0.0: completely rewrote RDirIterator and changed it to RDirEnumerator
           and RFileEnumerator, whereis no longer leaks massive memory during
           large jobs, plus the code is simpler
    2.0.1: allows for multiple /b arguments, updated to RickLib 1.5.0
    2.0.2: no longer uses iostream.h
    2.0.2.1: default format width changed from 13 to 14... it was time...
    2.0.3: built with RickLib 1.6.1
    2.1.0: added support for UNC names ("\\\\machine\\share\\dir\\", etc)
    2.1.1: added depth limiter command (added a numerical arg to /n)
    2.1.2: added /N rename special command
    3.0.0: port to python, only some features have been ported so far,
           but about 90% of what I actually use
    3.0.1: bugfixes for directory totalling and explicitly replacing '*.*'
           with '*' since they mean the same thing in Windows
    3.1.0: added -c and -b back (-c supports !!, !f, !q, !r )
    3.2.0: added -1 back
    3.3.0: added !d, !D, !t, !T, !b, !c, !x, !p, !P, !/, !n, and !0 
    3.4.0: changed -l to -L, added -l
    3.5.0: changed -L to -Ll, added -Lf, -Ln, -Lz, plus lots of bug fixing, 
           better exception handling
    3.5.1: fixed output (made sure all status stuff goes to stderr)
    3.5.2: bug fixes for directory size output
    3.5.3: bug fixes for directory size output and totalling
    3.6.0: '/' as argument prefix for Windows, '-' for Linux, improved arg 
           parsing, output order based on arg order, added /n
    3.6.1: added /u, switched back to subprocess.call( ) from os.system( ), not
           sure which one is better

    Known bugs: 
        - The status line is occasionally not erased when the search is complete
        - /r does not work unless the search directory is '.', trailing directory
          separators (or lack thereof) might be part of the issue
''' )


#//**********************************************************************
#//
#//  updateStatus
#//
#//  Sometimes whereis can be slow so we update the current directory
#//  count to stderr every 0.5 seconds.
#//
#//**********************************************************************

def statusProcess( ):
    global blankLine
        
    while not stopEvent.isSet( ):
        with outputLock:
            output = format( currentDirCount ) + " - " + currentDir

            if len( output ) > lineLength - 3:
                output = output[ 0 : lineLength - 4 ] + '...'

            print( blankLine + '\r' + output, end='\r', file=sys.stderr )

        stopEvent.wait( 0.5 )


#//**********************************************************************
#//
#//  main
#//
#//**********************************************************************

#  !! - single exclamation point
#  !f - fully qualified filespec
#  !q - double quote character (")
#  !r - relative filespec
#  !t - time of day (24-hour - HHMM) when app was started
#  !T - time of day (24-hour - HHMMSS) when app was started
#  !d - date (YYMMDD) when app was started
#  !D - date (YYYYMMDD) when app was started
#  !c - current working directory
#  !b - base filename (no extension)
#  !x - filename extension
#  !p - relative path
#  !P - absolute path 
#  !/ - OS-specific pathname separator
#  !n - OS-specific line separator
#  !0 - '/dev/null' (or OS equivalent)
#  !i - '<'
#  !o - '>'
#  !O - '>>'
#  !| - '|'

def main( ):
    global currentDir
    global currentDirCount
    global blankLine
    global lineLength

    if os.name == 'nt':
        argumentPrefix = argumentPrefixWindows
        prefixList = prefixListWindows
    else:
        argumentPrefix = argumentPrefixLinux
        prefixList = prefixListLinux

    parser = argparse.ArgumentParser( prog=PROGRAM_NAME, description=PROGRAM_NAME + ' - ' + VERSION + ' - ' + COPYRIGHT_MESSAGE, prefix_chars=prefixList )

    parser.add_argument( argumentPrefix + 'a', '--file_attributes', action='store_true' )
    parser.add_argument( argumentPrefix + '1', '--find_one', action='store_true' )
    parser.add_argument( argumentPrefix + 'b', '--backup', action='store', default='' )
    parser.add_argument( argumentPrefix + 'c', '--execute_command', action='store', default='' )
    parser.add_argument( argumentPrefix + 'd', '--output_timestamp', action='store_const', const='m' )
    parser.add_argument( argumentPrefix + 'D', choices='acm', default='m', help='output timestamp, a = last accessed, c = created, m = last modified' )
    parser.add_argument( argumentPrefix + 'e', '--output_dir_totals', action='store_true' )
    parser.add_argument( argumentPrefix + 'E', '--output_dir_totals_only', action='store_true' )
    parser.add_argument( argumentPrefix + 'i', '--include_filespec', action='append', nargs="+" )
    parser.add_argument( argumentPrefix + 'l', '--count_lines', action='store_true' )
    parser.add_argument( argumentPrefix + 'Lf', '--file_count_length', type=int, default=defaultFileCountLength )
    parser.add_argument( argumentPrefix + 'Ll', '--line_length', type=int, default=defaultLineLength )
    parser.add_argument( argumentPrefix + 'Ln', '--line_count_length', type=int, default=defaultLineCountLength )
    parser.add_argument( argumentPrefix + 'Lz', '--file_size_length', type=int, default=defaultFileSizeLength )
    parser.add_argument( argumentPrefix + 'm', '--no_commas', action='store_true' )
    parser.add_argument( argumentPrefix + 'n', '--max_depth', type=int, const=1, default=0, nargs='?' )
    parser.add_argument( argumentPrefix + 'r', '--output_relative_path', action='store_true' )
#    parser.add_argument( argumentPrefix + 'R', '--rename', choices='dmnsu' )
    parser.add_argument( argumentPrefix + 's', '--output_file_size', action='store_true' )
    parser.add_argument( argumentPrefix + 't', '--output_totals', action='store_true' )
    parser.add_argument( argumentPrefix + 'u', '--hide_command_output', action='store_true' )
    parser.add_argument( argumentPrefix + 'v', '--version', action='version', version='%(prog)s ' + VERSION )
    parser.add_argument( argumentPrefix + 'vv', '--version_history', action='store_true' )
    parser.add_argument( argumentPrefix + 'x', '--exclude_filespec', action='append', nargs='+' )
    parser.add_argument( argumentPrefix + 'z', '--print_command_only', action='store_true' )
    parser.add_argument( argumentPrefix + '?', '--print_help', action='store_true' )

    # let's do a little preprocessing of the argument list because argparse is missing a few pieces of functionality
    # the original whereis provided
    new_argv = list( )
    outputOrder = list( )

    # grab the fileSpec and SourceDir and stick everything else in the list for argparse
    prog = ''             
    fileSpec = ''
    sourceDir = ''

    copyNextOne = False                    
       
    for arg in sys.argv:
        if arg[ 0 ] not in prefixList:
            if copyNextOne:
                new_argv.append( arg )

                if sourceDir == '':
                    copyNextOne = False
            elif prog == '':
               prog = arg
            elif fileSpec == '':
                fileSpec = arg
            elif sourceDir == '':
                sourceDir = arg
            else:
                print( 'ignoring extra arg: ' + arg )
        else:
            new_argv.append( arg )
            copyNextOne = arg[ 1 ] in 'bciLx'   # these are args that can have parameters

            # build the output order list
            if arg[ 1 ] == 'a':
                outputOrder.append( outputAttributes )
            elif arg[ 1 ] == 'l':
                outputOrder.append( outputLineCount )
            elif arg[ 1 ] == 'd':
                outputOrder.append( outputModified )
            elif arg[ 1 ] == 's':
                outputOrder.append( outputSize )
            elif arg[ 1 ] == 'D':
                if arg[ 2 ] == 'a':
                    outputOrder.append( outputAccessed )
                elif arg[ 2 ] == 'c':
                    outputOrder.append( outputCreated )
                else:
                    outputOrder.append( outputModified )

    # set defaults if necessary
    if fileSpec == '':
        fileSpec = '*'

    if sourceDir == '':
        sourceDir = '.'

    # let argparse handle the rest
    args = parser.parse_args( new_argv )

    if args.print_help:
        parser.print_help( )
        exit( )

    if args.version_history:
        printRevisionHistory( )
        exit( )

    # let's handle all the flags and values parsed off the command-line
    if args.include_filespec == None:
        includeFileSpecs = list( )
    else:
        includeFileSpecs = args.include_filespec[ 0 ]

    if args.exclude_filespec == None:
        excludeFileSpecs = list( )
    else:
        excludeFileSpecs = args.exclude_filespec[ 0 ]

    fileCountLength = args.file_count_length
    fileSizeLength = args.file_size_length
    lineCountLength = args.line_count_length
    lineLength = args.line_length

    countLines = args.count_lines

    outputDirTotalsOnly = args.output_dir_totals_only
    outputRelativePath = args.output_relative_path
    outputTotals = args.output_totals
    outputTimestamp = args.output_timestamp
    outputFileSize = args.output_file_size
    outputDirTotals = args.output_dir_totals
    executeCommand = args.execute_command
    backupLocation = args.backup
    findOne = args.find_one
    hideCommandOutput = args.hide_command_output
    fileAttributes = args.file_attributes

    printCommandOnly = args.print_command_only

    maxDepth = args.max_depth

    if args.no_commas:
        formatString = 'd'
    else:
        formatString = ',d'            

    fileCountFormat = str( fileCountLength ) + formatString
    lineCountFormat = str( lineCountLength ) + formatString
    fileSizeFormat = str( fileSizeLength ) + formatString

    fileNameRepr = reprlib.Repr( )
    fileNameRepr = lineLength - 1    # sets max string length of repr

    # try to identify source dir and filespec intelligently...

    # I don't want order to matter if it's obvious what the user meant
    if all( ( c in './\\' ) for c in fileSpec ) or any( ( c in '*?' ) for c in sourceDir ) or \
       any( ( c in '/\\' ) for c in fileSpec ) or ( os.path.isdir( fileSpec ) ):
        fileSpec, sourceDir = sourceDir, fileSpec

    if all( ( c in './\\' ) for c in fileSpec ):
        fileSpec = '*'

    fileSpec = fileSpec.replace( '*.*', '*' )    # *.* and * mean the same thing on Windows

    # a little validation before we start
    if not os.path.isdir( sourceDir ):
        print( "whereis: source directory '" + sourceDir + "' does not exist or cannot be accessed", file=sys.stderr )
        exit( )

    if ( backupLocation != '' ) and ( not os.path.isdir( backupLocation ) ):
        print( "whereis: backup location '" + backupLocation + "' does not exist or cannot be accessed", file=sys.stderr )
        exit( )

    # start status thread
    blankLine = ' ' * ( lineLength - 1 ) 
    threading.Thread( target = statusProcess ).start( )

    fileCount = 0
    lineTotal = 0
    grandDirTotal = 0
    grandLineTotal = 0

    # initialize currentDir because the status thread might need it before we set it below
    currentDir = os.path.abspath( sourceDir )

    foundOne = False
    printDate = False

    attributeFlags = 0

    # walk the tree
    for top, dirs, files in os.walk( sourceDir ):
        top = os.path.normpath( top )

        relativePath = top[ len( sourceDir ) : ]

        # minor performance note:  we're still going to walk all the directories even if we are ignoring them
        if maxDepth > 0:
            depth = relativePath.count( os.sep ) + 1

            if relativePath != '' and relativePath[ 0 ] != os.sep:
                depth += 1

            if depth > maxDepth:
                continue

        if outputRelativePath:
            currentDir = top[ len( sourceDir ) : ]
        else:
            currentDir = os.path.abspath( top )

        currentDirCount += 1

        dirTotal = 0
        lineTotal = 0

        # build the set of files that match our criteria
        fileSet = set( fnmatch.filter( files, fileSpec ) )

        for includeFileSpec in includeFileSpecs:
            fileSet = fileSet.union( set( fnmatch.filter( files, includeFileSpec ) ) )

        for excludeFileSpec in excludeFileSpecs:
            fileSet = fileSet.difference( set( fnmatch.filter( files, excludeFileSpec ) ) )

        createdBackupDir = ( top == '.' )

        # now we have the list of files, so let's sort them and handle them
        for fileName in sorted( fileSet, key=str.lower ):
            absoluteFileName = os.path.join( os.path.abspath( top ), fileName )
            relativeFileName = os.path.join( top, fileName )

            fileSize = os.stat( absoluteFileName ).st_size
            dirTotal = dirTotal + fileSize
            fileCount += 1

            if fileAttributes:
                attributeFlags = win32file.GetFileAttributes( absoluteFileName )
                                           
            if executeCommand != '':
                translatedCommand = executeCommand

                base, extension = os.path.splitext( fileName )
                extension = extension.strip( )  # unix puts in a newline supposedly
                absolutePathName = os.path.dirname( absoluteFileName )
                relativePathName = os.path.dirname( relativeFileName )

                translatedCommand = translatedCommand.replace( '!!', '!' )
                translatedCommand = translatedCommand.replace( '!q', '"' )
                translatedCommand = translatedCommand.replace( '!i', '<' )
                translatedCommand = translatedCommand.replace( '!o', '>' )
                translatedCommand = translatedCommand.replace( '!O', '>>' )
                translatedCommand = translatedCommand.replace( '!|', '|' )

                translatedCommand = translatedCommand.replace( '!/', os.sep )
                translatedCommand = translatedCommand.replace( '!n', os.linesep )
                translatedCommand = translatedCommand.replace( '!0', os.devnull )

                translatedCommand = translatedCommand.replace( '!d', datetime.now( ).strftime( "%y%m%d" ) )
                translatedCommand = translatedCommand.replace( '!D', datetime.now( ).strftime( "%Y%m%d" ) )
                translatedCommand = translatedCommand.replace( '!t', datetime.now( ).strftime( "%H%M" ) )
                translatedCommand = translatedCommand.replace( '!T', datetime.now( ).strftime( "%H%M%S" ) )

                translatedCommand = translatedCommand.replace( '!c', '"' + os.getcwd( ) + '"' )
                translatedCommand = translatedCommand.replace( '!r', '"' + relativeFileName + '"' )
                translatedCommand = translatedCommand.replace( '!f', '"' + absoluteFileName + '"' )
                translatedCommand = translatedCommand.replace( '!b', '"' + base + '"' )              
                translatedCommand = translatedCommand.replace( '!x', '"' + extension + '"' )
                translatedCommand = translatedCommand.replace( '!p', '"' + relativePathName + '"' )
                translatedCommand = translatedCommand.replace( '!P', '"' + absolutePathName + '"' )

                if not hideCommandOutput:
                    translatedCommand += ' > ' + os.devnull

                if printCommandOnly:
                    print( ' ' * ( lineLength - 1 ) + '\r' + translatedCommand )
                else:
                    subprocess.call( translatedCommand )

            if countLines:
                lineCount = 0

                for line in codecs.open( absoluteFileName, 'rU', 'ascii', 'replace'  ): 
                    lineCount += 1

                lineTotal = lineTotal + lineCount

            if backupLocation != '':
                if not createdBackupDir:
                    backupTargetDir = os.path.join( backupLocation, top )
                    print( 'mkdir -p "' + backupTargetDir + '" > NUL ' )
                    createdBackupDir = True

                backupTargetFile = os.path.join( backupLocation, relativeFileName )
                print( 'copy "' + absoluteFileName + '" "' + backupTargetFile + '" > NUL ' )

            if not outputDirTotalsOnly:
                with outputLock:
                    # this will clear the console line for output    
                    print( blankLine, end='\r', file=sys.stderr )

                    for outputType in outputOrder:
                        if outputType == outputAccessed:
                            out_date = datetime.fromtimestamp( round( os.stat( absoluteFileName ).st_atime, 0 ) )
                            print( out_date.isoformat( ' ' ), end=' ' )
                        elif outputType == outputCreated:
                            out_date = datetime.fromtimestamp( round( os.stat( absoluteFileName ).st_ctime, 0 ) )
                            print( out_date.isoformat( ' ' ), end=' ' )
                        elif outputType == outputModified:
                            out_date = datetime.fromtimestamp( round( os.stat( absoluteFileName ).st_mtime, 0 ) )
                            print( out_date.isoformat( ' ' ), end=' ' )
                        elif outputType == outputSize:
                            print( format( fileSize, fileSizeFormat ), end=' ' )
                        elif outputType == outputLineCount:
                             print( format( lineCount, lineCountFormat ), end=' ' )
                        elif outputType == outputAttributes:
                            print( ( 'a' if attributeFlags & win32con.FILE_ATTRIBUTE_ARCHIVE else '-' ) +
                                   ( 'c' if attributeFlags & win32con.FILE_ATTRIBUTE_COMPRESSED else '-' ) +
                                   ( 'h' if attributeFlags & win32con.FILE_ATTRIBUTE_HIDDEN else '-' ) +
                                   ( 'n' if attributeFlags & win32con.FILE_ATTRIBUTE_NORMAL else '-' ) +
                                   ( 'r' if attributeFlags & win32con.FILE_ATTRIBUTE_READONLY else '-' ) +
                                   ( 's' if attributeFlags & win32con.FILE_ATTRIBUTE_SYSTEM else '-' ) +
                                   ( 't' if attributeFlags & win32con.FILE_ATTRIBUTE_TEMPORARY else '-' ), end=' ' )

                    #print( os.path.join( currentDir, repr( fileName )[ 1 : -1 ] ) )
                    if outputRelativePath:
                        print( repr( relativeFileName ).replace( '\\\\', '\\' )[ 1 : -1 ] )
                    else:
                        print( repr( absoluteFileName ).replace( '\\\\', '\\' )[ 1 : -1 ] )

            foundOne = True

            if findOne:
                break

        if outputDirTotals or outputDirTotalsOnly:
            with outputLock:
                print( blankLine, end='\r', file=sys.stderr )

                for outputType in outputOrder:
                    if outputType == outputAccessed:
                        print( ' ' * dateLength, end = ' ' )
                    elif outputType == outputCreated:
                        print( ' ' * dateLength, end = ' ' )
                    elif outputType == outputModified:
                        print( ' ' * dateLength, end = ' ' )
                    elif outputType == outputSize:
                        print( format( dirTotal, fileSizeFormat ), end=' ' )
                    elif outputType == outputLineCount:
                         print( format( lineTotal, lineCountFormat ), end=' ' )
                    elif outputType == outputAttributes:
                        print( ' ' * attributesLength, end = ' ' )

                print( currentDir )

        if outputTotals:
            grandDirTotal += dirTotal
            grandLineTotal += lineTotal
            currentDirCount += 1

        if foundOne and findOne:
            break

    if outputTotals:
        with outputLock:
            print( blankLine, end='\r' )

            for outputType in outputOrder:
                if outputType == outputAccessed:
                    print( ' ' * dateLength, end = ' ' )
                elif outputType == outputCreated:
                    print( ' ' * dateLength, end = ' ' )
                elif outputType == outputModified:
                    print( ' ' * dateLength, end = ' ' )
                elif outputType == outputSize:
                    print( ( '-' * fileSizeLength ), end=' ' )
                elif outputType == outputLineCount:
                    print( ( '-' * lineCountLength ), end=' ' )
                elif outputType == outputAttributes:
                    print( ' ' * attributesLength, end = ' ' )

            print( '-' * fileCountLength )

            for outputType in outputOrder:
                if outputType == outputAccessed:
                    print( ' ' * dateLength, end = ' ' )
                elif outputType == outputCreated:
                    print( ' ' * dateLength, end = ' ' )
                elif outputType == outputModified:
                    print( ' ' * dateLength, end = ' ' )
                elif outputType == outputSize:
                    print( format( grandDirTotal, fileSizeFormat ), end=' ' )
                elif outputType == outputLineCount:
                    print( format( grandLineTotal, lineCountFormat ), end=' ' )
                elif outputType == outputAttributes:
                    print( ' ' * attributesLength, end = ' ' )

            if outputDirTotalsOnly:
                print( format( currentDirCount, fileCountFormat ) )
            else:
                print( format( fileCount, fileCountFormat ) )

#//**********************************************************************
#//
#//  __main__
#//
#//**********************************************************************

if __name__ == '__main__':
    global blankLine

    try:
        main( )
    except KeyboardInterrupt: 
        pass
    finally:
        stopEvent.set( )            
        # raise RuntimeError( "Unhandled exception" )

    stopEvent.set( )

    print( blankLine, end='\r', file=sys.stderr )   # clear the status output


