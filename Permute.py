

def _permute(L, nexts, numbers, begin, end):
    if end == begin + 1:
        yield L
    else:
        for i in range(begin, end):
            c = L[i]
            if nexts[c][0] == numbers[c]:
                nexts[c][0] += 1
                L[begin], L[i] = L[i], L[begin]
                for p in _permute(L, nexts, numbers, begin + 1, end):
                    yield p
                L[begin], L[i] = L[i], L[begin]
                nexts[c][0] -= 1


def constrained_permutations(L, constraints):
    # warning: assumes that L has unique, hashable elements
    # constraints is a list of constraints, where each constraint is a list of elements which should appear in the permatation in that order
    # warning: constraints may not overlap!
    nexts = dict((a, [0]) for a in L)
    numbers = dict.fromkeys(L, 0) # number of each element in its constraint
    for constraint in constraints:
        for i, pos in enumerate(constraint):
            nexts[pos] = nexts[constraint[0]]
            numbers[pos] = i

    for p in _permute(L, nexts, numbers, 0, len(L)):
        yield p

def permutations(a, b):
    # print(a)
    # print(b)
    return list(p[:] for p in constrained_permutations(a,b))

# print(permutations([1,2,3],[[1,2]]))