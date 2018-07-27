import logging

from pacman.exceptions import PacmanPartitionException
from pacman.model.constraints.partitioner_constraints \
    import AbstractPartitionerConstraint, MaxVertexAtomsConstraint, \
    FixedVertexAtomsConstraint, SameAtomsAsVertexConstraint
from pacman.model.graphs.common import GraphMapper, Slice
from pacman.model.graphs.machine import MachineGraph
from pacman.utilities import utility_calls
from pacman.utilities.algorithm_utilities \
    import partition_algorithm_utilities as utils
from pacman.utilities.utility_objs import ResourceTracker

from spinn_utilities.progress_bar import ProgressBar

logger = logging.getLogger(__name__)


class BasicNAtomsPartitioner(object):
    """ An basic algorithm that can partition an application graph based\
        on the number of atoms in the vertices.
    """

    __slots__ = []

    @staticmethod
    def _get_ratio(top, bottom):
        if bottom == 0:
            return 1.0
        return top / bottom

    # inherited from AbstractPartitionAlgorithm
    def __call__(self, graph, machine):
        """
        :param graph: The application_graph to partition
        :type graph:\
            :py:class:`pacman.model.graphs.application.ApplicationGraph`
        :param machine:\
            The machine with respect to which to partition the application\
            graph
        :type machine: :py:class:`spinn_machine.Machine`
        :return: A machine graph
        :rtype:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :raise pacman.exceptions.PacmanPartitionException:\
            If something goes wrong with the partitioning
        """
        ResourceTracker.check_constraints(graph.vertices)
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=graph.vertices,
            supported_constraints=[
                MaxVertexAtomsConstraint, FixedVertexAtomsConstraint,
                SameAtomsAsVertexConstraint],
            abstract_constraint_type=AbstractPartitionerConstraint)

        # start progress bar
        progress = ProgressBar(
            graph.n_vertices,
            "Partitioning graph vertices with real basic assumption of n "
            "atoms")
        machine_graph = MachineGraph("Machine graph for " + graph.label)
        graph_mapper = GraphMapper()
        resource_tracker = ResourceTracker(machine)

        # Partition one vertex at a time
        for vertex in progress.over(graph.vertices):
            self._partition_one_application_vertex(
                vertex, resource_tracker, machine_graph, graph_mapper)

        utils.generate_machine_edges(machine_graph, graph_mapper, graph)

        return machine_graph, graph_mapper, resource_tracker.chips_used

    def _partition_one_application_vertex(
            self, vertex, res_tracker, m_graph, mapper):
        """ Partitions a single application vertex.
        """
        # Compute how many atoms of this vertex we can put on one core
        atoms_per_core = 255
        for constraint in vertex.constraints:
            if isinstance(constraint, MaxVertexAtomsConstraint):
                atoms_per_core = constraint.size
        if atoms_per_core < 1:
            raise PacmanPartitionException(
                "Not enough resources available to create vertex")

        # Partition into vertices
        for first in range(0, vertex.n_atoms, int(atoms_per_core)):
            # Determine vertex size
            last = min(first + atoms_per_core, vertex.n_atoms) - 1
            if first < 0 or last < 0:
                raise PacmanPartitionException(
                    "Not enough resources available to create vertex")

            # Create and store new vertex, and increment elements first
            vertex_slice = Slice(first, last)
            resources = vertex.get_resources_used_by_atoms(vertex_slice)

            m_vertex = vertex.create_machine_vertex(vertex_slice, resources)
            m_graph.add_vertex(m_vertex)
            mapper.add_vertex_mapping(m_vertex, vertex_slice, vertex)

    def _compute_atoms_per_core(self, vertex, res_tracker):
        """ Work out how many atoms per core are required for the given\
            vertex. Assumes that the first atom of the vertex is fully\
            representative.

        :rtype: float
        """
        # Get the usage of the first atom, then assume that this will be the
        # usage of all the atoms.
        requirements = vertex.get_resources_used_by_atoms(Slice(0, 1))

        # Locate the maximum resources available
        limits = res_tracker.get_maximum_constrained_resources_available(
            requirements, vertex.constraints)

        # Find the ratio of each of the resources - if 0 is required,
        # assume the ratio is the max available
        atoms_per_sdram = self._get_ratio(
            limits.sdram.get_value(), requirements.sdram.get_value())
        atoms_per_dtcm = self._get_ratio(
            limits.dtcm.get_value(), requirements.dtcm.get_value())
        atoms_per_cpu = self._get_ratio(
            limits.cpu_cycles.get_value(), requirements.cpu_cycles.get_value())

        n_atoms = None
        for fa_constraint in utility_calls.locate_constraints_of_type(
                vertex.constraints, FixedVertexAtomsConstraint):
            if n_atoms is not None and n_atoms != fa_constraint.size:
                raise PacmanPartitionException(
                    "Vertex has multiple contradictory fixed atom constraints"
                    " - cannot be both {} and {}".format(
                        n_atoms, fa_constraint.size))
            n_atoms = fa_constraint.size

        max_atom_values = [atoms_per_sdram, atoms_per_dtcm, atoms_per_cpu]
        for max_atom_constraint in utility_calls.locate_constraints_of_type(
                vertex.constraints, MaxVertexAtomsConstraint):
            max_atom_values.append(float(max_atom_constraint.size))
        max_atoms = min(max_atom_values)

        if n_atoms is not None and max_atoms < n_atoms:
            raise PacmanPartitionException(
                "Max size of {} is incompatible with fixed size of {}".format(
                    max_atoms, n_atoms))

        return n_atoms if n_atoms is not None else max_atoms