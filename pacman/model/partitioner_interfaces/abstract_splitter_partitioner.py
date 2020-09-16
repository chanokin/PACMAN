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

    @abstractmethod
    def create_machine_edge(
            self, src_machine_vertex, dest_machine_vertex,
            common_edge_type, app_edge, machine_graph,
            app_outgoing_edge_partition):
        """ overridable method for creating the machine edges

        :param MachineVertex src_machine_vertex:
        :param MachineVertex dest_machine_vertex:
        :param MachineEdge common_edge_type:
        :param ApplicationEdge app_edge:
        :param MachineGraph machine_graph:
        :param OutgoingEdgePartition app_outgoing_edge_partition:
        :rtype: None
        """