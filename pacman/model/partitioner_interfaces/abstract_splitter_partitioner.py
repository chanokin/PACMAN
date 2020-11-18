# Copyright (c) 2020-2021 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractSplitterPartitioner(object):
    """ Splitter API to allow other Partitioner's to add more stuff to the
    edge creation process.

    This makes sure that the methods super class expect to be there are not
    removed.

    """

    @abstractmethod
    def create_machine_edge(
            self, src_machine_vertex, dest_machine_vertex,
            common_edge_type, app_edge, machine_graph,
            app_outgoing_edge_partition, resource_tracker):
        """ Creates the machine edge (if needed) and adding it
        to the graph

        Some implementations of this method are able to detect that the
        requested edge is not actually needed so never create or add it.

        :param MachineVertex src_machine_vertex: Src machine vertex of a edge
        :param MachineVertex dest_machine_vertex: Dest machine vertex of a edge
        :param MachineEdge common_edge_type: The edge type to build
        :param ApplicationEdge app_edge: The app edge this machine edge is\
            to be associated with.
        :param MachineGraph machine_graph: Machine graph to add edge to.
        :param OutgoingEdgePartition app_outgoing_edge_partition: Partition
        :param Resource resource_tracker: The resource tracker.
        :rtype: None
        """
