;;; cdsware.el -- CDSware-related Emacs definitions people may find useful.
;;; $Id$
;;;
;;; This file is part of the CERN Document Server Software (CDSware).
;;; Copyright (C) 2002 CERN.
;;;
;;; The CDSware is free software; you can redistribute it and/or
;;; modify it under the terms of the GNU General Public License as
;;; published by the Free Software Foundation; either version 2 of the
;;; License, or (at your option) any later version.
;;;
;;; The CDSware is distributed in the hope that it will be useful, but
;;; WITHOUT ANY WARRANTY; without even the implied warranty of
;;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
;;; General Public License for more details.  
;;;
;;; You should have received a copy of the GNU General Public License
;;; along with CDSware; if not, write to the Free Software Foundation, Inc.,
;;; 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

;; switch off the beep
(setq visible-bell t)

;; spaces instead of tabs:
(setq-default indent-tabs-mode nil)

;; no newlines at the end:
(setq next-line-add-newlines nil)

;; fancy parens and such:
(set-scroll-bar-mode 'right)
(setq blink-cursor nil)
(setq transient-mark-mode t)
(show-paren-mode t)

;; light yellow on dark green is cool:
(when (locate-library "color-theme")
    (require 'color-theme)
    (color-theme-gnome2))

;; setting color-syntax highlighting:
(require 'font-lock)
(global-font-lock-mode t)
(setq-default font-lock-auto-fontify t)

;; fancy Python mode:
(when (locate-library "ipython")
  (require 'ipython))

;; most WML files in CDSware are Python files
(setq auto-mode-alist (cons '("\\.wml$" . python-mode) auto-mode-alist))

;; Pythonic things:
(autoload 'python-mode "python-mode" "Python editing mode." t)
(setq interpreter-mode-alist (cons '("python" . python-mode) interpreter-mode-alist))
; add customization by <gb@cs.unc.edu>
(add-hook 'python-mode-hook 'my-python-hook)
; this gets called by outline to deteremine the level. Just use the length of the whitespace
(defun py-outline-level ()
  (let (buffer-invisibility-spec)
    (save-excursion
      (skip-chars-forward "\t ")
      (current-column))))
; this get called after python mode is enabled
(defun my-python-hook ()
  ; outline uses this regexp to find headers. I match lines with no indent and indented "class"
  ; and "def" lines.
  (setq outline-regexp "[^ \t]\\|[ \t]*\\(def\\|class\\) ")
  ; enable our level computation
  (setq outline-level 'py-outline-level)
  ; do not use their \C-c@ prefix, too hard to type. Note this overides some python mode bindings
  (setq outline-minor-mode-prefix "\C-c")
  ; turn on outline mode
  (outline-minor-mode t)
  ; initially hide all but the headers
  (hide-body)
  ; make paren matches visible
  (show-paren-mode 1))              

;; choosing version control software:
(setq vc-default-back-end 'CVS)

;;; end of file