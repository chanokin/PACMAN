""" Collection of functions which together validate routes.
"""

from collections import namedtuple
import logging

from pacman.exceptions import PacmanRoutingException
from spinn_utilities.log import FormatAdapter
from pacman.model.constraints.key_allocator_constraints \
    import ContiguousKeyRangeContraint
from pacman.model.graphs.common import EdgeTrafficType
from spinn_utilities.ordered_set import OrderedSet
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities import utility_calls

logger = FormatAdapter(logging.getLogger(__name__))

# Define an internal class for placements
PlacementTuple = namedtuple('PlacementTuple', 'x y p')

_32_BITS = 0xFFFFFFFF
range_masks = {_32_BITS - ((2 ** i) - 1) for i in range(33)}


def validate_routes(machine_graph, placements, routing_infos,
                    routing_tables, machine, graph_mapper=None):
    """ Go though the placements given and check that the routing entries\
        within the routing tables support reach the correction destinations\
        as well as not producing any cycles.

    :param machine_graph: the graph
    :param placements: the placements container
    :param routing_infos: the routing info container
    :param routing_tables: \
        the routing tables generated by the routing algorithm
    :param graph_mapper: \
        the mapping between graphs or none if only using a machine graph
    :param machine: the python machine object
    :type machine: spinn_machine.Machine object
    :rtype: None
    :raises PacmanRoutingException: when either no routing table entry is\
        found by the search on a given router, or a cycle is detected
    """
    traffic_multicast = (
        lambda edge: edge.traffic_type == EdgeTrafficType.MULTICAST)
    progress = ProgressBar(
        placements.placements,
        "Verifying the routes from each core travel to the correct locations")
    for placement in progress.over(placements.placements):

        # locate all placements to which this placement/vertex will
        # communicate with for a given key_and_mask and search its
        # determined destinations

        # gather keys and masks per partition
        partitions = machine_graph.\
            get_outgoing_edge_partitions_starting_at_vertex(placement.vertex)

        if graph_mapper is not None:
            n_atoms = graph_mapper.get_slice(placement.vertex).n_atoms
        else:
            n_atoms = 0

        for partition in partitions:
            r_info = routing_infos.get_routing_info_from_partition(
                partition)
            is_continuous = _check_if_partition_has_continuous_keys(partition)
            if not is_continuous:
                logger.warning(
                    "Due to the none continuous nature of the keys in this "
                    "partition {}, we cannot check all atoms will be routed "
                    "correctly, but will check the base key instead",
                    partition)

            destination_placements = OrderedSet()

            # filter for just multicast edges, we don't check other types of
            # edges here.
            out_going_edges = filter(traffic_multicast, partition.edges)

            # for every outgoing edge, locate its destination and store it.
            for outgoing_edge in out_going_edges:
                dest_placement = placements.get_placement_of_vertex(
                    outgoing_edge.post_vertex)
                destination_placements.append(
                    PlacementTuple(x=dest_placement.x,
                                   y=dest_placement.y,
                                   p=dest_placement.p))

            # search for these destinations
            for key_and_mask in r_info.keys_and_masks:
                _search_route(
                    placement, destination_placements, key_and_mask,
                    routing_tables, machine, n_atoms, is_continuous)


def _check_if_partition_has_continuous_keys(partition):
    continuous_constraints = utility_calls.locate_constraints_of_type(
        partition.constraints, ContiguousKeyRangeContraint)
    # TODO: Can we do better here?
    return len(continuous_constraints) > 0


def _search_route(source_placement, dest_placements, key_and_mask,
                  routing_tables, machine, n_atoms, is_continuous):
    """ Locate if the routing tables work for the source to desks as\
        defined

    :param source_placement: the placement from which the search started
    :param dest_placements: \
        the placements to which this trace should visit only once
    :param key_and_mask: the key and mask associated with this set of edges
    :param n_atoms: the number of atoms going through this path
    :param is_continuous: \
        whether the keys and atoms mapping is continuous
    :type source_placement: instance of\
        :py:class:`pacman.model.placements.Placement`
    :type dest_placements: iterable of PlacementTuple
    :type key_and_mask: instance of\
        :py:class:`pacman.model.routing_info.BaseKeyAndMask`
    :rtype: None
    :raise PacmanRoutingException: when the trace completes and there are\
        still destinations not visited
    """
    if logger.isEnabledFor(logging.DEBUG):
        for dest in dest_placements:
            logger.debug("[{}:{}:{}]", dest.x, dest.y, dest.p)

    located_destinations = set()

    failed_to_cover_all_keys_routers = list()

    _start_trace_via_routing_tables(
        source_placement, key_and_mask, located_destinations,
        routing_tables, machine, n_atoms, is_continuous,
        failed_to_cover_all_keys_routers)

    # start removing from located_destinations and check if destinations not
    #  reached
    failed_to_reach_destinations = list()
    for dest in dest_placements:
        if dest in located_destinations:
            located_destinations.remove(dest)
        else:
            failed_to_reach_destinations.append(dest)

    # check for error if trace didn't reach a destination it was meant to
    error_message = ""
    if failed_to_reach_destinations:
        output_string = ""
        for dest in failed_to_reach_destinations:
            output_string += "[{}:{}:{}]".format(dest.x, dest.y, dest.p)
        source_processor = "[{}:{}:{}]".format(
            source_placement.x, source_placement.y, source_placement.p)
        error_message += ("failed to locate all destinations with vertex"
                          " {} on processor {} with keys {} as it did not "
                          "reach destinations {}".format(
                              source_placement.vertex.label, source_processor,
                              key_and_mask, output_string))

    # check for error if the trace went to a destination it shouldn't have
    if located_destinations:
        output_string = ""
        for dest in located_destinations:
            output_string += "[{}:{}:{}]".format(dest.x, dest.y, dest.p)
        source_processor = "[{}:{}:{}]".format(
            source_placement.x, source_placement.y, source_placement.p)
        error_message += ("trace went to more failed to locate all "
                          "destinations with vertex {} on processor {} "
                          "with keys {} as it didn't reach destinations {}"
                          .format(
                              source_placement.vertex.label, source_processor,
                              key_and_mask, output_string))

    if failed_to_cover_all_keys_routers:
        output_string = ""
        for data_entry in failed_to_cover_all_keys_routers:
            output_string += "[{}, {}, {}, {}]".format(
                data_entry['router_x'], data_entry['router_y'],
                data_entry['keys'], data_entry['source_mask'])
        source_processor = "[{}:{}:{}]".format(
            source_placement.x, source_placement.y, source_placement.p)
        error_message += (
            "trace detected that there were atoms which the routing entry's"
            " wont cover and therefore packets will fly off to unknown places."
            " These keys came from the vertex {} on processor {} and the"
            " failed routers are {}".format(
                source_placement.vertex.label, source_processor,
                output_string))

    # raise error if required
    if error_message != "":
        raise PacmanRoutingException(error_message)
    logger.debug("successful test between {} and {}",
                 source_placement.vertex.label, dest_placements)


def _start_trace_via_routing_tables(
        source_placement, key_and_mask, reached_placements, routing_tables,
        machine, n_atoms, is_continuous, failed_to_cover_all_keys_routers):
    """ Start the trace, by using the source placement's router and tracing\
        from the route.

    :param source_placement: the source placement used by the trace
    :param key_and_mask: the key being used by the vertex which\
        resides on the source placement
    :param reached_placements: the placements reached during the trace
    :param n_atoms: the number of atoms going through this path
    :param is_continuous: \
        bool stating if the keys and atoms mapping is continuous
    :param failed_to_cover_all_keys_routers: \
        list of failed routers for all keys
    :rtype: None
    :raises None: this method does not raise any known exception
    """
    current_router_table = routing_tables.get_routing_table_for_chip(
        source_placement.x, source_placement.y)
    visited_routers = set()
    visited_routers.add((current_router_table.x, current_router_table.y))

    # get src router
    entry = _locate_routing_entry(
        current_router_table, key_and_mask.key, n_atoms)

    _recursive_trace_to_destinations(
        entry, current_router_table, source_placement.x,
        source_placement.y, key_and_mask, visited_routers,
        reached_placements, machine, routing_tables, is_continuous, n_atoms,
        failed_to_cover_all_keys_routers)


def _check_all_keys_hit_entry(entry, n_atoms, base_key):
    """
    :param entry: routing entry discovered
    :param n_atoms: the number of atoms this partition covers
    :param base_key: the base key of the partition
    :return: the list of keys which this entry doesn't cover which it should
    """
    bad_entries = list()
    for atom_id in range(0, n_atoms):
        key = base_key + atom_id
        if entry.mask & key != entry.routing_entry_key:
            bad_entries.append(key)
    return bad_entries


# locates the next dest position to check
def _recursive_trace_to_destinations(
        entry, current_router, chip_x, chip_y, key_and_mask, visited_routers,
        reached_placements, machine, routing_tables, is_continuous, n_atoms,
        failed_to_cover_all_keys_routers):
    """ Recursively search though routing tables until no more entries are\
        registered with this key.

    :param entry: the original entry used by the first router which\
        resides on the source placement chip.
    :param current_router: \
        the router currently being visited during the trace
    :param key_and_mask: the key and mask being used by the vertex\
        which resides on the source placement
    :param visited_routers: the list of routers which have been visited\
        during this trace so far
    :param reached_placements: the placements reached during the trace
    :param chip_x: the x coordinate of the chip being considered
    :param chip_y: the y coordinate of the chip being considered
    :param n_atoms: the number of atoms going through this path
    :param is_continuous: \
        bool stating if the keys and atoms mapping is continuous
    :param failed_to_cover_all_keys_routers: \
        list of failed routers for all keys
    :type entry: \
        :py:class:`spinn_machine.MulticastRoutingEntry`
    :type current_router:\
        :py:class:`pacman.model.routing_tables.MulticastRoutingTable`
    :type chip_x: int
    :type chip_y: int
    :type key_and_mask:
        :py:class:`pacman.model.routing_info.BaseKeyAndMask`
    :type visited_routers: iterable of\
        :py:class:`pacman.model.routing_tables.MulticastRoutingTable`
    :type reached_placements: iterable of placement_tuple
    :rtype: None
    :raise None: this method does not raise any known exceptions
    """

    # determine where the route takes us
    chip_links = entry.link_ids
    processor_values = entry.processor_ids

    # if goes down a chip link
    if chip_links:
        # also goes to a processor
        if processor_values:
            _is_dest(processor_values, current_router, reached_placements)
        # only goes to new chip
        for link_id in chip_links:

            # locate next chips router
            machine_router = machine.get_chip_at(chip_x, chip_y).router
            link = machine_router.get_link(link_id)
            next_router = routing_tables.get_routing_table_for_chip(
                link.destination_x, link.destination_y)

            # check that we've not visited this router before
            _check_visited_routers(
                next_router.x, next_router.y, visited_routers)

            # locate next entry
            entry = _locate_routing_entry(
                next_router, key_and_mask.key, n_atoms)

            if is_continuous:
                bad_entries = _check_all_keys_hit_entry(
                    entry, n_atoms, key_and_mask.key)
                if bad_entries:
                    failed_to_cover_all_keys_routers.append(
                        {'router_x': next_router.x,
                         'router_y': next_router.y,
                         'keys': bad_entries,
                         'source_mask': key_and_mask.mask})

            # get next route value from the new router
            _recursive_trace_to_destinations(
                entry, next_router, link.destination_x, link.destination_y,
                key_and_mask, visited_routers, reached_placements, machine,
                routing_tables, is_continuous, n_atoms,
                failed_to_cover_all_keys_routers)

    # only goes to a processor
    elif processor_values:
        _is_dest(processor_values, current_router, reached_placements)


def _check_visited_routers(chip_x, chip_y, visited_routers):
    """ Check if the trace has visited this router already

    :param chip_x: the x coordinate of the chip being checked
    :param chip_y: the y coordinate of the chip being checked
    :param visited_routers: routers already visited
    :type chip_x: int
    :type chip_y: int
    :type visited_routers: iterable of\
        :py:class:`pacman.model.routing_tables.MulticastRoutingTable`
    :rtype: None
    :raise PacmanRoutingException: when a router has been visited twice.
    """
    visited_routers_router = (chip_x, chip_y)
    if visited_routers_router in visited_routers:
        raise PacmanRoutingException(
            "visited this router before, there is a cycle here. "
            "The routers I've currently visited are {} and the router i'm "
            "visiting is {}"
            .format(visited_routers, visited_routers_router))
    visited_routers.add(visited_routers_router)


def _is_dest(processor_ids, current_router, reached_placements):
    """ Check for processors to be removed

    :param reached_placements: the placements to which the trace visited
    :param processor_ids: the processor IDs which the last router entry\
        said the trace should visit
    :param current_router: the current router being used in the trace
    :rtype: None
    :raise None: this method does not raise any known exceptions
    """

    dest_x, dest_y = current_router.x, current_router.y
    for processor_id in processor_ids:
        reached_placements.add(PlacementTuple(dest_x, dest_y, processor_id))


def _locate_routing_entry(current_router, key, n_atoms):
    """ locate the entry from the router based off the edge

    :param current_router: the current router being used in the trace
    :param key: the key being used by the source placement
    :rtype: None
    :raise PacmanRoutingException: \
        when there is no entry located on this router
    """
    found_entry = None
    for entry in current_router.multicast_routing_entries:
        key_combo = entry.mask & key
        e_key = entry.routing_entry_key
        if key_combo == e_key:
            if found_entry is None:
                found_entry = entry
            else:
                logger.warning(
                    "Found more than one entry for key {}. This could be "
                    "an error, as currently no router supports overloading"
                    " of entries.", hex(key))
            if entry.mask in range_masks:
                last_atom = key + n_atoms - 1
                last_key = e_key + (~entry.mask & _32_BITS)
                if last_key < last_atom:
                    raise PacmanRoutingException(
                        "Full key range not covered: key:{} key_combo:{} "
                        "mask:{}, last_key:{}, e_key:{}".format(
                            hex(key), hex(key_combo), hex(entry.mask),
                            hex(last_key), hex(e_key)))
        elif entry.mask in range_masks:
            last_atom = key + n_atoms
            last_key = e_key + (~entry.mask & _32_BITS)
            if min(last_key, last_atom) - max(e_key, key) + 1 > 0:
                raise Exception(
                    "Key range partially covered:  key:{} key_combo:{} "
                    "mask:{}, last_key:{}, e_key:{}".format(
                        hex(key), hex(key_combo), hex(entry.mask),
                        hex(last_key), hex(e_key)))
    if found_entry is None:
        raise PacmanRoutingException("no entry located")
    return found_entry
