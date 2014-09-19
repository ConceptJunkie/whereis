whereis started out 1997 as a C++ program and was something I've used almost
daily on Windows since then.

As an exercise in learning Python, I ported it to Python about 2 years and
discovered to my delight that not only was the code a lot smaller in Python,
but that it was actually faster, too.

Since this is something I use a lot, especially at work, it's been pretty well
bug-tested and featureful.

Rick

  c:\sys\ut>whereis /?

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
          print file attributes

      /b dir, --backup dir
          backup found files to a location relative to dir

      /c command, --execute_command command
          execute a command for each file (see -hh for details)

      /D {a,c,m} --output_timestamp {a,c,m}
          output file timestamp, a = last accessed, c = created, m = last
          modified

      /d, --output_timestamp
          output file timestamp (equivalent to /Dm)

      /e, --output_dir_totals
          output totals for each directory

      /E, --output_dir_totals_only
          output totals for each directory and not for each file

      /i filespec [filespec ...], --include_filespec fielspec [filespec ...]
          include additional filespecs for searching

      /l, --count_lines
          output the line count of each file

      /Lf n, --file_count_length n
          set the amount of size of the file count column

      /Ll n, --line_length n
          set the default line length for displaying text (default is 80)

      /Ln n, --line_count_length n
          set the default size of the line count column

      /Lz n, --file_size_length n
          set the default size of the file size column

      /m, --no_commas
          display numerical values with no commas

      /n [n], --max_depth [n]
          maximum directory depth to recurse when searching, defaults to infinite
          if /n is not specified or 1 directory if /n is specified with no value

      /q, --quiet
          suppress unnecessary output

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

      /x filespec [filespec ...], --exclude_filespec filespec [filespec ...]
          exclude filespecs from searching

      /z, --print_command_only
          the same as /c, except the command is not executed, but output to the
          console

