from spinn_utilities.overrides import overrides


class SpecificBoardTagResource(object):
    """
    A resource that allocates a tag on a specific board before the class\
    needing it has been built.
    """

    __slots__ = [
        # The host IP address that will receive the data from this tag
        "_ip_address",

        # The port number that data from this tag will be sent to, or None
        # if the port is to be assigned elsewhere
        "_port",

        # A boolean flag that indicates if the SDP headers are stripped before
        # transmission of data
        "_strip_sdp",

        # A fixed tag id to assign, or None if any tag is OK
        "_tag",

        # The identifier that states what type of data is being transmitted
        # through this IPTag
        "_traffic_identifier",

        # The board IP address that this tag is going to be placed upon
        "_board"
    ]

    def __init__(self, board, ip_address, port, strip_sdp, tag=None,
                 traffic_identifier="DEFAULT"):
        """
        :param board: The IP address of the board to which this tag is to be\
            associated with
        :type board: str
        :param ip_address: The IP address of the host that will receive data\
            from this tag
        :type ip_address: str
        :param port: The port that will
        :type port: int or None
        :param strip_sdp: Whether the tag requires that SDP headers are\
            stripped before transmission of data
        :type strip_sdp: bool
        :param tag: A fixed tag id to assign, or None if any tag is OK
        :type tag: int
        :param traffic_identifier: The traffic to be sent using this tag; \
            traffic with the same traffic_identifier can be sent using\
            the same tag
        :type traffic_identifier: str
        """
        # pylint: disable=too-many-arguments
        self._board = board
        self._ip_address = ip_address
        self._port = port
        self._strip_sdp = strip_sdp
        self._tag = tag
        self._traffic_identifier = traffic_identifier

    @property
    def ip_address(self):
        """ The IP address to assign to the tag.

        :return: An IP address
        :rtype: str
        """
        return self._ip_address

    @property
    def port(self):
        """ The port of the tag

        :return: The port of the tag
        :rtype: int
        """
        return self._port

    @property
    def traffic_identifier(self):
        """ The traffic identifier for this IPTag
        """
        return self._traffic_identifier

    @property
    def strip_sdp(self):
        """ Whether SDP headers should be stripped for this tag

        :return: True if the headers should be stripped, False otherwise
        :rtype: bool
        """
        return self._strip_sdp

    @property
    def tag(self):
        """ The tag required, or None if any tag is OK.

        :return: The tag or None
        :rtype: int
        """
        return self._tag

    @property
    def board(self):
        """ The board IP address that this tag is to reside on

        :return: IP address
        """
        return self._board

    def get_value(self):
        return [
            self._board, self._ip_address, self._port, self._strip_sdp,
            self._tag, self._traffic_identifier]

    def __repr__(self):
        return (
            "IPTagResource(board_address={}, ip_address={}, port={}, "
            "strip_sdp={}, tag={}, traffic_identifier={})".format(
                self._board, self._ip_address, self._port, self._strip_sdp,
                self._tag, self._traffic_identifier))
