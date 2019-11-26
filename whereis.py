#!/usr/bin/env python
# -*- coding: latin-1 -*-

from __future__ import print_function

import six

import argparse
import codecs
import filecmp
import fnmatch
import itertools
import locale
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time

if six.PY2:
    import repr as reprlib
else:
    import reprlib              # prevents barfing on weird characters in filenames

if os.name == 'nt':
    import win32con
    import win32file

from datetime import datetime
from os.path import join, getsize

python26 = sys.version_info[ : 2 ] == ( 2, 6 )


#//******************************************************************************
#//
#//  globals/constants
#//
#//******************************************************************************

PROGRAM_NAME = 'whereis'
VERSION = '3.11.0'
COPYRIGHT_MESSAGE = 'copyright (c) 2019 (1997), Rick Gutleber (rickg@his.com)'

currentDir = ''
currentDirCount = 0
currentFileCount = 0

defaultFileCountLength = 9
defaultLineCountLength = 9
defaultFileSizeLength = 16
defaultLineLength = 80

fileCountLength = 0
fileSizeLength = 0
lineCount = 0
lineCountLength = 0
lineLength = 0

fileCountFormat = ''
lineCountFormat = ''
fileSizeFormat = ''

dateLength = 19
attributesLength = 7

lineLength = 0

outputLock = threading.Lock( )
stopEvent = threading.Event( )

outputAccessed = 0
outputCreated = 1
outputModified = 2
outputSize = 3
outputLineCount = 4
outputAttributes = 5

outputOrder = list( )

statusLineDirty = False
oldOutput = ''

findDupes = False

# OS-specific strings

copyCommandWindows = "copy"
copyCommandLinux = "cp"

argumentPrefixLinux = '-'
argumentPrefixWindows = '/'

prefixListLinux = argumentPrefixLinux
prefixListWindows = argumentPrefixLinux + argumentPrefixWindows

if os.name == 'nt':
    argumentPrefix = argumentPrefixWindows
    prefixList = prefixListWindows
    copyCommand = copyCommandWindows
else:
    argumentPrefix = argumentPrefixLinux
    prefixList = prefixListLinux
    copyCommand = copyCommandLinux


#//******************************************************************************
#//
#//  printRevisionHistory
#//
#//******************************************************************************

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
    3.7.0: added /u, fixed /n, switched back to subprocess.call( ) from
           os.system( ), not sure which one is better
    3.8.0: added /a
    3.8.1: changed exit( ) to return because TCC uses shebang and calling
           exit( ) also causes TCC to exit, also python files can be run
           directly from the TCC command-line without needing a batch file
           or alias
    3.8.2: small changes to status line, fixed /r
    3.8.3: fixed use of undefined variable
    3.8.4: changed back to os.system( ) because I can't get subprocess to work
    3.8.5: blankLine wasn't updated if /Ll was set
    3.8.6: directory depth wasn't always calculated correctly, causing /n1 to
           fail
    3.8.7: added TO_DEV_NULL
    3.8.8: now handles a permission exception when trying to get the filesize
           and just pretends the filesize is 0
    3.8.9: increased default file length of 16... 100s of GB.  It happens
           frequently enough when summing directory sizes.
    3.8.10: status line cleanup is only done when needed
    3.9.0: added /q, although the 3.8.10 fix eliminated the original reason
           for adding it
    3.9.1: don't update the status line unless it's actually changed
    3.9.2: handle stderr a little differently if stdout is being redirected
           since it doesn't need to be erased
    3.9.3: stdout is redirected when it's being piped, so that change didn't
           work so well
    3.9.4: I had stopped using reprlib correctly... probably a long time ago.
    3.9.5: minor bug fix with attributeFlags
    3.9.6: wrote help text to replace what argparse generates, because it's
           pretty ugly and hard to read
    3.9.7: simple exception handling for Unicode filenames
    3.9.8: whereis detects Unicode filenames rather than throwing an exception
    3.9.9: added /g to turn off filename truncation
    3.9.10:  changed from os.system( ) to subprocess.Popen( ) which doesn't
             block
    3.9.11:  whereis didn't properly allow multiple instances of /i and /x,
             file name truncation is off by default, /g now turns it on
    3.9.12:  minor bug with escaping a single-quote when processing /c
    3.10.0:  Linux compatibility, Python 2 compatibility, finally implemented
             /b (oops), fixed /c command output to console, fixed /e, /a
             outputs file permissions on Linux
    3.10.1:  Cython support
    3.10.2:  whereis now catches FileNotFound exceptions when trying to get
             file information on files that are write-locked.
    3.10.3:  whereis now catches OSError exceptions, which are thrown when,
             for instance, a file has the name "CON".
    3.11.0:  added /y to search for duplicate files and /w to add extra source
             directories to search

    Known bugs:
        - The original intent was to never have output wrap with /g (according
          to /Ll or the default of 80), but this never took into account extra
          columns being output.
''' )


#//**********************************************************************
#//
#//  outputTotalStats
#//
#//**********************************************************************

def outputTotalStats( size = 0, lines = 0, separator = False ):
    global fileSizeLength
    global lineCountLength

    if outputSize not in outputOrder:
        print( format( size, fileSizeFormat ), end=' ' )

    for outputType in outputOrder:
        if outputType == outputAccessed:
            print( ' ' * dateLength, end = ' ' )
        elif outputType == outputCreated:
            print( ' ' * dateLength, end = ' ' )
        elif outputType == outputModified:
            print( ' ' * dateLength, end = ' ' )
        elif outputType == outputSize:
            if separator:
                print( ( '-' * fileSizeLength ), end=' ' )
            else:
                print( format( size, fileSizeFormat ), end=' ' )
        elif outputType == outputLineCount:
            if separator:
                print( ( '-' * lineCountLength ), end=' ' )
            else:
                print( format( lines, lineCountFormat ), end=' ' )
        elif outputType == outputAttributes:
            print( ' ' * attributesLength, end = ' ' )


#//******************************************************************************
#//
#//  makeUnixPermissionsString
#//
#//  We build the permissions string backwards by looking at the last 9 bits
#//  of the mode value.
#//
#//******************************************************************************

def makeUnixPermissionsString( _mode ):
    modeString = 'xwr'  # backwards
    mode = _mode

    result = ''

    for i in range( 3 ):
        for j in range( 3 ):
            if mode & 0x01:
                result = modeString[ j ] + result
            else:
                result = '-' + result

            mode >>= 1

    return result


#//******************************************************************************
#//
#//  outputFileStats
#//
#//******************************************************************************

def outputFileStats( absoluteFileName, fileSize, lineCount, attributeFlags ):
    try:
        stat_result = os.stat( absoluteFileName )
    except FileNotFoundError:
        return
    except OSError:
        return

    for outputType in outputOrder:
        if outputType == outputAccessed:
            out_date = datetime.fromtimestamp( round( stat_result.st_atime, 0 ) )
            print( out_date.isoformat( ' ' ), end=' ' )
        elif outputType == outputCreated:
            out_date = datetime.fromtimestamp( round( stat_result.st_ctime, 0 ) )
            print( out_date.isoformat( ' ' ), end=' ' )
        elif outputType == outputModified:
            out_date = datetime.fromtimestamp( round( stat_result.st_mtime, 0 ) )
            print( out_date.isoformat( ' ' ), end=' ' )
        elif outputType == outputSize:
            print( format( fileSize, fileSizeFormat ), end=' ' )
        elif outputType == outputLineCount:
             print( format( lineCount, lineCountFormat ), end=' ' )
        elif outputType == outputAttributes:
            if os.name == 'nt':
                print( ( 'a' if attributeFlags & win32con.FILE_ATTRIBUTE_ARCHIVE else '-' ) +
                       ( 'c' if attributeFlags & win32con.FILE_ATTRIBUTE_COMPRESSED else '-' ) +
                       ( 'h' if attributeFlags & win32con.FILE_ATTRIBUTE_HIDDEN else '-' ) +
                       ( 'n' if attributeFlags & win32con.FILE_ATTRIBUTE_NORMAL else '-' ) +
                       ( 'r' if attributeFlags & win32con.FILE_ATTRIBUTE_READONLY else '-' ) +
                       ( 's' if attributeFlags & win32con.FILE_ATTRIBUTE_SYSTEM else '-' ) +
                       ( 't' if attributeFlags & win32con.FILE_ATTRIBUTE_TEMPORARY else '-' ), end=' ' )
            else:
                print( makeUnixPermissionsString( stat_result.st_mode ), end=' ' )


#//******************************************************************************
#//
#//  translateCommand
#//
#//  Translate the '!' tokens in the command to be executed
#//
#//  !! - single exclamation point
#//  !/ - OS-specific pathname separator
#//  !0 - '/dev/null' (or OS equivalent)
#//  !b - base filename (no extension)
#//  !c - current working directory
#//  !d - date (YYMMDD) when app was started
#//  !D - date (YYYYMMDD) when app was started
#//  !f - fully qualified filespec
#//  !i - '<'
#//  !n - OS-specific line separator
#//  !o - '>'
#//  !O - '>>'
#//  !P - absolute path
#//  !p - relative path
#//  !q - double quote character (")
#//  !r - relative filespec
#//  !t - time of day (24-hour - HHMM) when app was started
#//  !T - time of day (24-hour - HHMMSS) when app was started
#//  !x - filename extension
#//  !| - '|', pipe character
#//
#//******************************************************************************

def translateCommand( command, base, extension, currentAbsoluteDir, absoluteFileName, currentRelativeDir, \
                      relativeFileName ):
    translatedCommand = command.replace( '!!', '!' )

    translatedCommand = translatedCommand.replace( '!/', os.sep )

    translatedCommand = translatedCommand.replace( '!0', os.devnull )
    translatedCommand = translatedCommand.replace( '!D', datetime.now( ).strftime( "%Y%m%d" ) )
    translatedCommand = translatedCommand.replace( '!O', '>>' )
    translatedCommand = translatedCommand.replace( '!P', '"' + currentAbsoluteDir + '"' )
    translatedCommand = translatedCommand.replace( '!T', datetime.now( ).strftime( "%H%M%S" ) )

    translatedCommand = translatedCommand.replace( '!b', '"' + base + '"' )
    translatedCommand = translatedCommand.replace( '!c', '"' + os.getcwd( ) + '"' )
    translatedCommand = translatedCommand.replace( '!d', datetime.now( ).strftime( "%y%m%d" ) )
    translatedCommand = translatedCommand.replace( '!f', '"' + absoluteFileName + '"' )
    translatedCommand = translatedCommand.replace( '!i', '<' )
    translatedCommand = translatedCommand.replace( '!n', os.linesep )
    translatedCommand = translatedCommand.replace( '!o', '>' )
    translatedCommand = translatedCommand.replace( '!p', '"' + currentRelativeDir + '"' )
    translatedCommand = translatedCommand.replace( '!q', '"' )
    translatedCommand = translatedCommand.replace( '!r', '"' + relativeFileName + '"' )
    translatedCommand = translatedCommand.replace( '!t', datetime.now( ).strftime( "%H%M" ) )
    translatedCommand = translatedCommand.replace( '!x', '"' + extension + '"' )

    translatedCommand = translatedCommand.replace( '!|', '|' )

    return translatedCommand


#//**********************************************************************
#//
#//  statusProcess
#//
#//  Sometimes whereis can be slow, so we update the current directory
#//  count to stderr every 0.5 seconds unless /q is used.
#//
#//**********************************************************************

def statusProcess( ):
    global blankLine
    global statusLineDirty
    global oldOutput

    while not stopEvent.isSet( ):
        with outputLock:
            output = format( currentDirCount ) + ' (' + format( currentFileCount ) + ') - ' + currentDir

            if len( output ) > lineLength - 3:
                output = output[ 0 : lineLength - 4 ] + '...'

            if output != oldOutput:
                print( blankLine + '\r' + output + '\r', end='', file=sys.stderr )
                sys.stderr.flush( )
                statusLineDirty = True
                oldOutput = output

        stopEvent.wait( 0.5 )


#//******************************************************************************
#//
#//  printHelp
#//
#//******************************************************************************

def printHelp( ):
    helpText = \
'''
usage:  whereis [options] [filespec] [target]

Search for files with names matching 'filespec' in the location specified
by 'target'.

filespec defaults to '*.*'

target defaults to '.'

If only one argument is specified, whereis attempts to determine if it is a
filespec or target.

command-line options:

    /?, /h, --print_help
        output this help message and exit

    /1, --find_one
        quit after finding one file

    /a, --file_attributes
        print file attributes (file permissions on Linux)

    /b dir, --backup dir
        backup found files to a location relative to dir

    /c command, --execute_command command
        execute a command for each file (currently unsupported in Linux)

    /D {a,c,m} --output_timestamp {a,c,m}
        output file timestamp, a = last accessed, c = created, m = last
        modified

    /d, --output_timestamp
        output file timestamp (equivalent to /Dm)

    /e, --output_dir_totals
        output totals for each directory

    /E, --output_dir_totals_only
        output totals for each directory and not for each file

    /g, --filename_truncation
        whereis attempts to display the filenames on a single line

    /i filespec [filespec ...], --include_filespec filespec [filespec ...]
        include additional filespecs for searching

    /l, --count_lines
        output the line count of each file

    /Lf n, --file_count_length n
        set the amount of size of the file count column

    /Ll n, --line_length n
        set the default line length for displaying text, used with /g (default is 80)

    /Ln n, --line_count_length n
        set the default size of the line count column

    /Lz n, --file_size_length n
        set the default size of the file size column

    /m, --no_commas
        display numerical values with no commas (Python 2.6 does not support commas)

    /n [n], --max_depth [n]
        maximum directory depth to recurse when searching, defaults to infinite
        if /n is not specified or 1 directory if /n is specified with no value

    /q, --quiet
        suppress status output

    /r, --output_relative_path
        output a relative path to the current directory for files rather than
        an absolute file path

    /s, --output_file_size
        output the file sizes in bytes

    /t, --output_totals
        output totals for all numerical vallues

    /u, --hide_command_output
        suppress output from commands (i.e. when using /c)

    /v, --version
        output the version number and exit

    /vv, --version_history
        output the version history

    /w filespec [filespec ...], --extra_target filespec [filespec ...]
        adds one or more additional directories to search

    /x filespec [filespec ...], --exclude_filespec filespec [filespec ...]
        exclude filespecs from searching

    /y, --find_dupes
        search for duplicate files in files listed in output

    /z, --print_command_only
        the same as /c, except the command is not executed, but output to the
        console
'''

    if os.name != 'nt':
        helpText = helpText.replace( argumentPrefixWindows, argumentPrefixLinux )

    print( PROGRAM_NAME + ' ' + VERSION + '\n' + helpText )


#//******************************************************************************
#//
#//  main
#//
#//******************************************************************************

def main( ):
    global currentDir
    global currentDirCount
    global currentFileCount
    global blankLine
    global lineLength

    global fileCountLength
    global fileSizeLength
    global lineCountLength
    global lineLength

    global fileCountFormat
    global lineCountFormat
    global fileSizeFormat

    global quiet
    global statusLineDirty

    blankLine = ' ' * ( defaultLineLength - 1 )

    parser = argparse.ArgumentParser( prog=PROGRAM_NAME, description=PROGRAM_NAME + ' - ' + VERSION + ' - ' +
                                      COPYRIGHT_MESSAGE, prefix_chars=prefixList, add_help=False )

    parser.add_argument( argumentPrefix + 'a', '--file_attributes', action='store_true' )
    parser.add_argument( argumentPrefix + '1', '--find_one', action='store_true' )
    parser.add_argument( argumentPrefix + 'b', '--backup', action='store', default='' )
    parser.add_argument( argumentPrefix + 'c', '--execute_command', action='store', default='' )
    parser.add_argument( argumentPrefix + 'd', '--output_timestamp', action='store_const', const='m' )
    parser.add_argument( argumentPrefix + 'D', choices='acm', default='m', help='output timestamp, a = last accessed, c = created, m = last modified' )
    parser.add_argument( argumentPrefix + 'e', '--output_dir_totals', action='store_true' )
    parser.add_argument( argumentPrefix + 'E', '--output_dir_totals_only', action='store_true' )
    parser.add_argument( argumentPrefix + 'f', '--folders-only', action='store_true' )
    parser.add_argument( argumentPrefix + 'g', '--filename_truncation', action='store_true' )
    parser.add_argument( argumentPrefix + 'h', '--print_help2', action='store_true' )
    parser.add_argument( argumentPrefix + 'i', '--include_filespec', action='append', nargs='+' )
    parser.add_argument( argumentPrefix + 'l', '--count_lines', action='store_true' )
    parser.add_argument( argumentPrefix + 'Lf', '--file_count_length', type=int, default=defaultFileCountLength )
    parser.add_argument( argumentPrefix + 'Ll', '--line_length', type=int, default=defaultLineLength )
    parser.add_argument( argumentPrefix + 'Ln', '--line_count_length', type=int, default=defaultLineCountLength )
    parser.add_argument( argumentPrefix + 'Lz', '--file_size_length', type=int, default=defaultFileSizeLength )
    parser.add_argument( argumentPrefix + 'm', '--no_commas', action='store_true' )
    parser.add_argument( argumentPrefix + 'n', '--max_depth', type=int, const=1, default=0, nargs='?' )
    parser.add_argument( argumentPrefix + 'q', '--quiet', action='store_true' )
    parser.add_argument( argumentPrefix + 'r', '--output_relative_path', action='store_true' )
#    parser.add_argument( argumentPrefix + 'R', '--rename', choices='dmnsu' )
    parser.add_argument( argumentPrefix + 's', '--output_file_size', action='store_true' )
    parser.add_argument( argumentPrefix + 't', '--output_totals', action='store_true' )
    parser.add_argument( argumentPrefix + 'u', '--hide_command_output', action='store_true' )
    parser.add_argument( argumentPrefix + 'w', '--extra_target', action='append', nargs='+' )
    parser.add_argument( argumentPrefix + 'v', '--version', action='version', version='%(prog)s ' + VERSION )
    parser.add_argument( argumentPrefix + 'vv', '--version_history', action='store_true' )
    parser.add_argument( argumentPrefix + 'x', '--exclude_filespec', action='append', nargs='+' )
    parser.add_argument( argumentPrefix + 'y', '--find_dupes', action='store_true' )
    parser.add_argument( argumentPrefix + 'z', '--print_command_only', action='store_true' )
    parser.add_argument( argumentPrefix + '?', '--print_help', action='store_true' )

    # let's do a little preprocessing of the argument list because argparse is missing a few pieces of functionality
    # the original whereis provided... specifically the ability to determine the order in which arguments occur
    new_argv = list( )

    # grab the fileSpec and SourceDir and stick everything else in the list for argparse
    prog = ''
    fileSpec = ''
    sourceDir = ''

    extraSourceDirs = [ ]

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
            copyNextOne = arg[ 1 ] in 'bciLwx'   # these are args that can have parameters

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

    quiet = args.quiet

    if args.print_help or args.print_help2:
        printHelp( )
        return

    if args.version_history:
        printRevisionHistory( )
        return

    # let's handle all the flags and values parsed off the command-line
    if args.include_filespec:
        includeFileSpecs = list( itertools.chain( *args.include_filespec ) )
    else:
        includeFileSpecs = list( )

    if args.exclude_filespec:
        excludeFileSpecs = list( itertools.chain( *args.exclude_filespec ) )
    else:
        excludeFileSpecs = list( )

    if args.extra_target:
        extraSourceDirs = list( itertools.chain( *args.extra_target ) )

    fileCountLength = args.file_count_length
    fileSizeLength = args.file_size_length
    lineCountLength = args.line_count_length
    lineLength = args.line_length

    if lineLength != defaultLineLength:
        blankLine = ' ' * ( lineLength - 1 )

    countLines = args.count_lines

    outputDirTotalsOnly = args.output_dir_totals_only
    outputRelativePath = args.output_relative_path
    outputTotals = args.output_totals
    outputTimestamp = args.output_timestamp
    outputDirTotals = args.output_dir_totals
    executeCommand = args.execute_command
    backupLocation = args.backup
    findOne = args.find_one
    hideCommandOutput = args.hide_command_output
    fileAttributes = args.file_attributes
    foldersOnly = args.folders_only
    fileNameTruncation = args.filename_truncation

    printCommandOnly = args.print_command_only

    maxDepth = args.max_depth

    if args.no_commas or python26:
        formatString = 'd'
    else:
        formatString = ',d'

    fileCountFormat = str( fileCountLength ) + formatString
    lineCountFormat = str( lineCountLength ) + formatString
    fileSizeFormat = str( fileSizeLength ) + formatString

    fileNameRepr = reprlib.Repr( )
    fileNameRepr.maxstring = lineLength - 1    # sets max string length of repr

    findDupes = args.find_dupes

    #redirected = not sys.stdout.isatty( )

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
        return

    if ( backupLocation != '' ) and ( not os.path.isdir( backupLocation ) ):
        try:
            os.makedirs( backupLocation )
        except:
            print( "whereis: backup location '" + backupLocation + "' cannot be created", file=sys.stderr )

        return

    # start status thread
    if not quiet:
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

    sourceDirs = [ sourceDir ]
    sourceDirs.extend( extraSourceDirs )

    # We'll use this if we want to find duplicates.
    filesAndSizes = { }

    # walk the tree
    for currentSourceDir in sourceDirs:
        for top, dirs, files in os.walk( currentSourceDir ):
            top = os.path.normpath( top )

            # performance note:  We're still going to walk all the directories even if we are ignoring them.
            #                    I haven't figured out how to avoid that.
            if maxDepth > 0:
                depth = top.count( os.sep ) + 1

                if top != '' and top[ 0 ] != os.sep and top[ 0 ] != '.':
                    depth += 1

                if depth > maxDepth:
                    continue

            currentAbsoluteDir = os.path.abspath( top )
            currentRelativeDir = os.path.relpath( top, currentSourceDir )

            if outputRelativePath:
                currentDir = currentRelativeDir
            else:
                currentDir = currentAbsoluteDir

            currentDirCount += 1
            currentFileCount = 0

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
                currentFileCount += 1

                absoluteFileName = os.path.join( currentAbsoluteDir, fileName )
                relativeFileName = os.path.join( currentRelativeDir, fileName )

                try:
                    fileSize = os.stat( absoluteFileName ).st_size
                except PermissionError:
                    fileSize = 0
                except FileNotFoundError:
                    fileSize = 0
                except OSError:
                    fileSize = 0

                if findDupes:
                    filesAndSizes[ absoluteFileName ] = fileSize

                dirTotal = dirTotal + fileSize
                fileCount += 1

                if os.name == 'nt' and fileAttributes:
                    attributeFlags = win32file.GetFileAttributes( absoluteFileName )

                if executeCommand != '' and os.name == 'nt':
                    base, extension = os.path.splitext( fileName )
                    extension = extension.strip( )  # unix puts in a newline supposedly

                    translatedCommand = translateCommand( executeCommand, base, extension, currentAbsoluteDir,
                                                          absoluteFileName, currentRelativeDir, relativeFileName )

                    if hideCommandOutput:
                        translatedCommand += ' > ' + os.devnull

                    if printCommandOnly:
                        print( blankLine, end='\r', file=sys.stderr )
                        print( translatedCommand )
                    else:
                        subprocess.Popen( shlex.split( translatedCommand ), shell=True )

                lineCount = 0

                if countLines:
                    for line in codecs.open( absoluteFileName, 'rU', 'ascii', 'replace' ):
                        lineCount += 1

                    lineTotal = lineTotal + lineCount

                if backupLocation != '':
                    if not createdBackupDir:
                        backupTargetDir = os.path.join( backupLocation, currentRelativeDir )

                        if not os.path.exists( backupTargetDir ):
                            os.makedirs( backupTargetDir )

                        createdBackupDir = True

                    backupTargetFileName = os.path.join( backupLocation, relativeFileName )

                    try:
                        shutil.copy2( absoluteFileName, backupTargetDir )
                    except:
                        print( 'error copying ' + absoluteFileName + ' to ' + backupTargetDir )

                if not outputDirTotalsOnly:
                    with outputLock:
                        # this will clear the console line for output, if necessary
                        if not quiet and statusLineDirty:
                            print( blankLine, end='\r', file=sys.stderr )
                            statusLineDirty = False

                        outputFileStats( absoluteFileName, fileSize, lineCount, attributeFlags )

                        if outputRelativePath:
                            if fileNameTruncation:
                                outputText = fileNameRepr.repr( relativeFileName ).replace( '\\\\', '\\' )[ 1 : -1 ]
                            else:
                                outputText = relativeFileName.replace( '\\\\', '\\' )
                        else:
                            if fileNameTruncation:
                                outputText = fileNameRepr.repr( absoluteFileName ).replace( '\\\\', '\\' )[ 1 : -1 ]
                            else:
                                outputText = absoluteFileName.replace( '\\\\', '\\' )

                        try:
                            print( outputText )
                        except:
                            print( "whereis: unicode filename found ('" +
                                   str( outputText.encode( 'ascii', 'backslashreplace' ) ) + "')", file=sys.stderr )

                foundOne = True

                if findOne:
                    break

            if outputDirTotals or outputDirTotalsOnly:
                if outputDirTotalsOnly or dirTotal > 0:
                    with outputLock:
                        if not quiet and statusLineDirty:
                            print( blankLine, end='\r', file=sys.stderr )
                            statusLineDirty = False

                        if not outputDirTotalsOnly:
                            print( )

                        outputTotalStats( dirTotal, lineTotal )
                        print( currentDir.encode( sys.stdout.encoding, errors='replace' ) )

                        if not outputDirTotalsOnly:
                            print( )

            if outputTotals:
                grandDirTotal += dirTotal
                grandLineTotal += lineTotal
                currentDirCount += 1

            if foundOne and findOne:
                break

        if outputTotals:
            with outputLock:
                if not quiet and statusLineDirty:
                    print( blankLine, end='\r', file=sys.stderr )
                    statusLineDirty = False

                outputTotalStats( separator = True )

                print( '-' * fileCountLength )

                outputTotalStats( grandDirTotal, grandLineTotal )

                if outputDirTotalsOnly:
                    print( format( currentDirCount, fileCountFormat ) )
                else:
                    print( format( fileCount, fileCountFormat ) )

    # hey, we might not be done yet...
    if not findDupes:
        return

    sizesAndFiles = { }

    # flip the dictionary into a reverse multidict
    for key, value in filesAndSizes.items( ):
        sizesAndFiles.setdefault( value, set( ) ).add( key )

    # now for any key that has multiple values, those values are files
    # we need to actually compare, so let's make a list of those files
    fileSetsToCompare = list( values for key, values in sizesAndFiles.items( ) if len( values ) > 1 )

    print( )

    matchResults = [ ]

    for fileSet in fileSetsToCompare:
        if len( fileSet ) == 1:
            continue

        fileResults = { }

        for file in fileSet:
            fileResults[ file ] = 0

        fileFlavor = 1

        for firstFile, secondFile in itertools.combinations( fileSet, 2 ):
            if fileResults[ firstFile ] == 0 or fileResults[ secondFile ] == 0:
                print( f"Comparing '{firstFile}' and '{secondFile}'..." )

                if filecmp.cmp( firstFile, secondFile, shallow=False ):
                    if fileResults[ firstFile ] == 0:
                        if fileResults[ secondFile ] != 0:
                            fileResults[ firstFile ] = fileResults[ secondFile ]
                        else:
                            fileResults[ firstFile ] = fileFlavor
                            fileResults[ secondFile ] = fileFlavor
                            fileFlavor += 1
                    else:
                        fileResults[ secondFile ] = fileResults[ firstFile ]

        fileFlavors = { }

        # do the reverse multidict thing _again_
        for key, value in fileResults.items( ):
            fileFlavors.setdefault( value, set( ) ).add( key )

        #print( 'fileFlavors', fileFlavors )

        # extracts sets of files that match so we can print them out
        fileSetsThatMatch = [ ]

        for key, value in fileFlavors.items( ):
            #print( 'value', value )
            if key > 0 and len( value ) > 1:
                fileSetsThatMatch.append( list( value ) )

        #print( 'fileSetsThatMatch', fileSetsThatMatch )

        for fileSet in fileSetsThatMatch:
            matchResults.append( fileSet )

    print( )
    print( 'Match results...' )

    maxSize = [ 0, 0 ]

    for matchResult in matchResults:
        matches = sorted( matchResult )

        if len( maxSize ) < len( matches ):
            maxSize.extend( [ 0 ] * ( len( matches ) - len( maxSize ) ) )

        for i, match in enumerate( matches ):
            if maxSize[ i ] < len( match ):
                maxSize[ i ] = len( match )

    for matchResult in matchResults:
        matches = sorted( matchResult )

        output = ''

        for match in matches:
            output += '"' + match + '",' + ' ' * ( maxSize[ i ] - len( match ) + 5 )

        print( output )


#//******************************************************************************
#//
#//  startUp
#//
#//******************************************************************************

def startUp( ):
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


#//******************************************************************************
#//
#//  __main__
#//
#//******************************************************************************

if __name__ == '__main__':
    startUp( )

