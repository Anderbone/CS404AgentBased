#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 24 19:28:41 2019

@author: sujiaxin
"""
from u1851015 import AuctionClient

ports = 8020
bidderid = "1851015"
verbo = True

bidbot = AuctionClient(port=ports, mybidderid=bidderid, verbose=verbo)
bidbot.play_auction()
