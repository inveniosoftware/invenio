from operator import itemgetter

def maximized_mapping(matrix):
    '''
    Finds nearly maximized sum mapping from a matrix.
    With this matrix
    ((4, 1, 10),
     (7, 4, 2),
     (20, 4, 15))
    the function will return ((1, 3), (2, 2), (3, 1)).
    For performance reasons the function will not always return
    the optimal mapping.
    '''
    if not matrix or not matrix[0]:
        return []

    sorts = sorted([(i, j, v) for i, row in enumerate(matrix) for j, v in enumerate(row)]
                   , key = itemgetter(2)
                   , reverse = True)
    freei = set(range(len(matrix)))
    freej = set(range(len(matrix[0])))
    res = []

    for i, j, v in sorts:
        if i in freei and j in freej:
            res.append((i, j, v))
            freei.remove(i)
            freej.remove(j)
            if not freei or not freej:
                return res
    assert False # you shouldn't be here
    return res

