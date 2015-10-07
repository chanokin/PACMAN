"""
OutgoingEdgePartition
"""
from enum import Enum
from pacman.model.partitionable_graph.fixed_route_partitionable_edge import \
    FixedRoutePartitionableEdge
from pacman.model.partitionable_graph.multi_cast_partitionable_edge import \
    MultiCastPartitionableEdge
from pacman.model.partitioned_graph.fixed_route_partitioned_edge import \
    FixedRoutePartitionedEdge
from pacman.model.partitioned_graph.multi_cast_partitioned_edge import \
    MultiCastPartitionedEdge
from pacman import exceptions

EDGE_TYPES = Enum(
    value="EDGE_TYPES",
    names=[("MULTI_CAST", 0),
           ("NEAREST_NEIGBOUR", 1),
           ("PEER_TO_PEER", 2),
           ("FIXED_ROUTE", 3)])


class OutgoingEdgePartition(object):
    """
    A collection of egdes which have the same semantics
    """

    def __init__(self, identifier):
        self._identifier = identifier
        self._type = None
        self._edges = list()

    def add_edge(self, edge):
        """
        adds a edge into this outgoing edge partition
        :param edge: the instance of abstract edge to add to the list
        :return:
        """
        self._edges.append(edge)
        if self._type is None:
            self._type = self._deduce_type(edge)
        elif self._type != self._deduce_type(edge):
            raise exceptions.PacmanConfigurationException(
                "The edge {} was trying to be added to a partition {} which "
                "contains edges of type {}, yet the edge was of type {}. This"
                " is deemed an error. Please rectify this and try again. "
                "Thank you")

    @staticmethod
    def _deduce_type(edge):
        """
        deduces the enum from the edge type
        :param edge: the edge to deduce the type of
        :return: a enum type of edge_types
        """
        if isinstance(edge, MultiCastPartitionedEdge):
            return EDGE_TYPES.MULTI_CAST
        elif isinstance(edge, FixedRoutePartitionedEdge):
            return EDGE_TYPES.FIXED_ROUTE
        elif isinstance(edge, MultiCastPartitionableEdge):
            return EDGE_TYPES.MULTI_CAST
        elif isinstance(edge, FixedRoutePartitionableEdge):
            return EDGE_TYPES.FIXED_ROUTE
        else:
            raise exceptions.PacmanConfigurationException(
                "I dont reconise this type of edge, please rectify this and "
                "try again. Thank you.")

    @property
    def identifer(self):
        """
        returns the indenfiter for this outgoing egde partition
        :return:
        """
        return self._identifier

    @property
    def edges(self):
        """
        returns the edges that are associated with this outgoing egde partition
        :return:
        """
        return self._edges

    @property
    def type(self):
        """
        returns the type of the partition
        :return:
        """
        return self._type