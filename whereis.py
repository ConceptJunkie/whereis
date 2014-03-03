#!/usr/bin/env python

import argparse
import codecs
from datetime import datetime
import fnmatch
import locale
import os
from os.path import join, getsize
import reprlib                      # prevents barfing on weird characters in filenames
import sys
import threading
import time
import re


#//**********************************************************************
#//
#//  globals/constants
#//
#//**********************************************************************

PROGRAM_NAME = "whereis"
VERSION = "3.5.0"
COPYRIGHT_MESSAGE = "copyright (c) 2012 (1997), Rick Gutleber (rickg@his.com)"

currentDir = ""
currentDirCount = 1
blankLine = ""

defaultLineLength = 80                   
defaultFileCountLength = 9
defaultLineCountLength = 9
defaultFileSizeLength = 14 

lineLength = 0

outputLock = threading.Lock( )

stopEvent = threading.Event( )


#//**********************************************************************
#//
#//  printRevisionHistory
#//
#//**********************************************************************

def printRevisionHistory( ):
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
    2.0.0 : completely rewrote RDirIterator and changed it to RDirEnumerator
            and RFileEnumerator, whereis no longer leaks massive memory during
            large jobs, plus the code is simpler
    2.0.1 : allows for multiple /b arguments, updated to RickLib 1.5.0
    2.0.2 : no longer uses iostream.h
    2.0.2.1 : default format width changed from 13 to 14... it was time...
    2.0.3 : built with RickLib 1.6.1
    2.1.0 : added support for UNC names ("\\\\machine\\share\\dir\\", etc)
    2.1.1 : added depth limiter command (added a numerical arg to /n)
    2.1.2 : added /N rename special command
    3.0.0 : port to python, only some features have been ported so far,
            but about 90% of what I actually use
    3.0.1 : bugfixes for directory totalling and explicitly replacing '*.*'
            with '*' since they mean the same thing in Windows
    3.1.0 : added -c and -b back (-c supports !!, !f, !q, !r )
    3.2.0 : added -1 back
    3.3.0 : added !d, !D, !t, !T, !b, !c, !x, !p, !P, !/, !n, and !0 
    3.4.0 : changed -l to -L, added -l
    3.5.0 : changed -L to -Ll, added -Lf, -Ln, -Lz, plus lots of bug fixing, 
            better exception handling
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

            print( blankLine + output, end='\r', file=sys.stderr )

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

    parser = argparse.ArgumentParser( prog=PROGRAM_NAME, description=PROGRAM_NAME + ' - ' + VERSION + ' - ' + COPYRIGHT_MESSAGE )

    parser.add_argument( '-1', '--find_one', action='store_true' )
    parser.add_argument( '-b', '--backup', action='store', default='' )
    parser.add_argument( '-c', '--execute_command', action='store', default='' )
    parser.add_argument( '-d', '--output_timestamp', action='store_const', const='m' )
    parser.add_argument( '-D', choices='acm', default='m', help='output timestamp, a = last accessed, c = created, m = last modified' )
    parser.add_argument( '-e', '--output_dir_totals', action='store_true' )
    parser.add_argument( '-E', '--output_dir_totals_only', action='store_true' )
    parser.add_argument( '-i', '--include_filespec', action='append', nargs="+" )
    parser.add_argument( '-l', '--count_lines', action='store_true' )
    parser.add_argument( '-Lf', '--file_count_length', type=int, default=defaultFileCountLength )
    parser.add_argument( '-Ll', '--line_length', type=int, default=defaultLineLength )
    parser.add_argument( '-Ln', '--line_count_length', type=int, default=defaultLineCountLength )
    parser.add_argument( '-Lz', '--file_size_length', type=int, default=defaultFileSizeLength )
    parser.add_argument( '-m', '--no_commas', action='store_true' )
#    parser.add_argument( '-n', '--recurse_levels', type=int, default=0 )
    parser.add_argument( '-r', '--output_relative_path', action='store_true' )
#    parser.add_argument( '-R', '--rename', choices='dmnsu' )
    parser.add_argument( '-s', '--output_file_size', action='store_true' )
    parser.add_argument( '-t', '--output_totals', action='store_true' )
    parser.add_argument( '-v', '--version', action='version', version='%(prog)s ' + VERSION )
    parser.add_argument( '-vv', '--version_history', action='store_true' )
    parser.add_argument( '-x', '--exclude_filespec', action='append', nargs="+" )
    parser.add_argument( '-z', '--print_command_only', action='store_true' )
    parser.add_argument( '-?', '--print_help', action='store_true' )
    parser.add_argument( 'filespec', nargs='?', default='*', help='whereis tries to identify filespec and sourcedir correctly regardless of order' )
    parser.add_argument( 'sourceDir', nargs='?', default='./')

    args = parser.parse_args( )

    if args.print_help:
        parser.print_help( )
        exit( )

    if args.version_history:
        printRevisionHistory( )
        exit( )

    fileSpec = args.filespec
    sourceDir = args.sourceDir

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

    printCommandOnly = args.print_command_only

    if args.no_commas:
        formatString = 'd'
    else:
        formatString = ',d'            

    fileCountFormat = str( fileCountLength ) + formatString
    lineCountFormat = str( lineCountLength ) + formatString
    fileSizeFormat = str( fileSizeLength ) + formatString

    fileNameRepr = reprlib.Repr( )
    fileNameRepr = lineLength - 1    # sets max string length of repr

    #print( "sourceDir: " + sourceDir )
    #print( "fileSpec: " + fileSpec )
    #print( )

    # try to identify source dir and filespec intelligently...
    # I don't want order to matter if it's obvious what the user meant
    if all( ( c in './\\' ) for c in fileSpec ) or any( ( c in '*?' ) for c in sourceDir ) or \
       any( ( c in '/\\' ) for c in fileSpec ) or ( os.path.isdir( fileSpec ) ):
        fileSpec, sourceDir = sourceDir, fileSpec

    if all( ( c in './\\' ) for c in fileSpec ):
        fileSpec = '*'

    fileSpec = fileSpec.replace( '*.*', '*' )    # *.* and * mean the same thing on Windows

    if not os.path.isdir( sourceDir ):
        print( "whereis: source directory '" + sourceDir + "' does not exist or cannot be accessed", file=sys.stderr )
        exit( )

    if ( backupLocation != '' ) and ( not os.path.isdir( backupLocation ) ):
        print( "whereis: backup location '" + backupLocation + "' does not exist or cannot be accessed", file=sys.stderr )
        exit( )

    # start status thread
    blankLine = ' ' * ( lineLength - 1 ) + '\r'
    threading.Thread( target = statusProcess ).start( )

    #print( "sourceDir: " + sourceDir )
    #print( "fileSpec: " + fileSpec )

    fileCount = 0
    lineTotal = 0
    grandDirTotal = 0
    grandLineTotal = 0
    currentDir = os.path.abspath( sourceDir )

    foundOne = False

    # walk the tree
    for top, dirs, files in os.walk( sourceDir ):
        top = os.path.normpath( top )

        if outputRelativePath:
            currentDir = top
        else:
            currentDir = os.path.abspath( top )

        currentDirCount += 1

        dirTotal = 0
        lineTotal = 0

        fileSet = set( fnmatch.filter( files, fileSpec ) )

        for includeFileSpec in includeFileSpecs:
            fileSet = fileSet.union( fnmatch.filter( files, includeFileSpec ) )

        for excludeFileSpec in excludeFileSpecs:
            fileSet = fileSet.difference( fnmatch.filter( files, excludeFileSpec ) )

        createdBackupDir = ( top == '.' )

        for fileName in sorted( fileSet, key=str.lower ):
            absoluteFileName = os.path.join( os.path.abspath( top ), fileName )
            relativeFileName = os.path.join( top, fileName )

            fileSize = os.stat( absoluteFileName ).st_size
            dirTotal = dirTotal + fileSize
            fileCount += 1

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

                if printCommandOnly:
                    print( ' ' * ( lineLength - 1 ) + '\r' + translatedCommand )
                else:
                    #os.system( translatedCommand + ' > ' + os.devnull )
                    os.system( translatedCommand + ' > ' + os.devnull )

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
                    print( blankLine, end='' )

                    printDate = False

                    if outputTimestamp == 'a':
                        out_date = datetime.fromtimestamp( round( os.stat( absoluteFileName ).st_atime, 0 ) )
                        printDate = True
                    elif outputTimestamp == 'c':
                        out_date = datetime.fromtimestamp( round( os.stat( absoluteFileName ).st_ctime, 0 ) )
                        printDate = True
                    elif outputTimestamp == 'm':
                        out_date = datetime.fromtimestamp( round( os.stat( absoluteFileName ).st_mtime, 0 ) )
                        printDate = True

                    if printDate:
                        print( out_date.isoformat( ' ' ), end=' ' )

                    if outputFileSize:
                        print( format( fileSize, fileSizeFormat ), end=' ' )

                    if countLines: 
                        print( format( lineCount, lineCountFormat ), end=' ' )

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
                print( blankLine, end='' )
                print( format( dirTotal, fileSizeFormat ), end=' ' )

                if countLines: 
                    print( format( dirLineTotal, lineCountFormat ), end=' ' )

                print( currentDir )

        if outputTotals:
            grandDirTotal += dirTotal
            grandLineTotal += lineTotal
            currentDirCount += 1

        if foundOne and findOne:
            break

    if outputTotals:
        with outputLock:
            print( blankLine, end='' )

            if printDate:
                print( '                    ', end='' )            

            if outputFileSize: 
                print( '-' * fileSizeLength, end=' ' )

            if countLines:
                print( '-' * lineCountLength, end=' ' )

            print( '-' * fileCountLength )

            if printDate:
                print( '                    ', end='' )            

            if outputFileSize: 
                print( format( grandDirTotal, fileSizeFormat ), end=' ' )

            if countLines:
                print( format( grandLineTotal, lineCountFormat ), end=' ' )

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
    try:
        main( )
    except KeyboardInterrupt: 
        pass
    finally:
        stopEvent.set( )            

    stopEvent.set( )
    print( ' ' * ( lineLength - 1 ) + '\r', end='\r', file=sys.stderr )   # clear the status output


