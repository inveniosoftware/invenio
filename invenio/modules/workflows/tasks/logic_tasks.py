
def foreach(get_list_function=None, savename=None):
    def _foreach(obj, eng):

        step = str(eng.getCurrTaskId())
        try:
            if "Iterators" not in eng.extra_data:
                eng.extra_data["Iterators"] = {}
        except KeyError:
            eng.extra_data["Iterators"] = {}

        if step not in eng.extra_data["Iterators"]:
            eng.extra_data["Iterators"].update({step: 0})
        if callable(get_list_function):
            my_list_to_process = get_list_function(obj, eng)
        else:
            my_list_to_process = []

        if eng.extra_data["Iterators"][step] < len(my_list_to_process):

            obj.data = my_list_to_process[eng.extra_data["Iterators"][step]]
            if savename is not None:
                obj.extra_data[savename] = obj.data

            eng.extra_data["Iterators"][step] += 1
        else:
            eng.extra_data["Iterators"][step] = 0
            coordonatex = len(eng.getCurrTaskId()) - 1
            coordonatey = eng.getCurrTaskId()[coordonatex]
            new_vector = eng.getCurrTaskId()
            new_vector[coordonatex] = coordonatey + 2
            eng.setPosition(eng.getCurrObjId(), new_vector)

    return _foreach


def endforeach(obj, eng):
    coordonatex = len(eng.getCurrTaskId()) - 1
    coordonatey = eng.getCurrTaskId()[coordonatex]
    new_vector = eng.getCurrTaskId()
    new_vector[coordonatex] = coordonatey - 3
    eng.setPosition(eng.getCurrObjId(), new_vector)


def get_obj_data(obj, eng):
    eng.log.info("last task name: get_obj_data")
    return obj.data

