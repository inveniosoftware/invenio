;;; $Id$
;;;
;;; cdsware.el -- Emacs definitions people may find useful when
;;; hacking Invenio.  For deeper Emacs customizations and various
;;; tips concerning Invenio development in Emacs, such as how to use
;;; TAGS, CEDET and ECB environments, please see the wiki page:
;;; <https://twiki.cern.ch/twiki/bin/view/CDS/EmacsTips>.
;;;
;;; This file is part of Invenio.
;;; Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
;;;
;;; Invenio is free software; you can redistribute it and/or
;;; modify it under the terms of the GNU General Public License as
;;; published by the Free Software Foundation; either version 2 of the
;;; License, or (at your option) any later version.
;;;
;;; Invenio is distributed in the hope that it will be useful, but
;;; WITHOUT ANY WARRANTY; without even the implied warranty of
;;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
;;; General Public License for more details.
;;;
;;; You should have received a copy of the GNU General Public License
;;; along with Invenio; if not, write to the Free Software Foundation, Inc.,
;;; 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

;; switch off the beep
(setq visible-bell t)

;; spaces instead of tabs:
(setq-default indent-tabs-mode nil)

;; no newlines at the end:
(setq next-line-add-newlines nil)

;; fancy parens and such:
(set-scroll-bar-mode 'right)
(blink-cursor-mode nil)
(setq transient-mark-mode t)
(show-paren-mode t)

;; light yellow on dark green is cool:
(when (locate-library "color-theme")
    (require 'color-theme)
    (color-theme-initialize)
    (color-theme-gnome2))

;; setting color-syntax highlighting:
(require 'font-lock)
(global-font-lock-mode t)
(setq-default font-lock-auto-fontify t)

;; fancy Python mode:
(when (locate-library "ipython")
  (require 'ipython))

;; WebDoc files are like HTML files:
(setq auto-mode-alist (cons '("\\.webdoc$" . html-mode) auto-mode-alist))

;; Pythonic things:
(autoload 'python-mode "python-mode" "Python editing mode." t)
(setq interpreter-mode-alist (cons '("python" . python-mode) interpreter-mode-alist))
(defun pylint ()
    "Run pylint against the file behind the current buffer after
    checking if unsaved buffers should be saved."
    (interactive)
    (let* ((file (buffer-file-name (current-buffer)))
	   (command (concat "pylint -f parseable " file)))
      (save-some-buffers (not compilation-ask-about-save) nil) ; save  files.
      (compile-internal command "No more errors or warnings" "pylint")))
(global-set-key "\C-cp" 'pylint)
(global-set-key "\C-cw" 'py-pychecker-run)

; workaround for Emacs22 and pylint/pychecker:
(setq compilation-scroll-output t)

;; choosing version control software:
(setq vc-default-back-end 'CVS)

;; warn about trailing whitespaces:
(mapc (lambda (hook)
	(add-hook hook (lambda ()
			 (setq show-trailing-whitespace t))))
      '(text-mode-hook
	emacs-lisp-mode-hook
	python-mode-hook
	shell-script-mode-hook))

;;; end of file