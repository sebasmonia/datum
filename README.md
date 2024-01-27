# Datum

A command line tool to query databases via ODBC.  
It has the following goals:  

* Keep dependencies to a minimum (only docopt and pyodbc so far)
* Easy to install and use, but configurable
* Support as many database engines as possible
* Play nicely with Emacs' SQLi mode  

Datum is an attempt at a cleaner version of [sqlcmdline](https://github.com/sebasmonia/sqlcmdline/), which in turn was born as a quick replacement for [sqlcmd](https://docs.microsoft.com/en-us/sql/tools/sqlcmd-utility). Over time `sqlcmdline` gained support for more DB engines and other features, but it was never intended for use other than MSSQL.  
Datum was built from scratch keeping in mind some of the limitations in sqlcmdline, but also trying very hard to avoid the second system effect :)  
&nbsp;  

## v0.7 => v0.8 Breaking change

The parameter to use a literal connection string has been changed from `--conn_string` to the more standard `--conn-string`.

## Table of contents

<!--ts-->

   * [Installation](#installation)
   * [Connecting to a DB](#connecting-to-a-db)
   * [Configuration file](#configuration-file)
   * [Built-in Commands](#built-in-commands)
   * [Custom commands](#custom-commands)
   * [Emacs SQLi mode setup](#emacs-sqli-mode-setup)

<!--te-->

## Installation

You can install `datum` from this repository using `pip`:

```
pip install git+https://github.com/sebasmonia/datum.git
```

Remember that you should add `--upgrade` to check for package updates after you installed it.  
All examples in this manual use the SQLite version of the [Chinook sample database](https://github.com/jimfrenette/chinook-database): _"The Chinook data model represents a digital media store, including tables for artists, albums, media tracks, invoices and customers"_.

## Connecting to a DB

```
datum --conn-string=<connection_string> [--config=<path>]
```  
-OR-
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

Once connected, you are greeted with a message and a `>` prompt to type your queries. Special commands start with ":", use `:help` to get online help (or keep reading this manual).  
For example, if we were to connect to the SQLite version of Chinook and start querying...  

```
[user@host]$ datum --driver SQLITE3 --database /path/to/datase/chinook.db
Connected to server - database /path/to/datase/chinook.db

Special commands are prefixed with ":". For example, use ":exit" or ":quit" to
finish your session. Use ":help" to list available commands.
Everything else is sent directly to the server using ODBC when you type "GO" in
a new line or ";;" at the end of a query.

-@/path/to/datase/chinook.db
>:rows 3  
Printing 3 rows of each resulset.

-@/path/to/datase/chinook.db
>select * from artist  
>go

ArtistId|Name     
--------|---------
       1|AC/DC    
       2|Accept   
       3|Aerosmith

Rows printed: 3/0

Rows affected: 0

-@/path/to/datase/chinook.db
>select * from artist where name like 'b%';; 

ArtistId|Name               
--------|-------------------
       9|BackBeat           
      10|Billy Cobham       
      11|Black Label Society

Rows printed: 3/0

Rows affected: 0

-@/path/to/datase/chinook.db
>select * from artist where artistid > ?;;
1>25

ArtistId|Name         
--------|-------------
      26|Azymuth      
      27|Gilberto Gil 
      28|João Gilberto

Rows printed: 3/0

Rows affected: 0

-@/path/to/datase/chinook.db
>
```
The last example shows that we can use `?` to [parameterize queries](https://github.com/mkleehammer/pyodbc/wiki/Getting-started#parameters). You will be asked for input for as many parameters as `?` characters are in the query. These are properly escaped by pyodbc, so they are convenient when working with strings.  
&nbsp;  
The "Rows printed" message shows how many rows were displayed from the total returned by the query, as you can see above some drivers don't report the latter. Similarly "Rows affected" is reported by the drivers, it is usually accurate for non-query operations.  

## Configuration file

There's an option to provide an INI file to setup the start up value of Datum's config and setup "custom commands" (more on this in the relevant section).  
If `--config` is not provided, Datum will look for a file named `config.ini` in the directory `$XDG_CONFIG_HOME/datum` or `$HOME/.config/datum` (or `%USERPROFILE%\.config\datum` on Windows).  
&nbsp;  
When `--config` is supplied, the value is assumed to be a file in the current directory or a full path, and if not found then the config directory is searched.  
This is convenient in case you want to define custom queries for example per DB-engine using files named `mssql.ini`, `mariadb.ini`, `sqlite.ini`, etc.; you can drop all the files in the Datum `.config` directory and use e.g. `--config=sqlite.ini` when you connect to a SQLite DB.  
You could also store custom queries per-database in separate files, or keep config files in different repositories, and so on.  
&nbsp;  
The repository for Datum includes a thoroughly documented sample [config.ini](https://github.com/sebasmonia/datum/blob/main/config.ini) file. Note that the file is optional, and all configuration can be modified at runtime.

## Built-in commands

* `:help` - Prints the command list.
* `:rows [number]` - How many rows to print out of the resultset. Call with no number to see the current value. Use 0 for "all rows". If your query will return thousands of rows, printing will block the terminal for a few seconds. Default: 50 rows
* `:chars [number]` - How many chars per column to print. Call with no number to see the current value. Use 0 to not truncate. Depending on the settings of your terminal, printing long values can break the output tables. Default: 100 chars
* `:null [string]` - String to show for "NULL" values. Call with no args to see the current string. Use "OFF" (no quotes) to show nothing. Note that this makes empty string and null hard (impossible?) to tell apart. Default: "[NULL]"
* `:newline [string]` - String to replace newlines in values. Use ":newline OFF" (no quotes) to keep newlines as-is, it will most likely break the display of output. Call with no arg to show the current replacement value. Default: "[NL]"
* `:tab [string]` - String to replace tab in values. Use ":tab OFF" (no quotes) to keep tab characters. Call with no arguments to show the current string. Default: "[TAB]"
* `:timeout [number]` - Seconds for command timeout - how long to wait for a command to finish running. This is set in the ODBC connection, use 0 to wait "forever". Default: 30 seconds
* `:reconnect` - Force a new connection to the server, discarding the old one. Useful if you had a network hiccup, VPN drop, etc.
* `:csv [path]` - Export the output of the next query to a CSV file, without printing. The path is read literally, no need to escape characters, and it can be absolute or relative. Call with no arguments to cancel, if it was set before. 
* `:script [path]` - Read a script from a file. The input is processed as a custom command, so it supports `{placeholders}` and `?` ODBC parameters. See next section for more details on custom commands.

## Custom commands

When there is a `[queries]` section in the INI file, these are added as custom commands. These queries can be parameterized in two levels: using `{placeholders}` that will be replaced using Python's string formatting, and then with `?` for ODBC parameters.
&nbsp;  
You can't use `?` to parameterize LIMIT, but you can with a {placeholder}. You can even parameterize the target table. Assuming we have this in our `config.ini` file:
```
[queries]
limit=SELECT * FROM {table} LIMIT {how_many};
```
and if we run this query connected to the Chinook DB:
```
ChinookDSN
>:limit
table>album
how_many>8

Command query:
 SELECT * FROM album LIMIT 8;

AlbumId|Title                                |ArtistId
-------|-------------------------------------|--------
      1|For Those About To Rock We Salute You|       1
      2|Balls to the Wall                    |       2
      3|Restless and Wild                    |       2
      4|Let There Be Rock                    |       1
      5|Big Ones                             |       3
      6|Jagged Little Pill                   |       4
      7|Facelift                             |       5
      8|Warner 25 Anos                       |       6

Rows printed: 8/8

Rows affected: 0

ChinookDSN
>
```
After the query template runs through `format()`, it is executed as if it was typed by the user. This means we can combine both type of parameters.  
Let's add one more query to our INI file:
```
[queries]
limit=SELECT * FROM {table} LIMIT {how_many};
mixed=SELECT {field}, * FROM {table} WHERE {field} = ?
```
And then:
```
ChinookDSN
>:mixed
field>artistid
table>album

Command query:
 SELECT artistid, * FROM album WHERE artistid = ?
1>2

ArtistId|AlbumId|Title            |ArtistId
--------|-------|-----------------|--------
       2|      2|Balls to the Wall|       2
       2|      3|Restless and Wild|       2

Rows printed: 2/2

Rows affected: 0

ChinookDSN
>
```
There are more examples in the [config.ini](https://github.com/sebasmonia/datum/blob/main/config.ini) sample file.

## Emacs SQLi mode setup

In this repository there's a small package, [sql-datum](https://github.com/sebasmonia/datum/blob/main/sql-datum.el). Drop it somewhere in your load-path, `(require 'sql-datum)` and then you only need to add connections to `sql-connection-alist`.
Example of a use-package based setup, showcasing different combination of options:

```elisp
(use-package sql-datum :load-path "/path/to/sql-datum/inyour/localsetup"
  :after sql
  :config
  (add-to-list 'sql-connection-alist
               '("Chinook"
                 (sql-product 'datum)
                 (sql-send-terminator ";;")
                 (sql-server "")
                 (sql-user "")
                 (sql-password "")
                 (sql-datum-options '("--driver" "SQLITE3" ))
                 (sql-database "/path/to/datase/chinook.db")))
  (add-to-list 'sql-connection-alist
               '("MSSQL-Integrated"
                 (sql-product 'datum)
                 (sql-send-terminator ";;")
                 (sql-server "myserver.somewhere.mycompany")
                 (sql-database "northwind")
                 (sql-user "")
                 (sql-password "")
                 (sql-datum-options '("--driver" "ODBC Driver 17 for SQL Server" "--integrated"))))
  (add-to-list 'sql-connection-alist
               '("ChinookDSN"
                 (sql-product 'datum)
                 (sql-send-terminator ";;")
                 (sql-server "")
                 (sql-user "")
                 (sql-password 'ask)
                 (sql-datum-options '("--dsn" "ChinookDSN"))))
  (add-to-list 'sql-connection-alist
               '("MSSQL-authsource"
                 (sql-product 'datum)
                 (sql-send-terminator ";;")
                 (sql-server "myserver.somewhere.mycompany")
                 (sql-database "chinook")
                 (sql-user 'auth-source)
                 (sql-password 'auth-source)
                 (sql-datum-options '("--driver" "ODBC Driver 17 for SQL Server"))))
  (add-to-list 'sql-connection-alist
               '("MySQL-DSN-ENVVAR"
                 (sql-product 'datum)
                 (sql-send-terminator ";;")
                 (sql-server "")
                 (sql-database "")
                 (sql-user "userName")
                 (sql-password "ENV=SECRET_ENV_VAR")
                 (sql-datum-options '("--dsn" "ConnectionNameFromYourODBC.ini")))))
```
With the setup above you can use `M-x sql-connect` then select a connection from "Chinook", "MSSQL-Integrated", "ChinookDSN", "MSSQL-authsource", or "MySQL-DSN-ENVVAR".  
As seen above, there are two special symbols that can be used in the configuration:
* `'ask` can be assigned to `sql-password` to get prompted each time you try to connect, using `read-passwd`.  
* `'auth-source` can be used in either `sql-user` or `sql-password`, and then the parameter is retrieved from a backend supported by `auth-source`.  

For the last one, I only use `.authinfo.gpg`, but the package supports Gnome's keyring and KDE's wallet. It also allows adding more backends, check its documentation.  
The lookup is done by connection name, for the one in the sample above, you would add to your authinfo:  
```
machine MSSQL-authsource login "the username" password "a secret password"
```

Things to note:  
* The parameters `sql-server`, `sql-database`, `sql-user` and `sql-password` are mapped to Datum's --server, --database, --user and --password.
* If any of them is not used, it has to be set to an empty string to make sure they are ignored.
* Use `sql-datum-options` to provide any of the parameters not included in the standard 4 mentioned above: `--dsn`, `--driver`, `--integrated`, `--config`, `--conn-string`.
* There's an interactive command, `sql-datum`, that will prompt for each parameter, just like `sql-ms`, `sql-oracle`, etc.
* The configuration value `sql-send-terminator` is optional, but encouraged. It means when sending a buffer or active region to the SQLi process, you don't need to manually add a `;;` for the query to be executed immediately.  
  Or maybe you do prefer that, to make execution more explicit 🙂 (thanks to @ghollisjr for reporting)
