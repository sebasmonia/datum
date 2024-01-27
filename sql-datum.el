;;; sql-datum.el --- Adds Datum as a SQL Product   -*- lexical-binding: t; -*-

;; Copyright (C) 2021-2024 Sebastian Monia
;;
;; Author: Sebastian Monia <smonia@outlook.com>
;; URL: https://github.com/sebasmonia/datum
;; Package-Requires: ((emacs "27.1"))
;; Version: 1.1
;; Keywords: languages processes tools

;; This file is not part of GNU Emacs.

;;; SPDX-License-Identifier: MIT

;;; Commentary:

;; Pre-packaged setup to use Datum as an interface for SQLi buffers.
;; Steps to setup:
;;   1. Place sql-datum.el in your load-path.
;;   2. (require 'sql-datum)
;; Then...
;;   3. M-x sql-datum will prompt for parameters to create a connection
;; - OR -
;;   3. Add to sql-connection-alist an item that uses Datum to connect,
;;      it will show up in the candidates in when calling sql-connect.
;;
;; For a detailed Datum user manual, and additional Emacs setup examples, see:
;; https://github.com/sebasmonia/datum/blob/main/README.md

;;; Code:

(require 'sql)

(defcustom sql-datum-program "datum"
  "Command to start Datum.
See https://github.com/sebasmonia/datum for instructions on how
to install."
  :type 'file
  :group 'SQL)

(defvar sql-datum-login-params nil
  "This value is provided for compatiblity with sql.el, do not change.")

(defvar sql-datum-options nil
  "This value is provided for compatiblity with sql.el, do not change.")

(defun sql-comint-datum (product options &optional buf-name)
  "Create a comint buffer and connect to database using Datum.
PRODUCT is the sql product (datum). OPTIONS are additional
paramaters not defined in the customization. BUF-NAME is the name
for the `comint' buffer."
  ;; Support for "standard" parameter types that might be let-bound
  (let ((parameters (append options
                            (unless (string-empty-p sql-server)
                              (list "--server" sql-server))
                            (unless (string-empty-p sql-database)
                              (list "--database" sql-database))
                            (sql-datum--comint-username)
                            (sql-datum--comint-password))))
    ;; if the connection was started from `sql-connection-alist', only prompt
    ;; when the parameters werent defined
    (if sql-connection
        (unless parameters
          (setf parameters (sql-datum--prompt-connection)))
      ;; but for sql-datum "manual" connections, always prompt
      (setf parameters (sql-datum--prompt-connection)))
    (sql-comint product parameters buf-name)))


(defun sql-datum--comint-username ()
  "Determine the username for the connection.
When `sql-user' is a string, use as-is. If it's the symbol
auth-source, use said package to find the credentials.
Return a list with login values, or nil if the login can't be
determined/found."
  (if (eq 'auth-source sql-user)
      (list "--user" (plist-get (sql-datum--get-auth-source) :user))
    ;; else:  when it's non-empty string, use as-is
    (unless (string-empty-p sql-user)
      (list "--user" sql-user))))

(defun sql-datum--comint-password ()
  "Determine the username for the connection.
When `sql-password' is a string, use as-is. If it's the symbol
auth-source, use said package to find the credentials.
Return a list with passwrod values, or nil if can't be
determined/found."
  (if (eq 'auth-source sql-password)
      (list "--pass" (auth-info-password (sql-datum--get-auth-source)))
    ;; else: read from minibuffer if 'ask
    (if (eq 'ask sql-password)
        (list "--pass" (read-passwd "Password (empty to skip): "))
      ;; finally, if it's non-empty string, use as-is
      (unless (string-empty-p sql-password)
        (list "--pass" sql-password)))))

(defun sql-datum--get-auth-source ()
  "Return the `auth-source' token for the current server@database pair.
Raise an error if no entry is found."
  (require 'auth-source)
  (if-let ((auth-info (car (auth-source-search :host sql-connection
                                               :require '(:secret)))))
      auth-info
    (error "Didn't find the connection \"%s\" in auth-sources"
           sql-connection)))

(defun sql-datum--prompt-connection ()
  "Prompt for datum connection parameters interactively.
This function will \"smartly\" ask for parameters."
  (let ((parameters (if (y-or-n-p "Do you have a DSN? ")
                        (list "--dsn"
                              (read-string "DSN: "))
                      (list "--driver"
                            (read-string "ODBC Driver: ")))))
   (let ((server (read-string "Server (empty to skip): ")))
     (unless (string-empty-p server)
       (setf parameters (append parameters (list "--server" server)))))
   (let ((database (read-string "Database (empty to skip): ")))
     (unless (string-empty-p database)
       (setf parameters (append parameters (list "--database" database)))))
   (let ((user (read-string "Username (empty to skip): "))
         (pass (read-passwd "Password (empty to skip): ")))
     (unless (string-empty-p user)
       (setf parameters (append parameters (list "--user" user))))
     (unless (string-empty-p pass)
       (setf parameters (append parameters (list "--pass" pass))))
     ;; if user and pass are empty ask about integrated security, but
     ;; it is valid that the user says no to all (SQLite)
     (when (and (string-empty-p user) (string-empty-p pass))
       (when (y-or-n-p "No user nor password provided.  Use Integrated security? ")
         (setf parameters (append parameters (list "--integrated"))))))
     (when (y-or-n-p "Specify a config file? ")
       (setf parameters (append parameters (list "--config"
                                                 (read-file-name "Config file path: ")))))
     parameters))

;;;###autoload
(defun sql-datum (&optional buffer)
  "Run Datum as an inferior process.
The buffer with name BUFFER will be used or created."
  (interactive "P")
  ;; when the call is interactive, the sql.el machinery will trip on the
  ;; special symbol values 'auth-source and 'ask, which isn't surprising.
  ;; Usually there's history for these, but that makes 0 sense in the context
  ;; of the symbols, let's clear the values
  (when (or (symbolp sql-user)
            (null sql-user))
    (setf sql-user ""))
  (when (or (symbolp sql-password)
            (null sql-password))
    (setf sql-password ""))
  (sql-product-interactive 'datum buffer))

(sql-add-product 'datum "Datum - ODBC Client"
                 :free-software t
                 :prompt-regexp "^.*>"
                 :prompt-cont-regexp "^.*>"
                 :sqli-comint-func 'sql-comint-datum
                 :sqli-login 'sql-datum-login-params
                 :sqli-program 'sql-datum-program
                 :sqli-options 'sql-datum-options)

(provide 'sql-datum)
;;; sql-datum.el ends here
