"""A simple placing algorithm using the Hilbert space-filing curve,
translated from RIG."""

# pacman imports
from pacman.model.constraints.placer_constraints import SameChipAsConstraint
from pacman.utilities.algorithm_utilities import placer_algorithm_utilities
from pacman.model.placements import Placement, Placements
from pacman.utilities.utility_calls import locate_constraints_of_type
from pacman.utilities.utility_objs import ResourceTracker
from pacman.exceptions import PacmanPlaceException

from spinn_utilities.progress_bar import ProgressBar

#general imports
from math import log, ceil
import logging


logger = logging.getLogger(__name__)


# An internal (mutable) state object (note: used in place of a
# closure with nonlocal variables for Python 2 support).
#class _HilbertState(object):
#    def __init__(self, x=0, y=0, dx=1, dy=0):
#        self.x, self.y, self.dx, self.dy = x, y, dx, dy

class HilbertPlacer(object):

    def __call__(self, machine_graph, machine):
        ResourceTracker.check_constraints(machine_graph.vertices)

        placements = Placements()
        vertices = \
            placer_algorithm_utilities.sort_vertices_by_known_constraints(
                machine_graph.vertices)

        # Iterate over vertices and generate placements
        progress = ProgressBar(machine_graph.n_vertices,
                               "Placing graph vertices")
        resource_tracker = ResourceTracker(machine,
                               self._generate_hilbert(machine))
        vertices_on_same_chip = \
            placer_algorithm_utilities.get_same_chip_vertex_groups(
                    machine_graph.vertices)
        all_vertices_placed = set()
        for vertex in progress.over(vertices):
            if vertex not in all_vertices_placed:
                vertices_placed = self._place_vertex(
                    vertex, resource_tracker, machine, placements,
                    vertices_on_same_chip)
                all_vertices_placed.update(vertices_placed)
        return placements

    def _check_constraints(
            self, vertices, additional_placement_constraints=None):
        placement_constraints = {SameChipAsConstraint}
        if additional_placement_constraints is not None:
            placement_constraints.update(additional_placement_constraints)
        ResourceTracker.check_constraints(
            vertices, additional_placement_constraints=placement_constraints)

    def _generate_hilbert(self, machine, level, angle=1, chip_x=None,
                          chip_y=None, chip_dx=1, chip_dy=0):
        """Generator of points along a 2D Hilbert curve.

        This implements the L-system as described on
        `http://en.wikipedia.org/wiki/Hilbert_curve`.

        Parameters
        ----------
        level : int
            Number of levels of recursion to use in generating the curve.
            The resulting curve will be `(2**level)-1` wide/tall.
        angle : int
            **For internal use only.** `1` if this is the 'positive'
            expansion of the grammar and `-1` for the 'negative' expansion.
        """

        level = self._hilbert_chip_order(machine)

        # yield first position
        if chip_x is None or chip_y is None:
            place_chip = machine.boot_chip
            yield (chip_x, chip_y)

        if level <= 0:
            return

        # Turn left
        chip_dx, chip_dy = chip_dy * -angle, chip_dx * angle

        # Recurse negative
        for chip_x, chip_y in (level - 1, angle, chip_x, chip_y):
            yield (chip_x, chip_y)

        # Move forward
        chip_x, chip_y = chip_x + chip_dx, chip_y + chip_dy
        yield (chip_x, chip_y)

        # Turn right
        chip_dx,chip_dy = chip_dy * angle,chip_dx * -angle

        # Recurse positive
        for chip_x,chip_y in (level - 1, angle, chip_x, chip_y):
            yield (chip_x,chip_y)

        # Move forward
        chip_x,chip_y =chip_x +chip_dx,chip_y +chip_dy
        yield (chip_x,chip_y)

        # Recurse positive
        for chip_x, chip_y in (level - 1, angle, chip_x, chip_y):
            yield (chip_x, chip_y)

        # Turn right
        chip_dx, chip_dy = chip_dy * angle, chip_dx * -angle

        # Move forward
        chip_x, chip_y = chip_x + chip_dx, chip_y + chip_dy
        yield (chip_x, chip_y)

        # Recurse negative
        for chip_x, chip_y in (level - 1, -angle, chip_x, chip_y):
            yield (chip_x, chip_y)

        # Turn left
        chip_dx, chip_dy = chip_dy * -angle, chip_dx * angle

    def _hilbert_chip_order(self, machine):
        """A generator which iterates over a set of chips in a machine in
        a hilbert path.

        For use as a chip ordering for the sequential placer.
        """
        max_dimen = max(machine.max_chip_x, machine.max_chip_y)
        hilbert_levels = int(ceil(log(max_dimen, 2.0))) if max_dimen >= 1 \
            else 0
        return hilbert_levels

    def _place_vertex(self, vertex, resource_tracker, machine, placements,
            vertices_on_same_chip):

        vertices = vertices_on_same_chip[vertex]
        chips = self._generate_hilbert(machine)
        # Check for placement constraints
        hilbert_constraints =  locate_constraints_of_type(
            vertices, SameChipAsConstraint)

        if len(vertices) > 1:
            assigned_values = \
                resource_tracker.allocate_constrained_group_resources([
                    (vert.resources_required, vert.constraints)
                    for vert in vertices
                ], chips)
            for (x, y, p, _, _), vert in zip(assigned_values, vertices):
                placement = Placement(vert, x, y, p)
                placements.add_placement(placement)
        else:
            (x, y, p, _, _) = resource_tracker.allocate_constrained_resources(
                vertex.resources_required, vertex.constraints, chips)
            placement = Placement(vertex, x, y, p)
            placements.add_placement(placement)

        return vertices

