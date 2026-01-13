# Copyright (C) 2023 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Provides utilities for Ansys SCADE Python Wrapper."""

# ----------------------------------------------------------------------------
# naming
# ----------------------------------------------------------------------------

from typing import List


def tokenize_name(fullname: str) -> List[str]:
    """Return the tokens of a word."""
    tokens = []
    for name in fullname.split('_'):
        # there must be a more clever algorithm, one pass
        # for now, adapt an existing one
        if not name:
            tokens.append('')
            continue
        prev = name[0]
        lower = prev
        for c in name[1:]:
            if c.isupper() and prev != '_':
                lower += '_'
            prev = c
            lower += c
        lst = lower.split('_')
        # merge successive uppercase singletons
        prev = lst[0]
        for token in lst[1:]:
            if prev.isupper() and len(token) == 1 and token.isupper():
                prev += token
            else:
                tokens.append(prev)
                prev = token
        tokens.append(prev)
    return tokens


def lower_name(name: str) -> str:
    """Get the snake case form of a word."""
    return '_'.join(tokenize_name(name)).lower()


def upper_name(name: str) -> str:
    """Get the screaming snake case form of a word."""
    return '_'.join(tokenize_name(name)).upper()


def title_name(name: str) -> str:
    """Get the Pascal case form of a word."""
    return ''.join([token.title() for token in tokenize_name(name)])


def acronym(name: str) -> str:
    """Return the acronym of a word."""
    return ''.join([token[0] for token in tokenize_name(name)]).upper()


def local_name(name: str) -> str:
    """Get the camel case form of a word."""
    name = title_name(name)
    return name[0].lower() + name[1:]
