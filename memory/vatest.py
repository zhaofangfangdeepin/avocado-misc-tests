#!/usr/bin/env python
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright: 2017 IBM
# Author:Praveen K Pandey<praveen@linux.vnet.ibm.com>
#

import os
import shutil

from avocado import Test
from avocado import main
from avocado.utils import process, build, memory
from avocado.utils.software_manager import SoftwareManager


class VATest(Test):
    """
    Performs Virtual address space validation

    :avocado: tags=memory, power
    """

    def setUp(self):
        '''
        Build VA Test
        '''

        # Check for basic utilities
        smm = SoftwareManager()
        self.scenario_arg = int(self.params.get('scenario_arg', default=1))
        self.n_chunks = nr_pages = 0
        if self.scenario_arg not in range(1, 9):
            self.cancel("Test need to skip as scenario will be 1-9")
        elif self.scenario_arg in [7, 8, 9]:
            if memory.meminfo.Hugepagesize.g != 16:
                self.cancel(
                    "Test need to skip as 16GB huge need to configured")
        if self.scenario_arg not in [1, 2]:
            max_hpages = (0.9 * memory.meminfo.MemFree.m) / \
                memory.meminfo.Hugepagesize.m
            self.exist_pages = memory.get_num_huge_pages()
            memory.set_num_huge_pages(max_hpages)
            nr_pages = memory.get_num_huge_pages()
            self.n_chunks = (
                (nr_pages * memory.meminfo.Hugepagesize.m) / 16384)

        for packages in ['gcc', 'make']:
            if not smm.check_installed(packages) and not smm.install(packages):
                self.cancel('%s is needed for the test to be run' % packages)

        shutil.copyfile(os.path.join(self.datadir, 'va_test.c'),
                        os.path.join(self.teststmpdir, 'va_test.c'))

        shutil.copyfile(os.path.join(self.datadir, 'Makefile'),
                        os.path.join(self.teststmpdir, 'Makefile'))

        build.make(self.teststmpdir)

    def test(self):
        '''
        Execute VA test
        '''
        os.chdir(self.teststmpdir)

        result = process.run('./va_test -s %s -n %s'
                             % (self.scenario_arg,
                                self.n_chunks), shell=True, ignore_status=True)
        for line in result.stdout.splitlines():
            if 'failed' in line:
                self.fail("test failed, Please check debug log for failed"
                          "test cases")

    def tearDown(self):
        if self.scenario_arg not in [1, 2]:
            memory.set_num_huge_pages(self.exist_pages)


if __name__ == "__main__":
    main()
