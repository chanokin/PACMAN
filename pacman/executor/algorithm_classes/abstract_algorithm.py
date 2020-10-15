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

from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from pacman.exceptions import PacmanConfigurationException


@add_metaclass(AbstractBase)
class AbstractAlgorithm(object):
    """ Represents the metadata for an algorithm.
    """

    __slots__ = [

        # The ID of the algorithm; must be unique over all algorithms
        "_algorithm_id",

        # A list of inputs that must be provided
        "_required_inputs",

        # A list of inputs that can optionally be provided
        "_optional_inputs",

        # A list of output types
        "_outputs",

        # A list of required input tokens
        "_required_input_tokens",

        # A list of optional input tokens
        "_optional_input_tokens",

        # A list of generated output tokens
        "_generated_output_tokens"
    ]

    def __init__(
            self, algorithm_id, required_inputs, optional_inputs, outputs,
            required_input_tokens, optional_input_tokens,
            generated_output_tokens):
        """
        :param str algorithm_id: The unique ID of the algorithm
        :param list(AbstractInput) required_inputs:
            The inputs required by the algorithm
        :param list(AbstractInput) optional_inputs:
            The optional inputs for the algorithm, which will be provided\
            when available
        :param list(Output) outputs: The output types of the algorithm
        :param list(Token) required_input_tokens:
            Tokens required to have been generated before this algorithm can
            start
        :param list(Token) optional_input_tokens:
            Tokens required to have been generated before this algorithm can
            start if and only if at least one algorithm generates the token
        :param list(Token) generated_output_tokens:
            Tokens generated by this algorithm
        """
        # pylint: disable=too-many-arguments
        self._algorithm_id = algorithm_id
        self._required_inputs = required_inputs
        self._optional_inputs = optional_inputs
        self._outputs = outputs
        self._required_input_tokens = required_input_tokens
        self._optional_input_tokens = optional_input_tokens
        self._generated_output_tokens = generated_output_tokens

    @property
    def algorithm_id(self):
        """ The ID for this algorithm

        :rtype: str
        """
        return self._algorithm_id

    @property
    def required_inputs(self):
        """ The required inputs of the algorithm

        :rtype: list(AbstractInput)
        """
        return self._required_inputs

    @property
    def optional_inputs(self):
        """ The optional inputs of the algorithm

        :rtype: list(AbstractInput)
        """
        return self._optional_inputs

    @property
    def outputs(self):
        """ The outputs of the algorithm

        :rtype: list(Output)
        """
        return self._outputs

    @property
    def required_input_tokens(self):
        """ The required input tokens of the algorithm

        :rtype: list(Token)
        """
        return self._required_input_tokens

    @property
    def optional_input_tokens(self):
        """ The optional input tokens of the algorithm

        :rtype: list(Token)
        """
        return self._optional_input_tokens

    @property
    def generated_output_tokens(self):
        """ The generated output tokens of the algorithm
        """
        return self._generated_output_tokens

    def _get_inputs(self, inputs):
        """ Get the required and optional inputs out of the inputs

        :param dict(str,...) inputs: A dict of input type to value
        :return: A dict of parameter name to value
        :rtype: dict(str,...)
        :raises PacmanConfigurationException:
        """
        matches = dict()

        # Add required inputs, failing if they don't exist
        for required_input in self._required_inputs:
            match = required_input.get_inputs_by_name(inputs)
            if match is None:
                raise PacmanConfigurationException(
                    "Missing required input {} of type {} for algorithm {}"
                    .format(
                        required_input.name, required_input.param_types,
                        self._algorithm_id))
            matches.update(match)

        # Add optional inputs if they exist
        for optional_input in self._optional_inputs:
            match = optional_input.get_inputs_by_name(inputs)
            if match is not None:
                matches.update(match)
        return matches

    def _get_outputs(self, inputs, outputs):
        """ Get the outputs as a dictionary from the given return values

        :param dict(str,...) inputs: A dict of input type to value
        :param iterable outputs:
            A list of values of length equal to self._outputs
        :return: A dict of output type to value
        :rtype: dict(str,...)
        """
        return {
            output_def.output_type: output
            if output_def.file_name_type is None
            else inputs[output_def.file_name_type]
            for output_def, output in zip(self._outputs, outputs)
        }

    @abstractmethod
    def call(self, inputs):
        """ Call the algorithm with the given inputs and return the outputs

        :param inputs: A dict of input type -> value
        :type inputs: dict(str, ...)
        :return: A dict of output type -> value
        :rtype: dict(str, ...)
        """

    @abstractmethod
    def write_provenance_header(self, provenance_file):
        """
        Writes the header info for this algorithm
        So things like name, module, class, function and command_line_arguments

        But not anything about input and outputs as this is done elsewhere

        :param ~io.FileIO provenance_file: File to write to
        """
