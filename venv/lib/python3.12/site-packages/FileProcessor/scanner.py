# -*- coding: utf-8 -*-
# Copyright (c) CDU

"""Model Docstrings

"""

from __future__ import absolute_import
from __future__ import annotations
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os


class Scanner:
    """
    Scanner for files.

    it will scan directory(s) and return all file path.
    if deep bt 1, it will add dir path to scan list and scan it.
    """

    def ascan(self, src):
        directories = []
        if isinstance(src, (list, tuple)):
            directories.extend(src)
        else:
            directories.append(src)

        for directory in directories:
            directory = os.path.abspath(directory)
            if self.is_hidden_item(directory):
                continue
            for item in os.listdir(directory):
                item = os.path.join(directory, item)
                if os.path.isdir(item):
                    directories.append(item)
                else:
                    if self.is_hidden_item(item): continue
                    yield item

    def scan(self, src):
        return [file for file in self.ascan(src)]

    @staticmethod
    def is_hidden_item(file_or_directory):
        filename = str(os.path.basename(file_or_directory))
        if filename.startswith('.'):
            return True
        else:
            return False
