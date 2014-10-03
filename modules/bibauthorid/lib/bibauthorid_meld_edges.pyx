from invenio.bibauthorid_prob_matrix import Bib_matrix

def meld_edges(p1, p2):
    '''
    Creates one out_edges set from two.
    The operation is associative and commutative.
    The objects are: (out_edges for in a cluster, number of vertices in the same cluster)
    '''
    cdef int verts1, verts2

    out_edges1, verts1 = p1
    out_edges2, verts2 = p2
    assert verts1 > 0 and verts2 > 0, 'MELD_EDGES: verts problem %s %s ' % (str(verts1), str(verts2))
    cdef float vsum, invsum
    vsum = verts1 + verts2
    invsum = 1. / vsum

    assert len(out_edges1) == len(out_edges2), "MELD_EDGES: Invalid arguments for meld edges"
    size = len(out_edges1)

    result = list()
    for i in xrange(size):
        result.append(median(out_edges1[i][0], out_edges1[i][1], out_edges2[i][0], out_edges1[i][1],
                             verts1, verts2, invsum))

    return (result, vsum)


cdef tuple median(float e10,float e11, float e20, float e21, int verts1, int verts2, float invsum):

    cdef float i1, i2, inter_cert, inter_prob

    if e10 < 0:
        return (e10,e11)
    if e20 < 0:
        return (e20,e21)

    i1 = e11 * verts1
    i2 = e21 * verts2
    inter_cert = i1 + i2
    inter_prob = e10 * i1 + e20 * i2
    try:
        return (inter_prob / inter_cert, inter_cert * invsum)
    except ZeroDivisionError:
        return (0.,0.)


#old code before cythonization
#def meld_edges(p1, p2):
#    '''
#    Creates one out_edges set from two.
#    The operation is associative and commutative.
#    The objects are: (out_edges for in a cluster, number of vertices in the same cluster)
#    '''
#    out_edges1, verts1 = p1
#    out_edges2, verts2 = p2
#    assert verts1 > 0 and verts2 > 0, PID()+'MELD_EDGES: verts problem %s %s ' % (str(verts1), str(verts2))
#    vsum = verts1 + verts2
#    invsum = 1. / vsum
#
#    special_numbers = Bib_matrix.special_numbers #local reference optimization
#
#    def median(e1, e2):
#
#    #dirty optimization, should check if value is in dictionary instead
#    # if e1[0] in special_numbers: return e1
#    # if e2[0] in special_numbers: return e2
#        if e1[0] < 0:
#            assert e1[0] in special_numbers, "MELD_EDGES: wrong value for median? %s" % str(e1)
#            return e1
#        if e2[0] < 0:
#            assert e2[0] in special_numbers, "MELD_EDGES: wrong value for median? %s" % str(e2)
#            return e2
#
#        i1 = e1[1] * verts1
#        i2 = e2[1] * verts2
#        inter_cert = i1 + i2
#        inter_prob = e1[0] * i1 + e2[0] * i2
#        try:
#            return (inter_prob / inter_cert, inter_cert * invsum)
#        except ZeroDivisionError:
#            return (0.,0.)
#
#    assert len(out_edges1) == len(out_edges2), "Invalid arguments for meld edges"
#    size = len(out_edges1)
#
#    result = numpy.ndarray(shape=(size, 2), dtype=float, order='C')
#    gc.disable()
##    for i in xrange(size):
##        result[i] = median(out_edges1[i], out_edges2[i])
##        assert (result[i][0] >= 0 and result[i][0] <= 1) or result[i][0] in Bib_matrix.special_numbers, PID()+'MELD_EDGES: value %s' % result[i]
##        assert (result[i][1] >= 0 and result[i][1] <= 1) or result[i][1] in Bib_matrix.special_numbers, PID()+'MELD_EDGES: compat %s' % result[i]
#    result = [median(x,y) for x,y in izip(out_edges1, out_edges2)]
#    gc.enable()
#    return (result, vsum)
