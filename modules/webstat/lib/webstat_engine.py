## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

__revision__ = "$Id$"
__lastupdated__ = "$Date$"

import calendar, commands, datetime, time, os, cPickle
from invenio.config import CFG_TMPDIR, CFG_SITE_URL
from invenio.urlutils import redirect_to_url
from invenio.search_engine import perform_request_search
from invenio.dbquery import run_sql, wash_table_column_name

WEBSTAT_SESSION_LENGTH = 48*60*60 # seconds
WEBSTAT_GRAPH_TOKENS = '-=#+@$%&XOSKEHBC'

# KEY EVENT TREND SECTION

def get_keyevent_trend_collection_population(args):
    """
    Returns the quantity of documents in Invenio for
    the given timestamp range.

    @param args['collection']: A collection name
    @type args['collection']: str

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    # Collect list of timestamps of insertion in the specific collection
    ids = perform_request_search(cc=args['collection'])
    if len(ids) == 0:
        return []

    # collect action dates
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
    ids_str = str(ids).replace('[', '(').replace(']', ')')
    sql_query = ("SELECT creation_date FROM bibrec WHERE id IN %s AND creation_date > '%s'" + \
           "AND creation_date < '%s' ORDER BY creation_date DESC") % \
           (ids_str, lower, upper)
    action_dates = [x[0] for x in run_sql(sql_query)]

    sql_query = "SELECT COUNT(id) FROM bibrec WHERE id IN %s AND creation_date < '%s'" % \
                (ids_str,lower)
    initial_quantity = run_sql(sql_query)[0][0]

    return _get_trend_from_actions(action_dates, initial_quantity,
                                   args['t_start'], args['t_end'], args['granularity'], args['t_format'])


def get_keyevent_trend_search_frequency(args):
    """
    Returns the number of searches (of any kind) carried out
    during the given timestamp range.

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    # collect action dates
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
    sql = "SELECT date FROM query INNER JOIN user_query ON id=id_query " + \
          "WHERE date > '%s' AND date < '%s' ORDER BY date DESC" % \
          (lower, upper)
    action_dates = [x[0] for x in run_sql(sql)]

    return _get_trend_from_actions(action_dates, 0, args['t_start'], args['t_end'], args['granularity'], args['t_format'])

def get_keyevent_trend_search_type_distribution(args):
    """
    Returns the number of searches carried out during the given
    timestamp range, but also partion them by type Simple and
    Advanced.

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    # SQL to determine all simple searches:
    sql = "SELECT date FROM query INNER JOIN user_query ON id=id_query WHERE urlargs LIKE '%p=%' " + \
          "AND date > '%s' AND date < '%s' ORDER BY date DESC" % (lower, upper)
    simple = [x[0] for x in run_sql(sql)]

    # SQL to determine all advanced searches:
    sql = "SELECT date FROM query INNER JOIN user_query ON id=id_query WHERE urlargs LIKE '%as=1%' " + \
          "AND date > '%s' AND date < '%s' ORDER BY date DESC" % (lower, upper)
    advanced = [x[0] for x in run_sql(sql)]

    # Compute the trend for both types
    s_trend = _get_trend_from_actions(simple, 0, args['t_start'], args['t_end'], args['granularity'], args['t_format'])
    a_trend = _get_trend_from_actions(advanced, 0, args['t_start'], args['t_end'], args['granularity'], args['t_format'])

    # Assemble, according to return type
    return [(s_trend[i][0], (s_trend[i][1], a_trend[i][1])) for i in range(len(s_trend))]

def get_keyevent_trend_download_frequency(args):
    """
    Returns the number of full text downloads carried out
    during the given timestamp range.

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
    sql = "SELECT download_time FROM rnkDOWNLOADS WHERE download_time > '%s' \
            AND download_time < '%s'  ORDER BY download_time DESC" % (lower, upper)
    actions = [x[0] for x in run_sql(sql)]

    return _get_trend_from_actions(actions, 0, args['t_start'], args['t_end'], args['granularity'], args['t_format'])

# KEY EVENT SNAPSHOT SECTION

def get_keyevent_snapshot_uptime_cmd():
    """
    A specific implementation of get_current_event().

    @return: The std-out from the UNIX command 'uptime'.
    @type: str
    """
    return _run_cmd('uptime').strip().replace('  ', ' ')

def get_keyevent_snapshot_apache_processes():
    """
    A specific implementation of get_current_event().

    @return: The std-out from the UNIX command 'uptime'.
    @type: str
    """
    # The number of Apache processes (root+children)
    return _run_cmd('ps -e | grep apache2 | grep -v grep | wc -l')

def get_keyevent_snapshot_bibsched_status():
    """
    A specific implementation of get_current_event().

    @return: Information about the number of tasks in the different status modes.
    @type: [(str, int)]
    """
    sql = "SELECT status, COUNT(status) FROM schTASK GROUP BY status"
    return [(x[0], int(x[1])) for x in run_sql(sql)]

def get_keyevent_snapshot_sessions():
    """
    A specific implementation of get_current_event().

    @return: The current number of website visitors (guests, logged in)
    @type: (int, int)
    """
    # SQL to retrieve sessions in the Guests
    sql = "SELECT COUNT(session_expiry) FROM session INNER JOIN user ON uid=id " + \
          "WHERE email = '' AND " + \
          "session_expiry-%d < unix_timestamp() AND " % WEBSTAT_SESSION_LENGTH + \
          "unix_timestamp() < session_expiry"
    guests = run_sql(sql)[0][0]

    # SQL to retrieve sessions in the Logged in users
    sql = "SELECT COUNT(session_expiry) FROM session INNER JOIN user ON uid=id " + \
          "WHERE email <> '' AND " + \
          "session_expiry-%d < unix_timestamp() AND " % WEBSTAT_SESSION_LENGTH + \
          "unix_timestamp() < session_expiry"
    logged_ins = run_sql(sql)[0][0]

    # Assemble, according to return type
    return (guests, logged_ins)

# CUSTOM EVENT SECTION

def get_customevent_trend(args):
    """
    Returns trend data for a custom event over a give
    timestamp range.

    @param args['id']: The event id
    @type args['id']: str

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str

    @param args['cols']: Columns and it's content that will be include
                         if don't exist or it's empty it will include all cols
    @type args['cols']: [ [ str, str ], ]
    """
    # Get a MySQL friendly date
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
    tbl_name = get_customevent_table(args['id'])
    col_names = get_customevent_args(args['id'])

    sql_query = ["SELECT creation_time FROM %s WHERE creation_time > '%s'" % (tbl_name, lower)]
    sql_query.append("AND creation_time < '%s'" % upper)
    sql_param = []
    for col_bool, col_title, col_content in args['cols']:
        if not col_title in col_names:
            continue
        if col_content:
            if col_bool == "and" or col_bool == "":
                sql_query.append("AND %s" % wash_table_column_name(col_title))
            elif col_bool == "or":
                sql_query.append("OR %s" % wash_table_column_name(col_title))
            elif col_bool == "and_not":
                sql_query.append("AND NOT %s" % wash_table_column_name(col_title))
            else:
                continue
            sql_query.append(" LIKE %s")
            sql_param.append("%" + col_content + "%")
    sql_query.append("ORDER BY creation_time DESC")
    sql = ' '.join(sql_query)

    dates = [x[0] for x in run_sql(sql, tuple(sql_param))]
    return _get_trend_from_actions(dates, 0, args['t_start'], args['t_end'], args['granularity'], args['t_format'])

def get_customevent_dump(args):
    """
    Similar to a get_event_trend implemention, but NO refining aka frequency
    handling is carried out what so ever. This is just a dump. A dump!

    @param args['id']: The event id
    @type args['id']: str

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str

    @param args['cols']: Columns and it's content that will be include
                         if don't exist or it's empty it will include all cols
    @type args['cols']: [ [ str, str ], ]
    """
    # Get a MySQL friendly date
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    # Get customevents
    # events_list = [(creation_time, event, [arg1, arg2, ...]), ...]
    event_list = []
    event_cols = {}
    for id, i in [ (args['ids'][i], str(i)) for i in range(len(args['ids']))]:
        # Get all the event arguments and creation times
        tbl_name = get_customevent_table(id)
        col_names = get_customevent_args(id)
        sql_query = ["SELECT * FROM %s WHERE creation_time > '%s'" % (tbl_name, lower)] # Note: SELECT * technique is okay here
        sql_query.append("AND creation_time < '%s'" % upper)
        sql_param = []
        for col_bool, col_title, col_content in args['cols'+i]:
            if not col_title in col_names: continue
            if col_content:
                if col_bool == "and" or col_bool == "":
                    sql_query.append("AND %s" % wash_table_column_name(col_title))
                elif col_bool == "or":
                    sql_query.append("OR %s" % wash_table_column_name(col_title))
                elif col_bool == "and_not":
                    sql_query.append("AND NOT %s" % wash_table_column_name(col_title))
                else:
                    continue
                sql_query.append(" LIKE %s")
                sql_param.append("%" + col_content + "%")
        sql_query.append("ORDER BY creation_time DESC")
        sql = ' '.join(sql_query)
        res = run_sql(sql, tuple(sql_param))

        for row in res:
            event_list.append((row[1],id,row[2:]))
        # Get the event col names
        try:
            event_cols[id] = cPickle.loads(run_sql("SELECT cols FROM staEVENT WHERE id = %s", (id,))[0][0])
        except TypeError:
            event_cols[id] = ["Unnamed"]
    event_list.sort()

    output = []
    for row in event_list:
        temp = [row[1], row[0].strftime('%Y-%m-%d %H:%M:%S')]

        arguments = ["%s: %s" % (event_cols[row[1]][i], row[2][i]) for i in range(len(row[2]))]

        temp.extend(arguments)
        output.append(tuple(temp))

    return output

def get_customevent_table(id):
    """
    Helper function that for a certain event id retrives the corresponding
    event table name.
    """
    res = run_sql("SELECT CONCAT('staEVENT', number) FROM staEVENT WHERE id = %s", (id,))
    try:
        return res[0][0]
    except IndexError:
        # No such event table
        return None

def get_customevent_args(id):
    """
    Helper function that for a certain event id retrives the corresponding
    event argument (column) names.
    """
    res = run_sql("SELECT cols FROM staEVENT WHERE id = %s", (id,))
    try:
        if res[0][0]:
            return cPickle.loads(res[0][0])
        else:
            return []
    except IndexError:
        # No such event table
        return None

# GRAPHER

def create_graph_trend(trend, path, settings):
    """
    Creates a graph representation out of data produced from get_event_trend.

    @param trend: The trend data
    @type trend: [(str, str|int|(str|int,...))]

    @param path: Where to store the graph
    @type path: str

    @param settings: Dictionary of graph parameters
    @type settings: dict
    """
    # If no input, we don't bother about anything
    if len(trend) == 0:
        return

    # If no filename is given, we'll assume STD-out format and ASCII.
    if path == '':
        settings["format"] = 'asciiart'

    if settings["format"] == 'asciiart':
        out = ""

        if settings["multiple"] is not None:
            # Tokens that will represent the different data sets (maximum 16 sets)
            # Set index (=100) to the biggest of the histogram sums
            index = max([sum(x[1]) for x in trend])

            # Print legend box
            out += "Legend: %s\n\n" % ", ".join(["%s (%s)" % x for x in zip(settings["multiple"], WEBSTAT_GRAPH_TOKENS)])
        else:
            index = max([x[1] for x in trend])

        width = 82

        # Figure out the max length of the xtics, in order to left align
        xtic_max_len = max([len(_to_datetime(x[0]).strftime(settings["xtic_format"])) for x in trend])

        for row in trend:
            # Print the xtic
            xtic = _to_datetime(row[0]).strftime(settings["xtic_format"])
            out_row = xtic + ': ' + ' '*(xtic_max_len-len(xtic)) + '|'

            try:
                col_width = (1.0*width/index)
            except ZeroDivisionError:
                col_width = 0

            if settings["multiple"] is not None:
                # The second value of the row-tuple, represents the n values from the n data
                # sets. Each set, will be represented by a different ASCII character, chosen
                # from the randomized string 'WEBSTAT_GRAPH_TOKENS'. NOTE: Only up to 16 (len(WEBSTAT_GRAPH_TOKENS)) data
                # sets are supported.
                total = sum(row[1])

                for i in range(len(row[1])):
                    col = row[1][i]
                    try:
                        out_row += WEBSTAT_GRAPH_TOKENS[i]*int(1.0*col*col_width)
                    except ZeroDivisionError:
                        break

                if len([i for i in row[1] if type(i) is int and i > 0]) - 1 > 0:
                    out_row += out_row[-1]

            else:
                total = row[1]
                try:
                    out_row += '-'*int(1.0*total*col_width)
                except ZeroDivisionError:
                    break

            # Print sentinel, and the total
            out += out_row + '>' + ' '*(xtic_max_len+4+width-len(out_row)) + str(total) + '\n'

        # Write to destination file
        if path == '':
            print out
        else:
            open(path, 'w').write(out)

    elif settings["format"] == 'gnuplot':
        try:
            import Gnuplot
        except ImportError:
            return

        g = Gnuplot.Gnuplot()

        g('set style data linespoints')
        g('set terminal png small')
        g('set output "%s"' % path)

        if settings["title"] != '':
            g.title(settings["title"])
        if settings["xlabel"] != '':
            g.xlabel(settings["xlabel"])
        if settings["ylabel"] != '':
            g.ylabel(settings["ylabel"])

        if settings["xtic_format"] != '':
            xtics = 'set xtics ('
            xtics += ', '.join(['"%s" %d' %
                     (_to_datetime(trend[i][0], '%Y-%m-%d \
                     %H:%M:%S').strftime(settings["xtic_format"]), i)
                     for i in range(len(trend))]) + ')'
            g(xtics)
        g('set format y "%.0f"')

        # If we have multiple data sets, we need to do some magic to make Gnuplot eat it,
        # This is basically a matrix transposition, and the addition of index numbers.
        if settings["multiple"] is not None:
            cols = len(trend[0][1])
            rows = len(trend)
            plot_items = []
            y_max = 0
            for col in range(cols):
                data = []
                for row in range(rows):
                    data.append([row, trend[row][1][col]])
                plot_items.append(Gnuplot.PlotItems.Data(data, title=settings["multiple"][col]))
                tmp_max = max(data[col])
                if tmp_max > y_max:
                    y_max = tmp_max
            if y_max < 5:
                g('set ytic 1')
            g.plot(*plot_items)
        else:
            data = [x[1] for x in trend]
            y_max = max(data)
            if y_max < 5:
                g('set ytic 1')
            g.plot(data)

def create_graph_dump(dump, path, settings):
    """
    Creates a graph representation out of data produced from get_event_trend.

    @param dump: The dump data
    @type dump: [(str|int,...)]

    @param path: Where to store the graph
    @type path: str

    @param graph_settings: Dictionary of graph parameters
    @type graph_settings: dict
    """
    out = ""

    if len(dump) == 0:
        out += "No actions for this custom event are registered in the given time range."
    else:
        # Make every row in dump equally long, insert None if appropriate.
        max_len = max([len(x) for x in dump])
        events = [tuple(list(x) + [None]*(max_len-len(x))) for x in dump]

        cols = ["Event", "Date and time"] + ["Argument %d" % i for i in range(max_len-2)]

        column_widths = [max([len(str(x[i])) for x in events + [cols]])+3 for i in range(len(events[0]))]

        for i in range(len(cols)):
            out += cols[i] + ' '*(column_widths[i] - len(cols[i]))
        out += "\n"
        for i in range(len(cols)):
            out += '='*(len(cols[i])) + ' '*(column_widths[i] - len(cols[i]))
        out += "\n\n"

        for action in dump:
            for i in range(len(action)):
                if action[i] is None:
                    temp = ''
                else:
                    temp = action[i]
                out += str(temp) + ' '*(column_widths[i] - len(str(temp)))
            out += "\n"

    # Write to destination file
    if path == '':
        print out
    else:
        open(path, 'w').write(out)

# EXPORTER

def export_to_python(data, req):
    """
    Exports the data to Python code.

    @param data: The Python data that should be exported
    @type data: []

    @param req: The Apache request object
    @type req:
    """
    _export("text/x-python", str(data), req)

def export_to_csv(data, req):
    """
    Exports the data to CSV.

    @param data: The Python data that should be exported
    @type data: []

    @param req: The Apache request object
    @type req:
    """
    csv_list = [""""%s",%s""" % (x[0], ",".join([str(y) for y in ((type(x[1]) is tuple) and x[1] or (x[1],))])) for x in data]
    _export('text/csv', '\n'.join(csv_list), req)

# INTERNAL

def _export(mime, content, req):
    """
    Helper function to pass on the export call. Create a
    temporary file in which the content is stored, then let
    redirect to the export web interface.
    """
    filename = CFG_TMPDIR + "/webstat_export_" + str(time.time()).replace('.', '')
    open(filename, 'w').write(content)
    redirect_to_url(req, '%s/stats/export?filename=%s&mime=%s' % (CFG_SITE_URL, os.path.basename(filename), mime))

def _get_trend_from_actions(action_dates, initial_value, t_start, t_end, granularity, format):
    """
    Given a list of dates reflecting some sort of action/event, and some additional parameters,
    an internal data format is returned. 'initial_value' set to zero, means that the frequency
    will not be accumulative, but rather non-causal.

    @param action_dates: A list of dates, indicating some sort of action/event.
    @type action_dates: [datetime.datetime]

    @param initial_value: The numerical offset the first action's value should make use of.
    @type initial_value: int

    @param t_start: Start time for the time domain in format %Y-%m-%d %H:%M:%S
    @type t_start: str

    @param t_stop: End time for the time domain in format %Y-%m-%d %H:%M:%S
    @type t_stop: str

    @param granularity: The granularity of the time domain, span between values.
                        Possible values are [year,month,day,hour,minute,second].
    @type granularity: str

    @param format: Format of the 't_start' and 't_stop' parameters
    @type format: str

    @return: A list of tuples zipping a time-domain and a value-domain
    @type: [(str, int)]
    """
    # Append the maximum date as a sentinel indicating we're done
    action_dates.insert(0, datetime.datetime.max)

    # Create an iterator running from the first day of activity
    dt_iter = _get_datetime_iter(t_start, granularity, format)

    # Construct the datetime tuple for the stop time
    stop_at = _to_datetime(t_end, format) - datetime.timedelta(seconds=1)

    # If our t_start is more recent than the initial action_dates, we need to
    # drop those.
    t_start_dt = _to_datetime(t_start, format)
    while action_dates[-1] < t_start_dt:
        action_dates = action_dates[:-1]

    vector = [(None, initial_value)]
    # pylint: disable=E1101
    old = dt_iter.next()
    # pylint: enable=E1101
    upcoming_action = action_dates.pop()

    for current in dt_iter:
        # Counter of action_dates in the current span, set the initial value to
        # zero to avoid accumlation.
        if initial_value != 0:
            actions_here = vector[-1][1]
        else:
            actions_here = 0

        # Check to see if there's an action date in the current span
        while old <= upcoming_action < current:
            actions_here += 1
            try:
                upcoming_action = action_dates.pop()
            except IndexError:
                upcoming_action = datetime.datetime.max

        vector.append((old.strftime('%Y-%m-%d %H:%M:%S'), actions_here))
        old = current

        # Make sure to stop the iteration at the end time
        if current > stop_at:
            break

    # Remove the first bogus tuple, and return
    return vector[1:]

def _get_datetime_iter(t_start, granularity='day', format='%Y-%m-%d %H:%M:%S'):
    """
    Returns an iterator over datetime elements starting at an arbitrary time,
    with granularity of a [year,month,day,hour,minute,second].

    @param t_start: An arbitrary starting time in format %Y-%m-%d %H:%M:%S
    @type t_start: str

    @param granularity: The span between iterable elements, default is 'days'.
                        Possible values are [year,month,day,hour,minute,second].
    @type granularity: str

    @param format: Format of the 't_start' parameter
    @type format: str

    @return: An iterator of points in time
    @type: iterator over datetime elements
    """
    t = _to_datetime(t_start, format)

    # Make a time increment depending on the granularity and the current time
    # (the length of years and months vary over time)
    span = ""
    while True:
        yield t

        if granularity == "year":
            span = (calendar.isleap(t.year) and ["days=366"] or ["days=365"])[0]
        elif granularity == "month":
            span =  "days=" + str(calendar.monthrange(t.year, t.month)[1])
        elif granularity == "day":
            span = "days=1"
        elif granularity == "hour":
            span = "hours=1"
        elif granularity == "minute":
            span = "minutes=1"
        elif granularity == "second":
            span = "seconds=1"
        else:
            # Default just in case
            span = "days=1"

        t += eval("datetime.timedelta(" + span + ")")

def _to_datetime(dt, format='%Y-%m-%d %H:%M:%S'):
    return datetime.datetime(*time.strptime(dt, format)[:6])

def _run_cmd(command):
    """
    Runs a certain command and returns the string output. If the command is
    not found a string saying so will be returned. Use with caution!

    @param command: The UNIX command to execute.
    @type command: str

    @return: The std-out from the command.
    @type: str
    """
    return commands.getoutput(command)

