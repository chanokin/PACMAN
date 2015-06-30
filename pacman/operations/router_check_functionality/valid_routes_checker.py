from pacman import exceptions
from collections import namedtuple
import logging
logger = logging.getLogger(__name__)

# Define an internal class for placements
PlacementTuple = namedtuple('PlacementTuple', 'x y p')


class ValidRouteChecker(object):

    def __init__(self, partitioned_graph, placements, routing_infos,
                 routing_tables, machine):
        """

        :param partitioned_graph: the subgraph of the problem spec
        :param placements: the placements container
        :param routing_infos:  the routing info container
        :param routing_tables: the routing tables generated by the\
                    routing algorithum
        :param machine: the spinnmachine object
        :type machine: spinnmachine.machine.Machine object
        :return: None
        :raise None: this method does not raise any known excpetion
        """
        self._partitioned_graph = partitioned_graph
        self._placements = placements
        self._routing_infos = routing_infos
        self._routing_tables = routing_tables
        self._machine = machine

    def validate_routes(self):
        """ Go though the placements given during init and check that the\
            routing entries within the routing tables support reach the\
            correction destinations as well as not producing any cycles.

        :return: None
        :raises PacmanRoutingException: when either no routing table entry is\
                    found by the search on a given router, or a cycle is\
                    detected

        """
        for placement in self._placements.placements:
            outgoing_edges_for_partitioned_vertex = \
                self._partitioned_graph.outgoing_subedges_from_subvertex(
                    placement.subvertex)

            # locate all placements to which this placement/subvertex will
            # communicate with for a given key_and_mask and search its
            # determined destinations
            key_and_masks = \
                self._routing_infos.get_key_and_masks_for_partitioned_vertex(
                    placement.subvertex)

            # locate each set for a given key_and_mask
            for key_and_mask in key_and_masks:
                destination_placements = list()
                for outgoing_edge in outgoing_edges_for_partitioned_vertex:
                    edge_key_and_masks = \
                        self._routing_infos.get_keys_and_masks_from_subedge(
                            outgoing_edge)
                    for edge_key_and_mask in edge_key_and_masks:
                        if edge_key_and_mask == key_and_mask:
                            dest_placement = \
                                self._placements.get_placement_of_subvertex(
                                    outgoing_edge.post_subvertex)
                            dest_tuple = PlacementTuple(x=dest_placement.x,
                                                        y=dest_placement.y,
                                                        p=dest_placement.p)
                            if dest_tuple not in destination_placements:
                                destination_placements.append(dest_tuple)
                # search for these destinations
                self._search_route(placement, destination_placements,
                                   key_and_mask)

    def _search_route(self, source_placement, dest_placements, key_and_mask):
        """ Locate if the routing tables work for the source to desks as\
            defined

        :param source_placement: the placement from which the search started
        :param dest_placements: the placements to which this trace should visit\
        only once
        :param key_and_mask: the key and mask associated with this set of
        subedges
        :type source_placement: instance of
        pacman.model.placements.placement.Placement
        :type dest_placements: iterable of PlacementTuple
        :type key_and_mask: instanceof
        pacman.model.routing_info.key_and_mask.BaseKeyAndMask
        :return: None
        :raise PacmanRoutingException: when the trace completes and there are\
                    still destinations not visited
        """
        for dest in dest_placements:
            logger.debug("[{}:{}:{}]".format(dest.x, dest.y, dest.p))

        located_dests = set()

        self._start_trace_via_routing_tables(source_placement, key_and_mask.key,
                                             located_dests)

        # start removing from located_dests and check if dests not reached
        failed_to_reach_dests = list()
        for dest in dest_placements:
            if dest in located_dests:
                located_dests.remove(dest)
            else:
                failed_to_reach_dests.append(dest)

        # check for error if trace didnt reach a destination it was meant to
        error_message = ""
        if len(failed_to_reach_dests) > 0:
            output_string = ""
            for dest in failed_to_reach_dests:
                output_string += "[{}:{}:{}]".format(dest.x, dest.y, dest.p)
            source_processor = "[{}:{}:{}]".format(
                source_placement.x, source_placement.y, source_placement.p)
            error_message += ("failed to locate all dstinations with subvertex"
                              " {} on processor {} with keys {} as it didnt "
                              "reach dests {}".format(
                                  source_placement.subvertex.label,
                                  source_processor, key_and_mask,
                                  output_string))

        # check for error if the trace went to a destination it shouldn't have
        if len(located_dests) > 0:
            output_string = ""
            for dest in located_dests:
                output_string += "[{}:{}:{}]".format(dest.x, dest.y, dest.p)
            source_processor = "[{}:{}:{}]".format(
                source_placement.x, source_placement.y, source_placement.p)
            error_message += (
                "Path shows that packets from subvertex {} on processor {}"
                " went to incorrect processors. The cores it went to "
                "incorrectly were {}".format(
                    source_placement.subvertex.label, source_processor,
                    output_string))

        # raise error if required
        if error_message != "":
            raise exceptions.PacmanRoutingException(error_message)
        else:
            logger.debug("successful test between {} and {}"
                         .format(source_placement.subvertex.label,
                                 dest_placements))

    def _start_trace_via_routing_tables(
            self, source_placement, key, reached_placements):
        """this method starts the trace, by using the source placemnts
        router and tracing from the route.

        :param source_placement: the soruce placement used by the trace
        :param key: the key being used by the partitioned_vertex which resides\
                    on the soruce placement
        :param reached_placements: the placements reached during the trace
        :return: None
        :raises None: this method does not raise any known exception
        """
        current_router_table = self._routing_tables.get_routing_table_for_chip(
            source_placement.x, source_placement.y)
        visited_routers = set()
        current_router_table_tuple = (current_router_table.x,
                                      current_router_table.y)
        visited_routers.add(current_router_table_tuple)

        # get src router
        entry = self._locate_routing_entry(current_router_table, key)
        self._recursive_trace_to_dests(
            entry, current_router_table, source_placement.x,
            source_placement.y, key, visited_routers, reached_placements)

    # locates the next dest pos to check
    def _recursive_trace_to_dests(self, entry, current_router, chip_x, chip_y,
                                  key, visited_routers, reached_placements):
        """ this method recurively searches though routing tables till
        no more entries are registered with this key

        :param entry: the orginal entry used by the first router which
        resides on the soruce placement chip.
        :param current_router: the router currently being visited during the
         trace
        :param key: the key being used by the partitioned_vertex which resides
        on the soruce placement
        :param visited_routers: the list of routers which have been visited
        during this tracve so far
        :param reached_placements: the placements reached during the trace
        :param chip_x: the x coordinate of the chip being considered
        :param chip_y: the y coordinate of the chip being considered
        :type entry: spinnmachine.multicast_routing_entry.MulticastRoutingEntry
        :type current_router:
        pacman.model.routing_tables.multicasr_routing_table.MulticastRoutingTable
        :type chip_x: int
        :type chip_y: int
        :type key: int
        :type visited_routers: iterable of :
        pacman.model.routing_tables.multicasr_routing_table.MulticastRoutingTable
        :type reached_placements: iterable of placement_tuple
        :return: None
        :raise None: this method does not raise any known exceptions
        """

        # determine where the route takes us
        chip_links = entry.link_ids
        processor_values = entry.processor_ids

        # if goes downa chip link
        if len(chip_links) > 0:

            # also goes to a processor
            if len(processor_values) > 0:
                self._check_processor(processor_values, current_router,
                                      reached_placements)
            # only goes to new chip
            for link_id in chip_links:

                # locate next chips router
                machine_router = \
                    self._machine.get_chip_at(chip_x, chip_y).router
                link = machine_router.get_link(link_id)
                next_router = \
                    self._routing_tables.get_routing_table_for_chip(
                        link.destination_x, link.destination_y)
                if next_router is None:
                    raise exceptions.PacmanNotExistException(
                        "The link {} from router {} does not go to a router. "
                        "This was expected to have a router from entry {}. "
                        "Please fix and try again."
                        .format(link, machine_router, entry))

                # check that we've not visited this router before
                self._check_visited_routers(next_router.x, next_router.y,
                                            visited_routers)

                # locate next entry
                entry = self._locate_routing_entry(next_router, key)

                # get next route value from the new router
                self._recursive_trace_to_dests(
                    entry, next_router, link.destination_x, link.destination_y,
                    key, visited_routers, reached_placements)

        # only goes to a processor
        elif len(processor_values) > 0:
            self._check_processor(processor_values, current_router,
                                  reached_placements)

    @staticmethod
    def _check_visited_routers(chip_x, chip_y, visited_routers):
        """ Check if the trace has visited this router already
        :param chip_x: the x coordinate of the chip being checked
        :param chip_y: the y coordinate of the chip being checked
        :param visited_routers: routers already visted
        :type chip_x: int
        :type chip_y: int
        :type visited_routers: iterable of :
        pacman.model.routing_tables.multicasr_routing_table.MulticastRoutingTable
        :return: None
        :raise PacmanRoutingException: when a router has been visited twice.
        """
        visited_routers_router = (chip_x, chip_y)
        if visited_routers_router in visited_routers:
            raise exceptions.PacmanRoutingException(
                "visited this router before, there is a cycle here. "
                "The routers I've currently visited are {} and the router i'm "
                "visitiing is {}"
                .format(visited_routers, visited_routers_router))
        else:
            visited_routers.add(visited_routers_router)

    @staticmethod
    def _check_processor(processor_ids, current_router, reached_placements):
        """ Check for processors to be removed

        :param reached_placements: the placements to which the trace visited
        :param processor_ids: the processor ids which the last router entry\
                    said the trace should visit
        :param current_router: the current router being used in the trace
        :return: None
        :raise None: this method does not raise any known exceptions
        """

        dest_x, dest_y = current_router.x, current_router.y
        for processor_id in processor_ids:
            reached_placements.add(PlacementTuple(dest_x, dest_y,
                                                  processor_id))

    @staticmethod
    def _locate_routing_entry(current_router, key):
        """ locate the entry from the router based off the subedge

        :param current_router: the current router being used in the trace
        :param key: the key being used by the source placement
        :return None:
        :raise PacmanRoutingException: when there is no entry located on this\
                    router.
        """
        for entry in current_router.multicast_routing_entries:
            key_combo = entry.mask & key
            if key_combo == entry.routing_entry_key:
                return entry
        else:
            raise exceptions.PacmanRoutingException("no entry located")
