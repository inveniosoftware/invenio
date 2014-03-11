# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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


def foreach(get_list_function=None, savename=None, cache_data=False, order="ASC"):
    """

    :param get_list_function:
    :param savename:
    :param cache_data:
    :param order:
    :return:
    """
    if order not in ["ASC", "DSC"]:
        order = "ASC"

    def _foreach(obj, eng):
        my_list_to_process = []
        step = str(eng.getCurrTaskId())
        try:
            if "_Iterators" not in eng.extra_data:
                eng.extra_data["_Iterators"] = {}
        except KeyError:
            eng.extra_data["_Iterators"] = {}

        if step not in eng.extra_data["_Iterators"]:
            eng.extra_data["_Iterators"][step] = {}
            if cache_data:
                if callable(get_list_function):
                    eng.extra_data["_Iterators"][step]["cache"] = get_list_function(obj, eng)
                elif isinstance(get_list_function, list):
                    eng.extra_data["_Iterators"][step]["cache"] = get_list_function
                else:
                    eng.extra_data["_Iterators"][step]["cache"] = []

                my_list_to_process = eng.extra_data["_Iterators"][step]["cache"]
            if order == "ASC":
                eng.extra_data["_Iterators"][step].update({"value": 0})
            elif order == "DSC":
                eng.extra_data["_Iterators"][step].update({"value": len(my_list_to_process) - 1})
            eng.extra_data["_Iterators"][step]["previous_data"] = obj.data

        if callable(get_list_function):
            if cache_data:
                my_list_to_process = eng.extra_data["_Iterators"][step]["cache"]
            else:
                my_list_to_process = get_list_function(obj, eng)
        elif isinstance(get_list_function, list):
            my_list_to_process = get_list_function
        else:
            my_list_to_process = []

        if order == "ASC" and eng.extra_data["_Iterators"][step]["value"] < len(my_list_to_process):
            obj.data = my_list_to_process[eng.extra_data["_Iterators"][step]["value"]]
            if savename is not None:
                obj.extra_data[savename] = obj.data
            eng.extra_data["_Iterators"][step]["value"] += 1
        elif order == "DSC" and eng.extra_data["_Iterators"][step]["value"] > -1:
            obj.data = my_list_to_process[eng.extra_data["_Iterators"][step]["value"]]
            if savename is not None:
                obj.extra_data[savename] = obj.data
            eng.extra_data["_Iterators"][step]["value"] -= 1
        else:
            obj.data = eng.extra_data["_Iterators"][step]["previous_data"]
            del eng.extra_data["_Iterators"][step]
            coordonatex = len(eng.getCurrTaskId()) - 1
            coordonatey = eng.getCurrTaskId()[coordonatex]
            new_vector = eng.getCurrTaskId()
            new_vector[coordonatex] = coordonatey + 2
            eng.setPosition(eng.getCurrObjId(), new_vector)

    return _foreach


def simple_for(inita, enda, incrementa, variable_name=None):
    """
    :param inita: the starting value
    :param enda: the ending value
    :param incrementa: the increment of the value for each iteration
    :param variable_name: if needed the name in extra_data where we want to store
    the value
    """

    def _simple_for(obj, eng):

        init = inita
        end = enda
        increment = incrementa
        while callable(init):
            init = init(obj, eng)
        while callable(end):
            end = end(obj, eng)
        while callable(increment):
            increment = increment(obj, eng)

        finish = False
        step = str(eng.getCurrTaskId())
        try:
            if "_Iterators" not in eng.extra_data:
                eng.extra_data["_Iterators"] = {}
        except KeyError:
            eng.extra_data["_Iterators"] = {}

        if step not in eng.extra_data["_Iterators"]:
            eng.extra_data["_Iterators"][step] = {}
            eng.extra_data["_Iterators"][step].update({"value": init})

        if (increment > 0 and eng.extra_data["_Iterators"][step]["value"] > end) or \
                (increment < 0 and eng.extra_data["_Iterators"][step]["value"] < end):
            finish = True
        if not finish:
            if variable_name is not None:
                eng.extra_data["_Iterators"][variable_name] = eng.extra_data["_Iterators"][step]["value"]
            eng.extra_data["_Iterators"][step]["value"] += increment
        else:
            del eng.extra_data["_Iterators"][step]
            coordonatex = len(eng.getCurrTaskId()) - 1
            coordonatey = eng.getCurrTaskId()[coordonatex]
            new_vector = eng.getCurrTaskId()
            new_vector[coordonatex] = coordonatey + 2
            eng.setPosition(eng.getCurrObjId(), new_vector)

    return _simple_for


def end_for(obj, eng):
    """

    :param obj:
    :param eng:
    """
    coordonatex = len(eng.getCurrTaskId()) - 1
    coordonatey = eng.getCurrTaskId()[coordonatex]
    new_vector = eng.getCurrTaskId()
    new_vector[coordonatex] = coordonatey - 3
    eng.setPosition(eng.getCurrObjId(), new_vector)


def execute_if(fun, *args):
    """

    :param fun:
    :param args:
    :return:
    """

    def _execute_if(obj, eng):
        for rule in args:
            res = rule(obj, eng)
            if not res:
                eng.jumpCallForward(1)
        fun(obj, eng)

    return _execute_if


def workflow_if(cond, neg=False):
    """

    :param cond:
    :param neg:
    :return:
    """

    def _workflow_if(obj, eng):
        conda = cond
        while callable(conda):
            conda = conda(obj, eng)
        if "_state" not in eng.extra_data:
            eng.extra_data["_state"] = {}
        step = str(eng.getCurrTaskId())

        if neg:
            conda = not conda
        if step not in eng.extra_data["_state"]:
            eng.extra_data["_state"].update({step: conda})
        else:
            eng.extra_data["_state"][step] = conda
        if conda:
            eng.jumpCallForward(1)
        else:
            coordonatex = len(eng.getCurrTaskId()) - 1
            coordonatey = eng.getCurrTaskId()[coordonatex]
            new_vector = eng.getCurrTaskId()
            new_vector[coordonatex] = coordonatey + 1
            eng.setPosition(eng.getCurrObjId(), new_vector)

    return _workflow_if


def workflow_else(obj, eng):
    """

    :param obj:
    :param eng:
    """
    coordonatex = len(eng.getCurrTaskId()) - 1
    coordonatey = eng.getCurrTaskId()[coordonatex]
    new_vector = eng.getCurrTaskId()[:]
    new_vector[coordonatex] = coordonatey - 2
    if not eng.extra_data["_state"][str(new_vector)]:
        eng.jumpCallForward(1)
    else:
        coordonatex = len(eng.getCurrTaskId()) - 1
        coordonatey = eng.getCurrTaskId()[coordonatex]
        new_vector = eng.getCurrTaskId()
        new_vector[coordonatex] = coordonatey + 1
        eng.setPosition(eng.getCurrObjId(), new_vector)


def compare_logic(a, b, op):
    """

    :param a: value A to compare
    :param b: value B to compare
    :param op: Operator can be :
    - eq  A equal B
    - gt A greater than B
    - gte A greater than or equal B
    - lt A lesser than B
    - lte A lesser than or equal B
    :return: Boolean: result of the test
    """


    def _compare_logic(obj, eng):
        my_a = a
        my_b = b
        if callable(my_a):
            while callable(my_a):
                my_a = my_a(obj, eng)

        if callable(my_b):
            while callable(my_b):
                my_b = my_b(obj, eng)
        if op == "eq":
            if my_a == my_b:
                return True
            else:
                return False
        elif "gt" in op:
            if "e" in op:
                if my_a >= my_b:
                    return True
                else:
                    return False
            else:
                if my_a > my_b:
                    return True
                else:
                    return False
        elif "lt" in op:
            if "e" in op:
                if my_a <= my_b:
                    return True
                else:
                    return False
            else:
                if my_a < my_b:
                    return True
                else:
                    return False
        else:
            return False


    return _compare_logic
