# Copyright (c) 2017-2019 The University of Manchester
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

try:
    from collections.abc import defaultdict
except ImportError:
    from collections import defaultdict
from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import MulticastRoutingEntry
from pacman.model.routing_tables import (
    MulticastRoutingTable, MulticastRoutingTables)
from pacman.exceptions import PacmanElementAllocationException
from .entry import Entry

MAX_SUPPORTED_LENGTH = 1023


class PairCompressor(object):

    __slots__ = [
        #X Dict (by spinnaker_route) (for current chip)
        #X   of entries represented as (key, mask, defautible)
        "_all_entries",
        # Max length below which the algorithm should stop compressing
        "_target_length",
        # String of problems detected. Must be "" to finsih
        "_problems"
    ]

    def __call__(self, router_tables, target_length=None):
        if target_length is None:
            self._target_length = 0  # Compress as much as you can
        else:
            self._target_length = target_length
        # create progress bar
        progress = ProgressBar(
            router_tables.routing_tables,
            "Compressing routing Tables Pairwise")
        return self.compress_tables(router_tables, progress)

    def intersect(self, key_a, mask_a, key_b, mask_b):
        """
        Return if key-mask pairs intersect (i.e., would both match some of the
        same keys).
        For example, the key-mask pairs ``00XX`` and ``001X`` both match the
        keys ``0010`` and ``0011`` (i.e., they do intersect)::
            >>> intersect(0b0000, 0b1100, 0b0010, 0b1110)
            True
        But the key-mask pairs ``00XX`` and ``11XX`` do not match any of the
        same keys (i.e., they do not intersect)::
            >>> intersect(0b0000, 0b1100, 0b1100, 0b1100)
            False
        :param key_a: key of the first key-mask pair
        :type key_a: int
        :param mask_a: mask of the first key-mask pair
        :type mask_a: int
        :param key_b: key of the second key-mask pair
        :type key_b: int
        :param mask_b: mask of the second key-mask pair
        :type mask_b: int
        :return: True if and only if there is an intersection
        """
        return (key_a & mask_b) == (key_b & mask_a)

    def merge(self, entry1, entry2):
        """
        Merges two entries/triples into one that covers both

        The assumption is that they both have the same known spinnaker_route

        :param entry1: Key, Mask, defaultable from the first entry
        :type entry1: Entry
        :param entry2: Key, Mask, defaultable from the second entry
        :type entry2: Entry
        :return: Key, Mask, defaultable from merged entry
        :rtype: (int, int, bool)
        """
        any_ones = entry1.key | entry2.key
        all_ones = entry1.key & entry2.key
        all_selected = entry1.mask & entry2.mask

        # Compute the new mask  and key
        any_zeros = ~all_ones
        new_xs = any_ones ^ any_zeros
        mask = all_selected & new_xs  # Combine existing and new Xs
        key = all_ones & mask
        return key, mask, entry1.defaultable and entry2.defaultable

    def find_merge(self, an_entry, route_entries):
        for another in route_entries:
            m_key, m_mask, defaultable = self.merge(an_entry, another)
            ok = True
            for route in self._all_entries:
                for check in self._all_entries[route]:
                    if self.intersect(check.key, check.mask, m_key, m_mask):
                        ok = False
                        break
            if ok:
                route_entries.remove(another)
                return Entry(
                     m_key, m_mask, defaultable, an_entry.spinnaker_route)
        return None

    def compress_by_route(self, route_entries):
        results = []
        while len(route_entries) > 1:
            an_entry = route_entries.pop()
            merged = self.find_merge(an_entry, route_entries)
            if merged is None:
                results.append(an_entry)
            else:
                route_entries.append(merged)

        if len(route_entries) == 1:
            results.append(route_entries.pop())

        return results

    def compress_table(self, router_table):
        # Split the entries into buckets based on spinnaker_route

        self._all_entries = defaultdict(list)
        for entry in router_table.multicast_routing_entries:
            self._all_entries[entry.spinnaker_route].append(Entry(
                entry.routing_entry_key, entry.mask, entry.defaultable,
                entry.spinnaker_route))

        results = []
        all_routes = list(self._all_entries)
        for spinnaker_route in all_routes:
            if len(self._all_entries[spinnaker_route]) == 1:
                results.extend(self._all_entries.pop(spinnaker_route))

        complex_routes = sorted(
            list(self._all_entries),
            key=lambda x: len(self._all_entries[x]) + 1/(self._all_entries[x][0].spinnaker_route+1),
            reverse=False)
        for spinnaker_route in complex_routes:
            compressed = self.compress_by_route(
                self._all_entries.pop(spinnaker_route))
            results.extend(compressed)

        if len(results) > MAX_SUPPORTED_LENGTH:
            self._problems += "(x:{},y:{})={} ".format(
                router_table.x, router_table.y, len(results))
        print(router_table.number_of_entries, len(results), self._problems)
        compressed_table = MulticastRoutingTable(
            router_table.x, router_table.y)
        for entry in results:
            m = MulticastRoutingEntry(
                entry.key, entry.mask, defaultable=entry.defaultable,
                spinnaker_route=entry.spinnaker_route)
            compressed_table.add_multicast_routing_entry(m)

        return compressed_table

    def compress_tables(self, router_tables, progress):
        """
        Compress all the unordered routing tables

        Tables who start of smaller than target_length are not compressed

        :param router_tables: Routing tables
        :type router_tables: MulticastRoutingTables
        :param progress: Progress bar to show while working
        :tpye progress: ProgressBar
        :return: The compressed but still unordered routing tables
        """
        compressed_tables = MulticastRoutingTables()
        self._problems = ""
        for table in progress.over(router_tables.routing_tables):
            if table.number_of_entries < self._target_length:
                compressed_table = table
            else:
                compressed_table = self.compress_table(table)
            compressed_tables.add_routing_table(compressed_table)

        if len(self._problems) > 0:
            raise PacmanElementAllocationException(
                "The routing table after compression will still not fit"
                " within the machines router: {}".format(self._problems))
        return compressed_tables