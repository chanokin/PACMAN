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

import json
import time
from pacman.exceptions import PacmanRoutingException
from pacman.model.routing_tables.multicast_routing_tables import (from_json)
from pacman.model.routing_tables.multicast_routing_tables import (to_json)
from pacman.model.routing_tables import (MulticastRoutingTables)
from pacman.operations.algorithm_reports.routing_compression_checker_report \
    import compare_tables
from pacman.operations.router_compressors.mundys_router_compressor.\
    routing_table_condenser import (
        MundyRouterCompressor)
from pacman.operations.router_compressors.unordered_compressor import \
    UnorderedCompressor
from pacman.operations.router_compressors.pair_compressor import PairCompressor


#  original_tables = from_json("malloc_1hard_routing_tables.json.gz")
original_tables = from_json("routing_tables_zoned_big.json.gz")

#bad = MulticastRoutingTables()
good = MulticastRoutingTables()
for original in original_tables:
    if original.number_of_entries > 1023:
        good.add_routing_table(original)
    #else:
    #    bad.add_routing_table(original)

#json_obj = to_json(bad)
# dump to json file
#with open("bad_routing_tables.json", "w") as f:
#    json.dump(json_obj, f)
#json_obj = to_json(good)
# dump to json file
#with open("routing_tables_zoned_big.json", "w") as f:
#    json.dump(json_obj, f)
#original_tables = good


MUNDY = False
PRE = False
TEST = False
mundy_compressor = MundyRouterCompressor()
# Hack to stop it throwing a wobly for too many entries
MundyRouterCompressor.max_supported_length = 5000
pre_compressor = UnorderedCompressor()
test_compressor = PairCompressor()

if MUNDY:
    start = time.time()
    mundy_tables = mundy_compressor(original_tables)
mundy_time = time.time()
if PRE:
    pre_tables = pre_compressor(original_tables)
pre_time = time.time()
if MUNDY and PRE:
    both_tables = mundy_compressor(pre_tables)
both_time = time.time()
if TEST:
    test_tables = test_compressor(original_tables)
test_time = time.time()
for original in original_tables:
    org_routes = set()
    for entry in original.multicast_routing_entries:
        org_routes.add(entry.spinnaker_route)
    if MUNDY:
        mundy = mundy_tables.get_routing_table_for_chip(original.x, original.y)
        mundy_routes = set()
        for entry in mundy.multicast_routing_entries:
            if entry.spinnaker_route == 32:
                print(entry)
            mundy_routes.add(entry.spinnaker_route)
        print("Testing Mundy")
        try:
            compare_tables(original, mundy)
            print("Mundy Passed")
        except PacmanRoutingException as ex:
            print(ex)
    if PRE:
        pre = pre_tables.get_routing_table_for_chip(original.x, original.y)
        pre_routes = set()
        for entry in pre.multicast_routing_entries:
            pre_routes.add(entry.spinnaker_route)
        print("Testing Pre")
        compare_tables(original, pre)
        print("Pre Passed")
    if MUNDY and PRE:
        both = both_tables.get_routing_table_for_chip(original.x, original.y)
        both_routes = set()
        for entry in both.multicast_routing_entries:
            both_routes.add(entry.spinnaker_route)
        print("Testing Both")
        try:
            compare_tables(original, both)
            print("Both Passed")
        except PacmanRoutingException as ex:
            print(ex)
    if TEST:
        test = test_tables.get_routing_table_for_chip(original.x, original.y)
        test_routes = set()
        for entry in test.multicast_routing_entries:
            test_routes.add(entry.spinnaker_route)
        print("Testing test")
        compare_tables(original, test)
        print("Test Passed")

    print("org:", original.number_of_entries, len(org_routes))
    if PRE:
        print("pre:", pre.number_of_entries, len(pre_routes))
    if MUNDY:
        print("mundy:", mundy.number_of_entries, len(mundy_routes))
        if PRE:
            print("both:", both.number_of_entries, len(both_routes))
    if PRE:
        print("test:", test.number_of_entries, len(test_routes))
if MUNDY:
    print(mundy_time-start)
if PRE:
    print(pre_time-mundy_time)
if MUNDY and PRE:
    print(both_time-pre_time)
if TEST:
    print(test_time-both_time)