#-*-coding: latin-1 -*-

from flask import g
from scisynergy_flask import app


##########################

def findArea(partial):
    areas_list = getattr(app, 'acmareas')
    retList = list()
    for area in areas_list:
        if area.find(partial) > 0:
            retList.append(area)
        
    return retList