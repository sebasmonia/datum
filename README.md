# Datum

An attempt at a cleaner version of [sqlcmdline](https://github.com/sebasmonia/sqlcmdline/). Unlike that tool, this one doesn't try to mimic [sqlcmd](https://docs.microsoft.com/en-us/sql/tools/sqlcmd-utility) and instead is built from scratch to be compatible with more DB engines. It also pip-installable from this repository.  

## Table of contents

<!--ts-->

   * [Installation](#installation)
   * [Usage](#usage)
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

## Usage

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
The alternative is to provide either a DSN, or an ODBC driver to use. A DSN might contain all the information needed, or skip some parameters (for example, the auth portion) so you can still add more values to the mix.  
You can interpolate environment variables in your shell of choice, a (hopefully) simpler alternative is to start a value with `ENV=`. For example `--pass=ENV=DB_SECRET` would get the value for the password from $DB_SECRET / %DB_SECRET%.

## Configuration file

There's an option to provide an INI file to setup the start up value of Datum's config and optionally provide custom "commands" (more on this in the relevant section).  
The value for `--config` defaults to `config.ini`. It is accessed as-is (in case you specify a filename in the current directory or a full path), and if not found then it is assumed to be a file in the directory `$XDG_CONFIG_HOME/datum` or `$HOME/.config/datum` (or `%USERPROFILE%\.config\datum` on Windows). This is convenient in case you want to define custom queries for example per DB-engine using files named `mssql.ini`, `mariadb.ini`, `sqlite.ini`, etc. Then you can just drop all the files in the Datum `.config` directory and use e.g. `--config=sqlite.ini` when you connect to a SQLite DB. You could also store custom queries per-database in separate files, and so on.  
&nbsp;  
The repository for Datum includes a throughly documented sample [config.ini](https://raw.githubusercontent.com/sebasmonia/datum/main/config.ini) file. Note that the file is completely optional, and all configuration can be modified at runtime.

## Commands

**TBD**  

## Custom commands

**TBD**  

## Emacs SQLi mode setup

**TBD**  

