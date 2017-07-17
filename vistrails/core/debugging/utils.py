import copy
import sys, os
import random
import logging

goodbad = [True, False]
numtests = 10

def evaluate(x, formula):
	local = x
	logging.debug("local is: "+str(local))
	logging.debug("formula is: "+formula)
	ret = eval(formula)
	logging.debug("ret is "+str(ret))
	return ret


def loadtests(filename):
	fileicareabout = open(filename,"r")
	text = fileicareabout.readlines()
	fileicareabout.close()
	workflow = text[0]

	if (workflow != "null\n"):
		script,func = (workflow[:-1]).split(",")
		workflow = getattr(__import__(script), func)
	else:
		workflow = None
	formula = text[1]
	cost = text[2]
	cols = text[3][:-1].split(",")
	alllines = text[4:]


	allexperiments = []
	allresults = [] # experiments and their results

	for e in alllines:
		exp = (e[:-1]).split(",")
		allexperiments.append(exp)
  

	for e in allexperiments:
		x = copy.deepcopy(e)
		x.append(evaluate(e, formula))
		allresults.append(x)

	return [workflow,allexperiments,allresults,formula,cost,cols]
