from collections import defaultdict


class ConstraintOrder(object):
    """ A constraint order definition for sorting
    """

    def __init__(
            self, constraint_class, relative_order,
            required_optional_properties=None):
        """

        :param constraint_class: The class of the constraint
        :param relative_order:\
            The order of the constraint relative to other constraints to be\
            sorted
        :param required_optional_properties:\
            Properties of the constraint instances that must not be None for\
            the constraint to match this ordering
        """
        self._constraint_class = constraint_class
        self._relative_order = relative_order
        self._required_optional_properties = required_optional_properties

    @property
    def constraint_class(self):
        return self._constraint_class

    @property
    def relative_order(self):
        return self._relative_order

    @property
    def required_optional_properties(self):
        return self._required_optional_properties


class VertexSorter(object):
    """ Sorts vertices based on constraints with given criteria
    """

    def __init__(self, constraint_order):
        """

        :param constraint_order:\
            The order in which the constraints are to be sorted
        :type constraint_order: list of ConstraintOrder
        """

        # Group constraints based on the class
        self._constraints = defaultdict(list)
        for constraint in constraint_order:
            self._constraints[constraint.constraint_class].append(
                (constraint.relative_order,
                    constraint.required_optional_properties)
            )

        # Sort each list of constraint by the number of optional properties,
        # largest first
        for constraints in self._constraints.itervalues():
            constraints.sort(key=lambda _, opts: len(opts), reversed=True)

    def sort(self, vertices):
        """ Sort the given set of vertices by the constraint ordering

        :param vertices: The vertices to sort
        :return: The sorted list of vertices
        """
        vertices_with_rank = list()
        for vertex in vertices:

            # Get all the ranks of the constraints
            ranks = []
            for constraint in vertex.constraints:

                # If the constraint is one to sort by
                if constraint.__class__ in self._constraints:
                    rank, opts = self._constraints[constraint.__class__]
                    if self._matches(constraint, opts):
                        ranks.append(rank)

            # Sort and store the ranks for overall ordering
            ranks.sort()
            vertices_with_rank.append(vertex, ranks)

        # Sort the vertices - because ranks is a list, things with the same
        # min rank will be sorted by the next highest rank and so on
        vertices_with_rank.sort(key=lambda _, rank: rank)
        return [vertex for vertex, _ in vertices_with_rank]

    @staticmethod
    def _matches(constraint, opts):
        """ Determines if the constraint matches the given optional required\
            parameters
        """
        if opts is None:
            return True

        for opt in opts:
            if getattr(constraint, opt) is None:
                return False

        return True
