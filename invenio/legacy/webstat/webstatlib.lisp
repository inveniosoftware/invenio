;;; webstatlib.lisp -- library with httpd log file analyzer to gather
;;; CDS usage stats.  Another functionality is to parse old Apache log
;;; files and prepare Detailed record page views statistics for
;;; rnkPAGEVIEWS table.
;;;
;;; This file is part of Invenio.
;;; Copyright (C) 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

;;
;; Auxiliary functions come first.

#-gcl (in-package #:cl-user)

(defpackage #:webstatlib
  #-gcl (:use #:cl)
  (:export #:print-general-stats
           #:print-search-interface-stats
           #:print-search-collections-stats
           #:print-search-pattern-stats
           #:print-basket-stats
           #:print-alert-stats
           #:print-download-stats))

#-gcl (proclaim '(optimize (speed 3) (safety 1) (debug 0) (compilation-speed 0) (space 0)))

(defun parse-integer-or-zero (string)
  "Parse integer from STRING and return either the integer, or zero."
  (let ((out 0))
    (if (string-not-equal string "-")
        (setf out (parse-integer string)))
    out))

(defun hash-table-keys (hashtable &optional (sort-by-value nil))
  "Return list of HASHTABLE keys.  Optionally, sort the key list by
hash value."
  (let ((keys '()))
    (maphash (lambda (key val)
               (declare (ignore val))
               (push key keys))
             hashtable)
    (if sort-by-value
        (sort keys #'(lambda (x y)
                       (let ((x-val (gethash x hashtable))
                             (y-val (gethash y hashtable)))
                         (if (equalp x-val y-val)
                             (string< x y) ; when values are equal, test by keys
                             (> x-val y-val)))))
        keys)))

(defun hash-table-values (hashtable)
  "Return list of HASHTABLE values."
  (let ((vals '()))
    (maphash (lambda (key val)
               (declare (ignore key))
               (push val vals))
             hashtable)
    vals))

(defun hash-table-key-val-stats (hashtable predicate
                                 &optional (apply-predicate-to-vals nil))
  "Return the number of keys in HASHTABLE that satisfy the PREDICATE.
Another returned value is the sum of values for these keys.  Suitable
when values are integers, as in histograms."
  (declare (type function predicate))
  (let ((number-of-keys 0)
        (sum-of-values 0))
    (declare (type fixnum number-of-keys sum-of-values))
    (maphash (lambda (key val)
               (if apply-predicate-to-vals
                   (when (funcall predicate val)
                     (incf number-of-keys)
                     (incf sum-of-values val))
                   (when (funcall predicate key)
                     (incf number-of-keys)
                     (incf sum-of-values val))))
             hashtable)
    (values number-of-keys sum-of-values)))

(defun split-string-by-one-space (string)
    "Return list of substrings of STRING divided by *one* space each.
Two consecutive spaces will be seen as if there were an empty string
between them.  Taken from Common Lisp Cookbook."
    (declare (type simple-base-string string))
    (loop for i = 0 then (1+ j)
          as j = (position #\Space string :start i)
          collect (subseq string i j)
          while j))

(defun split-string-by-equal-sign (string)
    "Return list of two substrings of STRING around one equal sign,
stripping any whitespace. Return nil if the equal sign was not found."
    (declare (type simple-base-string string))
    (let ((pos (position #\= string)))
      (if pos
          (values (string-trim " " (subseq string 0 pos))
                  (string-trim " " (subseq string (1+ pos))))
          nil)))

(defun string-substitute (string substring replacement-string)
  "Taken from c.l.l."
  (declare (type simple-base-string string substring replacement-string))
  (let ((substring-length (length substring))
        (last-end 0)
        (new-string ""))
    (declare (type simple-base-string new-string)
             (type integer substring-length last-end))
    (do ((next-start
          (search substring string)
          (search substring string :start2 last-end)))
        ((null next-start)
         (concatenate 'string new-string (subseq string last-end)))
      (declare (type (or integer null) next-start))
      (setq new-string
            (concatenate 'string
                         new-string
                         (subseq string last-end next-start)
                         replacement-string))
      (setq last-end (+ next-start substring-length)))))

(defun string-decode-url (string)
  "Return string where URL is unquoted, that is %22 is substituted by
a double quote, etc."
  (declare (type simple-base-string string))
  (setf string (string-substitute string "%20" " "))
  (setf string (string-substitute string "+" " "))
  (setf string (string-substitute string "%2B" "+"))
  (setf string (string-substitute string "%22" "\""))
  (setf string (string-substitute string "%23" "#"))
  (setf string (string-substitute string "%25" "%"))
  (setf string (string-substitute string "%26" "&"))
  (setf string (string-substitute string "%27" "'"))
  (setf string (string-substitute string "%28" "("))
  (setf string (string-substitute string "%29" ")"))
  (setf string (string-substitute string "%2A" "*"))
  (setf string (string-substitute string "%2C" ","))
  (setf string (string-substitute string "%2F" "/"))
  (setf string (string-substitute string "%3A" ":"))
  (setf string (string-substitute string "%3D" "="))
  (setf string (string-substitute string "%3E" ">"))
  (setf string (string-substitute string "%3F" "?"))
  (setf string (string-substitute string "%5B" "["))
  (setf string (string-substitute string "%5C" "\\"))
  (setf string (string-substitute string "%5D" "]")))

(defun get-month-number-from-month-name (month-name)
  "Return month number for MONTH-NAME."
  (declare (type simple-base-string month-name))
  (cond ((string= month-name "Jan") 1)
        ((string= month-name "Feb") 2)
        ((string= month-name "Mar") 3)
        ((string= month-name "Apr") 4)
        ((string= month-name "May") 5)
        ((string= month-name "Jun") 6)
        ((string= month-name "Jul") 7)
        ((string= month-name "Aug") 8)
        ((string= month-name "Sep") 9)
        ((string= month-name "Oct") 10)
        ((string= month-name "Nov") 11)
        ((string= month-name "Dec") 12)
        (t 0)))

(defun get-urlarg-values-from-url-string (url-string url-arg
                                          &optional (return-empty-value nil))
  "Return list of values of URL-ARG in the URL-STRING.  For example,
if URL-STRING contains 'search?p=ellis&f=title', and URL-ARG is
'f', then return list of 'title'.  If URL-ARG is not present in
URL-STRING, return list of empty string."
  (declare (type simple-base-string url-string url-arg))
  (let ((out nil)
        (position-pattern-beg nil)
        (position-pattern-end nil))
    (setf position-pattern-beg (search (concatenate 'string url-arg "=")
                                       url-string))
    (if (not position-pattern-beg)
        (progn
          (when return-empty-value
            (push "" out)))
        (progn
          (setf position-pattern-end (search "&" url-string
                                             :start2 position-pattern-beg))
          (if (null position-pattern-end)
              (setf position-pattern-end (length url-string)))
          (push (string-decode-url (subseq url-string
                                           (+ (length url-arg) 1 position-pattern-beg)
                                           position-pattern-end))

                out)))
    (if return-empty-value
        out
        (remove-if #'(lambda (x)
                       (declare (type simple-base-string x))
                       (string= "" x))
                   out))))

(defun get-datetime-from-httpd-log-datetime-string (httpd-log-datetime-string)
  "Return request date in numerical format YYYYMMDD from HTTPD-LOG-DATETIME-STRING."
  (declare (type simple-base-string httpd-log-datetime-string))
  (let ((yyyy (subseq httpd-log-datetime-string 7 11))
        (mm-number (get-month-number-from-month-name (subseq httpd-log-datetime-string 3 6)))
        (dd (subseq httpd-log-datetime-string 0 2)))
    (declare (type fixnum mm-number))
    (+ (* 100 100 (parse-integer yyyy))
       (* 100 mm-number)
       (parse-integer dd))))

(defun get-datetimee-from-httpd-log-datetime-string (httpd-log-datetime-string)
  "Return request date in the format YYYY-MM-DD HH:MM:SS from HTTPD-LOG-DATETIME-STRING."
  (declare (type simple-base-string httpd-log-datetime-string))
  (let ((yyyy (subseq httpd-log-datetime-string 7 11))
        (mm (get-month-number-from-month-name (subseq httpd-log-datetime-string 3 6)))
        (dd (subseq httpd-log-datetime-string 0 2))
        (hms (subseq httpd-log-datetime-string 12 20)))
    (format nil "~A-~A-~A ~A" yyyy mm dd hms)))

(defun get-current-collection-from-httpd-log-request-string (httpd-log-request-string)
  "Return current collection found in HTTPD-LOG-REQUEST-STRING.
Examples of input: 'search?cc=Books', '/?c=Books', '/collection/Books?ln=en'."
  (declare (special *home-collection*))
  (let ((out nil)
        (url-string (subseq httpd-log-request-string
                            (position #\space httpd-log-request-string)
                            (position #\space httpd-log-request-string :from-end t))))
    (if (search "?cc=" url-string)
        (setf out (get-urlarg-values-from-url-string url-string "cc" t))
        (if (search "?c=" url-string)
            (setf out (get-urlarg-values-from-url-string url-string "c" t))
            (if (search "/collection/" url-string)
                (setf out (list (string-decode-url (subseq url-string
                                                           (+ (search "/collection/" url-string) (length "/collection/"))
                                                           (search "?ln=" url-string :from-end t)))))
                (setf out (list *home-collection*)))))
    (if (string= (car out) "")
        (setf out (list *home-collection*)))
    out))

(defun get-search-patterns-from-httpd-log-request-string (httpd-log-request-string)
  "Return list of search pattern strings (p=,p1=,p2=,p3=) found in
HTTPD-LOG-REQUEST-STRING.  As a side effect, increment counters for
*NUMBER-OF-SIMPLE-SEARCHES* and *NUMBER-OF-DETAILED-RECORD-PAGES* when
a simple search or a detailed record page is selected."
  (declare (type simple-base-string httpd-log-request-string)
           (special *search-engine-url*
                    *search-engine-url-old-style*
                    *detailed-record-url*
                    *number-of-simple-searches*
                    *number-of-advanced-searches*
                    *number-of-detailed-record-pages*))
  (let ((out nil)
        (url-string (subseq httpd-log-request-string
                            (position #\space httpd-log-request-string)
                            (position #\space httpd-log-request-string :from-end t))))
    ;; url-string now contains URL without leading GET and trailing HTTP/1.1 strings
    (when (or (search *search-engine-url* url-string)
              (search *search-engine-url-old-style* url-string)
              (search *detailed-record-url* url-string))
      (if (or (search *detailed-record-url* url-string)
              (search "?id=" url-string)
              (search "?recid=" url-string)
              (search "?sysno=" url-string)
              (search "?sysnb=" url-string))
          ;; detailed record page happened:
          (incf *number-of-detailed-record-pages*)
          (if (search "p1=" httpd-log-request-string)
              ;; advanced search happened:
              (progn
                (incf *number-of-advanced-searches*)
                (setf out (append (get-urlarg-values-from-url-string url-string "p1")
                                  (get-urlarg-values-from-url-string url-string "p2")
                                  (get-urlarg-values-from-url-string url-string "p3"))))
              ;; simple search happened:
              (progn
                (incf *number-of-simple-searches*)
                (setf out (get-urlarg-values-from-url-string url-string "p" t))))))
    out))

(defun wash-httpd-log-line (httpd-log-line)
  "Fix eventual problems in HTTPD-LOG-LINE, such as backslash-quote
that some browsers seem to produce.  To be called for the input to
wash it out."
  (declare (type simple-base-string httpd-log-line))
  (string-substitute httpd-log-line "\\\"" "%22"))

;; HTTPD-LOG-ENTRY stucture that will represent Apache log hits, and
;; functions to create it.

(defstruct httpd-log-entry
  "Structure representing Apache combined log entry."
  (ip "" :type simple-base-string)
  (datetime 0 :type integer)             ; YYYYMMDD              (FIXME: get rid of this)
  (datetimee "" :type simple-base-string) ; YYYY-MM-DD HH:MM:SS
  (request "" :type simple-base-string)
  (status 0 :type integer)
  (bytes 0 :type integer)
  (referer "" :type simple-base-string)
  (browser "" :type simple-base-string))

(defun parse-httpd-log-line-conses-a-lot (line)
  "Return list of elements read from Apache combined log LINE.  The
elements in line are text strings delimited either by spaces or by
double quotes or brackets.  (Spaces within double quotes or brackets
do not take their separator effect.  Double quote preceded by a
backslash do not take its effect neither.)  WARNING: THIS FUNCTION
CONSES A LOT, A FASTER REWRITE IS AVAILABLE BELOW."
  (declare (type simple-base-string line))
  (if (string= line "")
      nil
      (let ((current-char (char line 0))
            (position-term-next nil)
            (position-term-offset 0))
        (declare (type (or fixnum null) position-term-next position-term-offset)
                 (type character current-char))
        (cond ((char= current-char #\")
               (setf position-term-next (position #\" line :start 1)
                     position-term-offset 1))
              ((char= current-char #\[)
               (setf position-term-next (position #\] line :start 1)
                     position-term-offset 1))
              (t (setf position-term-next (position #\Space line :start 1))))
        (if (or (null position-term-next)
                (>= (+ 1 position-term-next position-term-offset) (length line)))
            (list (subseq line position-term-offset))
            (append (list (subseq line position-term-offset position-term-next))
                    (parse-httpd-log-line (subseq line
                                                  (+ 1
                                                     position-term-next
                                                     position-term-offset))))))))

(defun parse-httpd-log-line (line)
  "Return list of elements read from Apache combined log LINE.  The
elements in line are text strings delimited either by spaces or by
double quotes or brackets.  (Spaces within double quotes or brackets
do not take their separator effect.  Double quote preceded by a
backslash do not take its effect neither.)"
  (declare (type simple-base-string line))
  (labels ((get-next-char-to-search (current-char)
             (declare (type character current-char))
             (cond ((char= current-char #\[) #\])
                   ((char= current-char #\") #\")
                   (t #\space)))
           (get-char-offset (current-char)
             (declare (type character current-char))
             (cond ((char= current-char #\[) 1)
                   ((char= current-char #\") 1)
                   (t 0))))
    (let* ((out nil)
           (position-max (1- (length line)))
           (position-term 0)
           (position-term-offset (get-char-offset (char line position-term)))
           (position-term-next (position (get-next-char-to-search (char line position-term))
                                         line
                                         :start (+ position-term-offset position-term))))
      (declare (type (or integer null) position-term position-term-next)
               (type integer position-max position-term-offset))
      (loop (when (null position-term-next)
              (when (< position-term position-max)
                (push (subseq line (+ position-term position-term-offset)) out))
              (return (nreverse out)))
            (push (subseq line (+ position-term position-term-offset) position-term-next) out)
            (setf position-term (min (+ 1 position-term-next position-term-offset)
                                     position-max))
            (setf position-term-offset (get-char-offset (char line position-term)))
            (setf position-term-next (position (get-next-char-to-search (char line position-term))
                                               line
                                               :start (+ position-term position-term-offset)))))))

(defun create-httpd-log-entry (httpd-log-line)
  "Create HTTPD-LOG-ENTRY structure from HTTPD-LOG-LINE Apache
combined log line.  The line is supposed to be washed already."
  (declare (type simple-base-string httpd-log-line))
  ; firstly parse Apache line according to spaces and quotes into list:
  (let ((httpd-log-line-list (parse-httpd-log-line httpd-log-line)))
    ;; secondly transform into entry:
    (make-httpd-log-entry :ip (nth 0 httpd-log-line-list)
                          :request (nth 4 httpd-log-line-list)
                          :datetime (get-datetime-from-httpd-log-datetime-string
                                     (nth 3 httpd-log-line-list))
                          :datetimee (get-datetimee-from-httpd-log-datetime-string
                                     (nth 3 httpd-log-line-list))
                          :status (parse-integer (nth 5 httpd-log-line-list))
                          :bytes (parse-integer-or-zero (nth 6 httpd-log-line-list))
                          :referer (nth 7 httpd-log-line-list)
                          :browser (nth 8 httpd-log-line-list))))

(defun create-httpd-log-entries (httpd-log-filename
                                 &optional (exclude-ip-list nil))
  "Create list of HTTPD-LOG-ENTRY structures from HTTPD-LOG-FILENAME
Apache combined log file.  The log file lines are cleaned to make them
valid, if necessary.  When EXCLUDE-IP-LIST is set, then lines coming
from those IPs are excluded."
  (declare (type simple-base-string httpd-log-filename)
           (type list exclude-ip-list))
  (let ((httpd-log-entries nil))
    (format t "~&** APACHE LOG FILE ANALYSIS")
    (format t "~&Filename: ~A" httpd-log-filename)
    (unless (null exclude-ip-list)
      (format t "~&Excluding search engine hits from ~A." exclude-ip-list))
    (with-open-file (input-stream httpd-log-filename :direction :input)
      (do ((line (read-line input-stream nil)
                 (read-line input-stream nil)))
          ((not line))
        (declare (type (or simple-base-string null) line))
        (let ((httpd-log-entry-item (create-httpd-log-entry (wash-httpd-log-line line))))
          (if (or (null exclude-ip-list)
                  (not (member (httpd-log-entry-ip httpd-log-entry-item)
                               exclude-ip-list :test #'equal)))
              (push httpd-log-entry-item httpd-log-entries)))))
    httpd-log-entries))

(defun filter-httpd-log-entries (httpd-all-log-entries url-substring-pattern
                                 &optional (status-code 200))
  "Return only those of HTTPD-ALL-LOG-ENTRIES that satisfy
URL-SUBSTRING-PATTERN and are of status STATUS-CODE."
  (remove-if-not #'(lambda (httpd-log-entry-item)
                     (and (search url-substring-pattern (httpd-log-entry-request httpd-log-entry-item))
                          (= status-code (httpd-log-entry-status httpd-log-entry-item))))
                 httpd-all-log-entries))

;; Functions that analyze the files according to the typical use cases.

(defun print-general-stats (httpd-all-log-entries)
  "Read HTTPD-LOG-ENTRIES and print some general stats such as
the total number of hits, etc."
  (declare (special *nb-histogram-items-to-print*))
  (format t "~&~%** GENERAL STATS")
  (let ((nb-hits (length httpd-all-log-entries))
        (datetime-last (httpd-log-entry-datetime (car httpd-all-log-entries)))
        (datetime-first (httpd-log-entry-datetime (car (last httpd-all-log-entries))))
        (visitor-histogram (make-hash-table :test #'equalp)))
    ;; build histogram:
    (dolist (httpd-log-entry-item httpd-all-log-entries)
      (incf (gethash (httpd-log-entry-ip httpd-log-entry-item)
                     visitor-histogram 0)))
    ;; print summary info:
    (format t "~&There were ~D website hits dating from ~A to ~A."
            nb-hits datetime-first datetime-last)
    (format t "~&This makes an average of ~F website hits per day."
            (/ nb-hits (1+ (- datetime-last datetime-first))))
    (format t "~&There were ~D unique visitors in ~D days."
            (length (hash-table-keys visitor-histogram))
            (1+ (- datetime-last datetime-first)))
    ;; print visitors histogram:
    (format t "~&~80,1,0,'.<~A ~; ~A~>" "Visitor" "no. of hits")
    (let ((visitors-to-print (hash-table-keys visitor-histogram t)))
      (if (> (length visitors-to-print) *nb-histogram-items-to-print*)
          (setq visitors-to-print (subseq visitors-to-print 0 *nb-histogram-items-to-print*)))
      (dolist (visitor visitors-to-print)
        (format t "~&~80,1,0,'.<~A ~; ~A~>" visitor
                (gethash visitor visitor-histogram))))))

(defun print-search-interface-stats (httpd-all-log-entries)
  "Read HTTPD-ALL-LOG-ENTRIES, analyze search interface usage and print
interesting statistics."
  (declare (special *search-interface-url*
                    *search-interface-url-old-style*
                    *home-collection*
                    *nb-histogram-items-to-print*))
  (let ((httpd-log-entries (append (filter-httpd-log-entries httpd-all-log-entries *search-interface-url*)
                                   (filter-httpd-log-entries httpd-all-log-entries *search-interface-url-old-style*)))
        (collection-histogram (make-hash-table :test #'equalp)))
    ;; build histogram:
    (dolist (httpd-log-entry httpd-log-entries)
      (dolist (current-collection (get-current-collection-from-httpd-log-request-string
                                   (httpd-log-entry-request
                                    httpd-log-entry)))
        (incf (gethash current-collection collection-histogram 0))))
    ;; print summary info:
    (format t "~&~%** SEARCH INTERFACE COLLECTIONS USAGE ANALYSIS")
    (let ((number-of-interface-visits
           (reduce #'+ (hash-table-values collection-histogram))))
      (format t "~&There were ~D visits of search interface pages."
              number-of-interface-visits)
      (format t "~&There were ~D visits of non-Home search interface pages. (~4F\%)"
              (- number-of-interface-visits (gethash *home-collection* collection-histogram 0))
              (if (zerop number-of-interface-visits)
                  0
                  (* 100 (/ (gethash *home-collection* collection-histogram 0)
                            number-of-interface-visits)))))
    ;; print histogram:
    (format t "~&~80,1,0,'.<~A ~; ~A~>" "Collection" "no. of visits")
    (let ((collections-to-print (hash-table-keys collection-histogram t)))
      (if (> (length collections-to-print) *nb-histogram-items-to-print*)
          (setq collections-to-print (subseq  collections-to-print 0 *nb-histogram-items-to-print*)))
      (dolist (collection collections-to-print)
        (format t "~&~80,1,0,'.<~A ~; ~A~>" collection
                (gethash collection collection-histogram))))))

(defun print-search-collections-stats (httpd-all-log-entries)
  "Read HTTPD-ALL-LOG-ENTRIES, analyze search engine usage and print
interesting statistics with respect to collections."
  (declare (special *search-engine-url*
                    *search-engine-url-old-style*
                    *home-collection*
                    *nb-histogram-items-to-print*))
  (let ((httpd-log-entries (append (filter-httpd-log-entries httpd-all-log-entries *search-engine-url*)
                                   (filter-httpd-log-entries httpd-all-log-entries *search-engine-url-old-style*)))
        (collection-histogram (make-hash-table :test #'equalp)))
    ;; build histogram:
    (dolist (httpd-log-entry httpd-log-entries)
      (if (or (search "c=" (httpd-log-entry-request httpd-log-entry))
              (search "cc=" (httpd-log-entry-request httpd-log-entry)))
          (dolist (current-collection (get-current-collection-from-httpd-log-request-string
                                       (httpd-log-entry-request
                                        httpd-log-entry)))
            (incf (gethash current-collection collection-histogram 0)))))
    ;; print summary info:
    (format t "~&~%** SEARCH ENGINE COLLECTIONS USAGE ANALYSIS")
    (let ((number-of-interface-visits
           (reduce #'+ (hash-table-values collection-histogram))))
      (format t "~&There were ~D search engine hits."
              number-of-interface-visits)
      (format t "~&There were ~D searches originating from non-Home collections. (~4F\%)"
              (- number-of-interface-visits (gethash *home-collection* collection-histogram 0))
              (* 100 (/ (gethash *home-collection* collection-histogram 0) number-of-interface-visits))))
    ;; print histogram:
    (format t "~&~80,1,0,'.<~A ~; ~A~>" "Originating collection"  "no. of searches")
    (let ((collections-to-print (hash-table-keys collection-histogram t)))
      (if (> (length collections-to-print) *nb-histogram-items-to-print*)
          (setq collections-to-print (subseq collections-to-print 0 *nb-histogram-items-to-print*)))
      (dolist (collection collections-to-print)
        (format t "~&~80,1,0,'.<~A ~; ~A~>" collection
                (gethash collection collection-histogram))))))

(defun print-search-pattern-stats (httpd-all-log-entries)
  "Read HTTPD-ALL-LOG-ENTRIES, analyze search patterns and print
interesting statistics."
  (declare (special *search-engine-url*
                    *search-engine-url-old-style*
                    *nb-histogram-items-to-print*
                    *number-of-simple-searches*
                    *number-of-advanced-searches*
                    *number-of-detailed-record-pages*))
  (setf *number-of-simple-searches* 0
        *number-of-advanced-searches* 0
        *number-of-detailed-record-pages* 0)
  (let ((httpd-log-entries (append (filter-httpd-log-entries httpd-all-log-entries *search-engine-url*)
                                   (filter-httpd-log-entries httpd-all-log-entries *search-engine-url-old-style*)))
        (pattern-histogram (make-hash-table :test #'equalp)))
    ;; build histogram:
    (dolist (httpd-log-entry httpd-log-entries)
      (dolist (pattern (get-search-patterns-from-httpd-log-request-string (httpd-log-entry-request
                                                                           httpd-log-entry)))
        (incf (gethash pattern pattern-histogram 0))))
    ;; print summary info:
    (format t "~&~%** SEARCH ENGINE QUERY PATTERN ANALYSIS")
    (if (null httpd-log-entries)
        (format t "~&No valid search engine hits found.  Exiting.")
        (let ((number-of-search-engine-hits (length httpd-log-entries))
              (number-of-patterns (hash-table-count pattern-histogram))
              (day-first (httpd-log-entry-datetime (nth (1- (length httpd-log-entries))
                                                        httpd-log-entries)))
              (day-last (httpd-log-entry-datetime (first httpd-log-entries))))
          (declare (type integer number-of-search-engine-hits
                         number-of-patterns day-first day-last))
          ;; a - total number of searches and patterns
          (format t "~&Found ~D search engine hits." number-of-search-engine-hits)
          (format t "~&First search engine hit log is dated ~A." day-first)
          (format t "~&Last search engine hit log is dated ~A." day-last)
          (format t "~&This makes an average of ~F search engine hits per day."
                  (/ number-of-search-engine-hits (1+ (- day-last day-first))))
          (format t "~&There were ~D simple searches out of ~D search engine hits. (~4F\%)"
                  *number-of-simple-searches* number-of-search-engine-hits
                  (* 100 (/ *number-of-simple-searches* number-of-search-engine-hits)))
          (format t "~&There were ~D advanced searches out of ~D search engine hits. (~4F\%)"
                  *number-of-advanced-searches* number-of-search-engine-hits
                  (* 100 (/ *number-of-advanced-searches* number-of-search-engine-hits)))
          (format t "~&There were ~D detailed record pages out of ~D search engine hits. (~4F\%)"
                  *number-of-detailed-record-pages* number-of-search-engine-hits
                  (* 100 (/ *number-of-detailed-record-pages* number-of-search-engine-hits)))
          (format t "~&There are ~D different query patterns for ~D search engine hits. (~4F\%)"
                  number-of-patterns number-of-search-engine-hits
                  (* 100 (/ number-of-patterns number-of-search-engine-hits)))
          ;; b - empty searches
          (format t "~&There are ~D empty query pattern searches out of ~D search engine hits. (~4F\%)"
                  (gethash "" pattern-histogram 0)
                  number-of-search-engine-hits
                  (* 100 (/ (gethash "" pattern-histogram 0) number-of-search-engine-hits)))
          ;; c - phrase searches and patterns
          (multiple-value-bind (number-of-phrase-patterns number-of-phrase-searches)
              (hash-table-key-val-stats pattern-histogram #'(lambda (x)
                                                              (declare (type simple-base-string x))
                                                              (position #\" x)))
            (format t "~&There are ~D phrase searches out of ~D search engine hits. (~4F\%)"
                    number-of-phrase-searches
                    number-of-search-engine-hits
                    (* 100 (/ number-of-phrase-searches number-of-search-engine-hits)))
            (format t "~&There are ~D phrase query patterns out of ~D query patterns. (~4F\%)"
                    number-of-phrase-patterns
                    number-of-patterns
                    (* 100 (/ number-of-phrase-patterns number-of-patterns))))
          ;; d - onetime searches and patterns
          (multiple-value-bind (number-of-onetime-patterns number-of-onetime-searches)
              (hash-table-key-val-stats pattern-histogram #'(lambda (x)
                                                              (declare (integer x))
                                                              (= x 1)) t)
            (format t "~&There are ~D one-time event searches out of ~D search engine hits. (~4F\%)"
                    number-of-onetime-searches
                    number-of-search-engine-hits
                    (* 100 (/ number-of-onetime-searches number-of-search-engine-hits)))
            (format t "~&There are ~D one-time query patterns out of ~D query patterns. (~4F\%)"
                    number-of-onetime-patterns
                    number-of-patterns
                    (* 100 (/ number-of-onetime-patterns number-of-patterns))))
          ;; e - one-word searches and patterns
          (multiple-value-bind (number-of-oneword-patterns number-of-oneword-searches)
              (hash-table-key-val-stats pattern-histogram #'(lambda (x)
                                                              (declare (type simple-base-string x))
                                                              (not (position #\space x))))
            (format t "~&There are ~D one-word searches out of ~D search engine hits. (~4F\%)"
                    number-of-oneword-searches
                    number-of-search-engine-hits
                    (* 100 (/ number-of-oneword-searches number-of-search-engine-hits)))
            (format t "~&There are ~D one-word query patterns out of ~D query patterns. (~4F\%)"
                    number-of-oneword-patterns
                    number-of-patterns
                    (* 100 (/ number-of-oneword-patterns number-of-patterns))))
          ;; f - wildcard queries and patterns
          (multiple-value-bind (number-of-wildcard-patterns number-of-wildcard-searches)
              (hash-table-key-val-stats pattern-histogram #'(lambda (x)
                                                              (declare (type simple-base-string x))
                                                              (position #\* x)))
            (format t "~&There are ~D wildcard searches out of ~D search engine hits. (~4F\%)"
                    number-of-wildcard-searches
                    number-of-search-engine-hits
                    (* 100 (/ number-of-wildcard-searches number-of-search-engine-hits)))
            (format t "~&There are ~D wildcard query patterns out of ~D query patterns. (~4F\%)"
                    number-of-wildcard-patterns
                    number-of-patterns
                    (* 100 (/ number-of-wildcard-patterns number-of-patterns))))
          ;; g - punctuation-like queries and patterns
          (multiple-value-bind (number-of-punctuation-patterns number-of-punctuation-searches)
              (hash-table-key-val-stats pattern-histogram #'(lambda (x)
                                                              (declare (type simple-base-string x))
                                                              (or (position #\+ x)
                                                                  (position #\- x)
                                                                  (position #\/ x))))
            (format t "~&There are ~D punctuation-like searches out of ~D search engine hits. (~4F\%)"
                    number-of-punctuation-searches
                    number-of-search-engine-hits
                    (* 100 (/ number-of-punctuation-searches number-of-search-engine-hits)))
            (format t "~&There are ~D punctuation-like query patterns out of ~D query patterns. (~4F\%)"
                    number-of-punctuation-patterns
                    number-of-patterns
                    (* 100 (/ number-of-punctuation-patterns number-of-patterns))))
          ;; h - anyfield queries and patterns
          (multiple-value-bind (number-of-anyfield-patterns number-of-anyfield-searches)
              (hash-table-key-val-stats pattern-histogram #'(lambda (x)
                                                              (declare (type simple-base-string x))
                                                              (not (position #\: x))))
            (declare (ignore number-of-anyfield-searches))
            (format t "~&There are ~D any-field query patterns out of ~D query patterns. (~4F\%)"
                    number-of-anyfield-patterns
                    number-of-patterns
                    (* 100 (/ number-of-anyfield-patterns number-of-patterns))))
          ;; print detailed histogram:
          (format t "~&~80,1,0,'.<~A ~; ~A~>" "User query"  "no. of occurrences")
          (let ((patterns-to-print (hash-table-keys pattern-histogram t)))
            (if (> (length patterns-to-print) *nb-histogram-items-to-print*)
                (setq patterns-to-print (subseq patterns-to-print 0 *nb-histogram-items-to-print*)))
            (dolist (pattern patterns-to-print)
              (format t "~&~80,1,0,'.<~A ~; ~A~>" pattern
                      (gethash pattern pattern-histogram))))))))

(defun print-basket-stats (httpd-all-log-entries)
  "Read HTTPD-LOG-ENTRIES and print stats related to user baskets."
  (declare (special *basket-url*
                    *add-to-basket-url*
                    *display-basket-url*
                    *display-public-basket-url*))
  (let ((datetime-first (httpd-log-entry-datetime (car httpd-all-log-entries)))
        (datetime-last (httpd-log-entry-datetime (car (last httpd-all-log-entries))))
        (httpd-log-entries (filter-httpd-log-entries httpd-all-log-entries *basket-url*))
        (basket-user-histogram (make-hash-table :test #'equalp)))
    ;; build basket users histogram:
    (dolist (httpd-log-entry-item httpd-log-entries)
      (incf (gethash (httpd-log-entry-ip httpd-log-entry-item)
                     basket-user-histogram 0)))
    (format t "~&~%** USER BASKETS STATS")
    ;; print basket usage summary info:
    (format t "~&There were ~D user basket page hits." (length httpd-log-entries))
    (format t "~&This makes an average of ~F user basket page hits per day."
            (/ (length httpd-log-entries) (1+ (- datetime-last datetime-first))))
    (format t "~&There were ~D unique basket page users in ~D days."
            (length (hash-table-keys basket-user-histogram))
            (1+ (- datetime-last datetime-first)))
    ;; add to basket:
    (format t "~&There were ~D additions to baskets."
            (length (filter-httpd-log-entries httpd-log-entries *add-to-basket-url*)))
    ;; display baskets:
    (format t "~&There were ~D displays of baskets, out of which ~D public baskets accesses."
            (length (filter-httpd-log-entries httpd-log-entries *display-basket-url*))
            (length (filter-httpd-log-entries httpd-log-entries *display-public-basket-url*)))))

(defun print-alert-stats (httpd-all-log-entries)
  "Read HTTPD-LOG-ENTRIES and print stats related to user alerts."
  (declare (special *alert-url*
                    *display-your-alerts-url*
                    *display-your-searches-url*))
  (let ((datetime-first (httpd-log-entry-datetime (car httpd-all-log-entries)))
        (datetime-last (httpd-log-entry-datetime (car (last httpd-all-log-entries))))
        (httpd-log-entries (filter-httpd-log-entries httpd-all-log-entries *alert-url*))
        (alert-user-histogram (make-hash-table :test #'equalp)))
    ;; build alert users histogram:
    (dolist (httpd-log-entry-item httpd-log-entries)
      (incf (gethash (httpd-log-entry-ip httpd-log-entry-item)
                     alert-user-histogram 0)))
    (format t "~&~%** USER ALERTS STATS")
    ;; print alert usage summary info:
    (format t "~&There were ~D user alert page hits." (length httpd-log-entries))
    (format t "~&This makes an average of ~F user alert page hits per day."
            (/ (length httpd-log-entries) (1+ (- datetime-last datetime-first))))
    (format t "~&There were ~D unique alert page users in ~D days."
            (length (hash-table-keys alert-user-histogram))
            (1+ (- datetime-last datetime-first)))
    ;; display alert:
    (format t "~&There were ~D displays of user alerts."
            (length (filter-httpd-log-entries httpd-log-entries *display-your-alerts-url*)))
    ;; display alerts:
    (format t "~&There were ~D displays of user searches history."
            (length (filter-httpd-log-entries httpd-log-entries *display-your-searches-url*)))))

;; Special-purpose entry points:

(defun print-download-stats (httpd-log-filename file-pattern stats-frequency)
  "Read httpd log file HTTPD-LOG-FILENAME, looking for FILE-PATTERN.
Print download stats for intervals of STATS-FREQUENCY, which may be
day, week, or month."
  (declare (ignore httpd-log-filename file-pattern stats-frequency))
  (format t "~&FIXME: Not implemented yet.")
  t)

(defun extract-page-views-events (httpd-log-filename
                                  &optional (exclude-ip-list nil))
  "Walk through HTTPD-LOG-FILENAME and extract detailed record page
views events.  Useful to input old statistics of page views into
Invenio's rnkPAGEVIEWS table.  If EXCLUDE-IP-LIST is set, then do not
count events coming from those IPs."
  (declare (type simple-base-string httpd-log-filename)
           (type list exclude-ip-list))
  (flet ((extract-recid-from-detailed-record-page-url (url)
           (declare (type simple-base-string url))
           (if (search "GET /record/" url)
               (or (parse-integer (subseq url (length "GET /record/")) :junk-allowed t) 0)
               (if (search "GET /search.py?recid=" url) ; compatibility with old style URLs
                   (or (parse-integer (subseq url (length "GET /search.py?recid=")) :junk-allowed t) 0)
                   0))))
    (format t "-- APACHE LOG FILE ANALYSIS")
    (format t "~&-- Filename: ~A" httpd-log-filename)
    (unless (null exclude-ip-list)
      (format t "~&-- Excluding search engine hits from ~A." exclude-ip-list))
    (with-open-file (input-stream httpd-log-filename :direction :input)
      (do ((line (read-line input-stream nil)
                 (read-line input-stream nil)))
          ((not line))
        (declare (type (or simple-base-string null) line))
        (let ((httpd-log-entry-item (create-httpd-log-entry (wash-httpd-log-line line))))
          (if (and (or (null exclude-ip-list)
                       (not (member (httpd-log-entry-ip httpd-log-entry-item)
                                    exclude-ip-list :test #'equal)))
                   (plusp (extract-recid-from-detailed-record-page-url
                             (httpd-log-entry-request httpd-log-entry-item))))
              (format t "~&INSERT INTO rnkPAGEVIEWS (id_bibrec, client_host, view_time) VALUES ('~A', INET_ATON('~A'), '~A');"
                      (extract-recid-from-detailed-record-page-url
                       (httpd-log-entry-request httpd-log-entry-item))
                      (httpd-log-entry-ip httpd-log-entry-item)
                      (httpd-log-entry-datetimee httpd-log-entry-item)))))))
  (format t "~&-- DONE"))

(defun read-conf-file (analyzer-config-file)
  "Read ANALYZER-CONFIG-FILE and initialize variables found there.
  E.g. line there saying `detailed-record-url = \"/record/\"' will get
  parsed as (setf *detailed-record-url* \"/record/\")."
  (with-open-file (input-stream analyzer-config-file :direction :input)
    (let ((inside-apache-log-analyzer-section nil))
      (do ((line (read-line input-stream nil)
                 (read-line input-stream nil)))
          ((not line))
        (if (string= line "[apache_log_analyzer]")
            (setf inside-apache-log-analyzer-section t))
        (when inside-apache-log-analyzer-section
          (multiple-value-bind (lhs rhs) (split-string-by-equal-sign line)
            (when lhs
              (setf (symbol-value (intern (string-upcase (concatenate 'string "*" lhs "*"))))
                    (read-from-string rhs)))))))))

;; Main entry point:

(defun analyze-httpd-log-file (analyzer-config-file httpd-log-file)
  "Main function that analyzes HTTPD-LOG-FILE according to
instructions presented in ANALYZER-CONFIG-FILE."
  (declare (special *profile*
                    *nb-histogram-items-to-print*
                    *exclude-ip-list*
                    *home-collection*
                    *search-interface-url*
                    *search-interface-url-old-style*
                    *search-engine-url*
                    *search-engine-url-old-style*
                    *detailed-record-url*
                    *basket-url*
                    *add-to-basket-url*
                    *display-basket-url*
                    *display-public-basket-url*
                    *alert-url*
                    *display-your-alerts-url*
                    *display-your-searches-url*))
  (read-conf-file analyzer-config-file)
  (when *profile*
    #+cmu (profile:profile-all)
    #+fixmeclisp (mon:monitor-all)
    #+sbcl (progn
             (sb-profile:profile PRINT-SEARCH-PATTERN-STATS)
             (sb-profile:profile CREATE-HTTPD-LOG-ENTRIES)
             (sb-profile:profile GET-SEARCH-PATTERNS-FROM-HTTPD-LOG-REQUEST-STRING)
             (sb-profile:profile PARSE-HTTPD-LOG-LINE)
             (sb-profile:profile STRING-DECODE-URL)
             (sb-profile:profile CREATE-HTTPD-LOG-ENTRY)
             (sb-profile:profile GET-DATETIME-FROM-HTTPD-LOG-DATETIME-STRING)
             (sb-profile:profile WASH-HTTPD-LOG-LINE)
             (sb-profile:profile GET-MONTH-NUMBER-FROM-MONTH-NAME)
             (sb-profile:profile MAKE-HTTPD-LOG-ENTRY)
             (sb-profile:profile PARSE-INTEGER-OR-ZERO)
             (sb-profile:profile GET-URLARG-VALUES-FROM-URL-STRING)
             (sb-profile:profile HASH-TABLE-KEYS)
             (sb-profile:profile HASH-TABLE-KEY-VAL-STATS)
             (sb-profile:profile STRING-SUBSTITUTE)))
  (let ((httpd-all-log-entries (create-httpd-log-entries httpd-log-file *exclude-ip-list*)))
    (print-general-stats httpd-all-log-entries)
    (print-search-interface-stats httpd-all-log-entries)
    (print-search-collections-stats httpd-all-log-entries)
    (print-search-pattern-stats httpd-all-log-entries)
    (print-basket-stats httpd-all-log-entries)
    (print-alert-stats httpd-all-log-entries))
  (format t "~&")
  (when *profile*
    #+cmu (profile:report-time)
    #+fixmeclisp (mon:report)
    #+sbcl (sb-profile:report)))

