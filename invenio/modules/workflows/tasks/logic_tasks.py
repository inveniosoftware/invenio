
def foreach(get_list_function=None, savename=None, order="ASC"):
    if order not in ["ASC", "DSC"]:
        order = "ASC"

    def _foreach(obj, eng):

        step = str(eng.getCurrTaskId())
        try:
            if "Iterators" not in eng.extra_data:
                eng.extra_data["Iterators"] = {}
        except KeyError:
            eng.extra_data["Iterators"] = {}

        if callable(get_list_function):
            my_list_to_process = get_list_function(obj, eng)
        else:
            my_list_to_process = []

        if step not in eng.extra_data["Iterators"] and order == "ASC":
            eng.extra_data["Iterators"].update({step: 0})


        if step not in eng.extra_data["Iterators"] and order == "DSC":
            eng.extra_data["Iterators"].update({step: len(my_list_to_process) - 1})


        if order == "ASC" and eng.extra_data["Iterators"][step] < len(my_list_to_process):
            obj.data = my_list_to_process[eng.extra_data["Iterators"][step]]
            if savename is not None:
                obj.extra_data[savename] = obj.data
            eng.extra_data["Iterators"][step] += 1
        elif order == "DSC" and eng.extra_data["Iterators"][step] > -1:
            obj.data = my_list_to_process[eng.extra_data["Iterators"][step]]
            if savename is not None:
                obj.extra_data[savename] = obj.data
            eng.extra_data["Iterators"][step] -= 1
        else:
            del eng.extra_data["Iterators"][step]
            coordonatex = len(eng.getCurrTaskId()) - 1
            coordonatey = eng.getCurrTaskId()[coordonatex]
            new_vector = eng.getCurrTaskId()
            new_vector[coordonatex] = coordonatey + 2
            eng.setPosition(eng.getCurrObjId(), new_vector)

    return _foreach


def simple_for(initA, endA, incrementA, variable_name=None):

    def _simple_for(obj, eng):

        init = initA
        end = endA
        increment = incrementA
        while callable(init):
            init = init(obj, eng)
        while callable(end):
            end = end(obj, eng)
        while callable(increment):
            increment = increment(obj, eng)

        finish = False
        step = str(eng.getCurrTaskId())
        try:
            if "Iterators" not in eng.extra_data:
                eng.extra_data["Iterators"] = {}
        except KeyError:
            eng.extra_data["Iterators"] = {}

        if step not in eng.extra_data["Iterators"]:
            eng.extra_data["Iterators"].update({step: init})

        if (increment > 0 and eng.extra_data["Iterators"][step] > end) or \
                (increment < 0 and eng.extra_data["Iterators"][step] < end):
            finish = True
        if not finish:
            if variable_name is not None:
                eng.extra_data["Iterators"][variable_name] = eng.extra_data["Iterators"][step]
            eng.extra_data["Iterators"][step] += increment
        else:
            del eng.extra_data["Iterators"][step]
            coordonatex = len(eng.getCurrTaskId()) - 1
            coordonatey = eng.getCurrTaskId()[coordonatex]
            new_vector = eng.getCurrTaskId()
            new_vector[coordonatex] = coordonatey + 2
            eng.setPosition(eng.getCurrObjId(), new_vector)

    return _simple_for


def end_for(obj, eng):
    coordonatex = len(eng.getCurrTaskId()) - 1
    coordonatey = eng.getCurrTaskId()[coordonatex]
    new_vector = eng.getCurrTaskId()
    new_vector[coordonatex] = coordonatey - 3
    eng.setPosition(eng.getCurrObjId(), new_vector)


def get_obj_data(obj, eng):
    eng.log.info("last task name: get_obj_data")
    return obj.data


def execute_if(fun, *args):
    def _execute_if(obj, eng):
        for rule in args:
            res = rule(obj, eng)
            if not res:
                eng.jumpCallForward(1)
        fun(obj, eng)
    return _execute_if
