# Datum

A command line tool to query databases via ODBC.  
It has the following goals:  
&nbsp;  
* Keep dependencies to a minimum (only pyodbc so far)
* Easy to install and use, but configurable
* Support as many database engines as possible
* Play nicely with Emacs' SQLi mode  
&nbsp;  
It is an attempt at a cleaner version of [sqlcmdline](https://github.com/sebasmonia/sqlcmdline/). That tool was born out of necessity since [sqlcmd](https://docs.microsoft.com/en-us/sql/tools/sqlcmd-utility) didn't quite work with SQLi. Over time I added support for other DB engines but it was never intended for full compatiblity.  
Datum was built from scratch keeping in mind some of the limitations in sqlcmdline, but also trying very hard to avoid the second system effect :)  
&nbsp;  
## Table of contents

<!--ts-->

   * [Installation](#installation)
   * [Connecting to a DB](#connecting-to-a-db)
   * [Configuration file](#configuration-file)
   * [Commands](#comands)
   * [Custom commands](#custom-comands)
   * [Emacs SQLi mode setup](#emacs-sqli-mode-setup)

<!--te-->

## Installation

You can install `datum` using `pip`:

```
pip install git+https://github.com/sebasmonia/datum.git
```

Remember that you should add `--upgrade` to check for package updates after you installed it.

## Connecting to a DB

```
datum --conn_string=<connection_string> [--config=<path>]
```  
&nbsp;  
-OR-
&nbsp;  
```
datum (--driver=<odbc_driver> | --dsn=<dsn>)
      [--server=<server> --database=<database>]
      [--user=<username> --pass=<password> --integrated]
      [--config=<path>]
```

You can use `datum --help` in your terminal to see more details about each parameter, although they are pretty self-explanatory.  
If you go with the first version, you are meant to specify a full connection string.  
The alternative is to provide either a DSN, or an ODBC driver to use. A DSN might contain all the information needed, or skip some parameters (for example, the auth portion) so you can still add more values in the invocation.  
You can interpolate environment variables in your shell of choice, a (hopefully) simpler alternative is to start a value with `ENV=`. For example `--pass=ENV=DB_SECRET` would get the value for the password from $DB_SECRET / %DB_SECRET%.

Once connected, you are greeted with a messsage and a `>` prompt to type your queries. Special commands start with ":", use `:help` to get online help (or keep reading this manual).  
Use "GO" in a new line to send the query to the database. Alternatively, you can end your query with `;;`:

```
> SELC

```

## Configuration file

There's an option to provide an INI file to setup the start up value of Datum's config and setup "custom commands" (more on this in the relevant section).  
If `--config` is not provided, Datum will look for a file named `config.ini` in the directory `$XDG_CONFIG_HOME/datum` or `$HOME/.config/datum` (or `%USERPROFILE%\.config\datum` on Windows).  
When provided, the value is assumed to be a file in the current directory or a full path, and if not found then the config directory is searched. This is convenient in case you want to define custom queries for example per DB-engine using files named `mssql.ini`, `mariadb.ini`, `sqlite.ini`, etc.; you can just drop all the files in the Datum `.config` directory and use e.g. `--config=sqlite.ini` when you connect to a SQLite DB. You could also store custom queries per-database in separate files, or keep config files in different repositories, and so on.  
&nbsp;  
The repository for Datum includes a throughly documented sample [config.ini](https://github.com/sebasmonia/datum/blob/main/config.ini) file. Note that the file is completely optional, and all configuration can be modified at runtime.

## Commands


* :help - Prints the command list.
* :rows [number] - How many rows to print out of the resultset. Call with no number to see the current value. Use 0 for "all rows".
* :chars [number] - How many chars per column to print. Call with no number to see the current value. Use 0 to not truncate.

:null [string]    String to show for "NULL" in the database. Call with no args
                  to see the current string. Use "OFF" (no quotes) to show
                  nothing. Note that this makes empty string and null hard to
                  differentiate.

:newline [string] String to replace newlines in values. Use "OFF" (no quotes)
                  to keep newlines as-is, it will most likely break the display
                  of output. Call with no arg to display the current value.

:tab [string]     String to replace tab in values. Use "OFF" (no quotes) to
                  keep tab characters. Call with no arguments to show the
                  current value.

:timeout [number] Seconds for command timeouts - how long to wait for a command
                  to finish running.

## Custom commands

**TBD**  

## Emacs SQLi mode setup

**TBD**  
