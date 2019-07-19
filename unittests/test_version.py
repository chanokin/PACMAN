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

import unittest
import spinn_utilities
import spinn_machine
import pacman


class Test(unittest.TestCase):
    """ Tests for the SCAMP version comparison
    """

    def test_compare_versions(self):
        spinn_utilities_parts = spinn_utilities.__version__.split('.')
        spinn_machine_parts = spinn_machine.__version__.split('.')
        pacman_parts = pacman.__version__.split('.')

        self.assertEqual(spinn_utilities_parts[0], pacman_parts[0])
        self.assertLessEqual(spinn_utilities_parts[1], pacman_parts[1])

        self.assertEqual(spinn_machine_parts[0], pacman_parts[0])
        self.assertLessEqual(spinn_machine_parts[1], pacman_parts[1])
