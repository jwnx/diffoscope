# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
# Copyright © 2016 Ximin Luo <infinity0@pwned.gg>
#
# diffoscope is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# diffoscope is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import re
import logging

from diffoscope.tools import tool_required
from diffoscope.difference import Difference

from .utils.file import File
from .utils.command import Command
from .utils.libarchive import LibarchiveContainer, list_libarchive

logger = logging.getLogger(__name__)


# TODO: this would also be useful for Go archives. Currently those are handled
# by StaticLibFile, but then readelf complains with "Error: Not an ELF file".
# ArFile gives slightly more reasonable output, e.g. a readable plain diff of
# the __.PKGDEF member which is just a text file containing the Go interface.

class ArContainer(LibarchiveContainer):
    def get_adjusted_members(self):
        members = list(super().get_adjusted_members())
        known_ignores = {
            "/": "this is the symbol table, already accounted for in other output",
            "//": "this is the table for GNU long names, already accounted for in the archive filelist",
        }
        filtered_out = [p for p in members if p[0] in known_ignores]
        if filtered_out:
            for k, v in filtered_out:
                logger.debug("ignored ar member '%s' because %s", k, known_ignores[k])
        return [p for p in members if p[0] not in known_ignores]

class ArSymbolTableDumper(Command):
    @tool_required('nm')
    def cmdline(self):
        return ['nm', '-s', self.path]

class ArFile(File):
    CONTAINER_CLASS = ArContainer
    FILE_TYPE_RE = re.compile(r'\bar archive\b')

    def compare_details(self, other, source=None):
        return [Difference.from_command(ArSymbolTableDumper, self.path, other.path),
                Difference.from_text_readers(list_libarchive(self.path),
                                             list_libarchive(other.path),
                                             self.path, other.path, source="file list")]
