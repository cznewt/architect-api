#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ansible inventory script to get the metadata from the Architect service.
"""
import sys
import posix


def cli():

    # TODO: HTTP request to Architect service
    sys.exit(posix.EX_OK)


if __name__ == '__main__':
    cli()
