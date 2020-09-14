# Copyright (c) 2019-2020 The University of Manchester
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
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod)


@add_metaclass(AbstractBase)
class AbstractControlsDestinationOfEdges(object):

    def __init__(self):
        pass

    @abstractmethod
    def get_destinations_for_edge_from(
            self, app_edge, partition_id, original_source_machine_vertex):
        """ allows a vertex to decide which of its internal machine vertices\
        take a given machine edge

        :param app_edge: the application edge
        :param partition_id: the outgoing partition id
        :param original_source_machine_vertex: the machine vertex that set
        off this application edge consideration
        :return: iterable of destination machine vertices
        """

    @abstractmethod
    def get_post_slice_for(self, machine_vertex):
        """ allows a application vertex to control the slices perceived by \
        out systems.

        :param machine_vertex: the machine vertex to hand slice for
        :return: the slice considered for this vertex
        """

    @abstractmethod
    def get_in_coming_slices(self):
        """ allows a application vertex to control the set of slices for \
        incoming application edges

        :return: the slices incoming to this vertex
        """