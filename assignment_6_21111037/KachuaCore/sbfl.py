#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module to generate a test-suite with optimized number of tests.
"""
import sys
sys.path.insert(0,'../Submission/')
from sbflSubmission import fitnessScore
import copy
import csv
import random
#import map
import numpy as np
import time
from interpreter import *
import argparse
import math
class Executor():
    # Execute the program using the input test
    # and find which components are executed by test
    # and the final turtle location.
    def __init__(self):
        pass

    def execute(self, ir, inputList={}, end=0):
        '''
        returns coverage and turtle location at the end of program.
        '''
        coverage = []
        inptr = ConcreteInterpreter(ir)
        terminated = False
        inptr.initProgramContext(inputList)
        # The maximum time given to execute a test case.
        while time.time() <= end:
            coverage.append(inptr.pc)
            terminated = inptr.interpret()
            if terminated:
                break
        if time.time() >= end:
            print(f"[SBFL] Program took too long to execute. Terminated\n")
        else:
            print("[SBFL] Program Ended.\n")
        
        #final turtle location.
        turtle_pos = inptr.trtl.pos()
        
        return list(set(coverage)), turtle_pos
    
#Genetic Algorithm takes object of type Individual
class Individual():
    def __init__(self,individual):
        self.individual = individual #activity matrix
        self.fitness = None #fitness-score of activity matrix
        self.fitness_valid = False #flag varible used by Genetic Algorithm

#GenticAlgo class is implementation of Genetic Algorithm.
class GeneticAlgo():
    def __init__(self,spectrum,popsize,cxpb,mutpb,ngen,verbose):
        """
        Parameters
        ----------
        spectrum : list
            takes a test-suite of a program generated by SBFL class.
        popsize : int
            size of the population.
        cxpb : float
            crossover probability.
        mutpb : float
            mutation probability.
        ngen : int
            number of times genetic algorithm will iterate.
        verbose : boolean
            whther to show log of GA to console or not.
        """
        self.program_spectrum = spectrum
        self.cxpb = cxpb
        self.mutpb = mutpb
        self.ngen = ngen
        self.popsize = popsize
        self.population = None
        self.verbose = verbose
        self.ntests = len(spectrum)
        
    def genPopulation(self):
        """
        This function generate n number of random individual/spectrums 
        using actual program's spectrum, here n = self.popsize 
        """
        self.population = []
        for _ in range(self.popsize):
            newspectrum = copy.deepcopy(self.program_spectrum)
            #Generate random size test suites
            random.shuffle(newspectrum)
            Toremove = random.randint(1,len(newspectrum) -1);
            for __ in range(Toremove):
             newspectrum.pop(random.randint(0,len(newspectrum)-1))   
            self.population.append(Individual(newspectrum))
    def selBest(self, population, k):
        """
        This function selects best k individuals from population.
        if |population| > k, then best k individuals are returned in 
        sorted order
        ----------
        population : list of Individuals
            list of individual from where best-k individuals will be selected.
        k : int
            number of best individuals to return.
        Returns
        -------
        list
        """
        #temp contains : fitnes value, test case size, index of individual in population
        temp = []
        for i,ind in enumerate(population):
            temp.append([ind.fitness,len(ind.individual),i])
        temp = sorted(temp,reverse=False) #####ToDo : Fix it to generic way
        
        if len(temp) >=k:
            return [population[i[2]] for i in temp[:k]]
        else:
            return [population[i[2]] for i in temp]
        
    def cxAndmut(self,P1,P2):
        """
        This function performs crossover and mutation according to self.cxpb
        and self.mutpb values. then returns new offsprings.
        ----------
        P1 : Individual
            first Individual
        P2 : Individual
            second individual
        Returns
        -------
        ind1 : Individual
            first offspring.
        ind2 : Individual
            second offspring.
        """
        ind1 = copy.deepcopy(P1)
        ind2 = copy.deepcopy(P2)
        if random.random() < self.cxpb:
            Toshuffle = random.randint(1,min(len(ind1.individual),len(ind2.individual)))
            for _ in range(Toshuffle):
                index1 = random.randint(0, len(ind1.individual) - 1);
                index2 = random.randint(0, len(ind2.individual) - 1);
                ind1.individual[index1], ind2.individual[index2] = ind2.individual[index2], ind1.individual[index1]
        if random.random() <self.mutpb:
            if random.random() < 0.5 :
                #add randomly few test cases
                for ind in [ind1,ind2]:
                    Toadd = random.randint(0,self.ntests -1)
                    for _ in range(Toadd):
                            ind.individual.append(random.choice(self.program_spectrum))
            else:
                #remove test cases randomly
                for ind in [ind1,ind2]:
                    Toremove = random.randint(0,len(ind.individual) -1)
                    for _ in range(Toremove):
                        ind.individual.pop(random.randint(0,len(ind.individual) -1))
        #remove fitness to None and flag to false i.e it is a new individual
        ind1.fitness = None
        ind1.fitness_valid =False
        ind2.fitness = None
        ind2.fitness_valid =False
        return ind1,ind2
    
    def removeDuplicates(self, population):
        """
        This is a utility function to remove duplicate Individuals from a list 
        of population. Here duplicate means spectrum1 == spectrum2
        Note : Dictonary datastructure is used to optimize the search time.
        Since for list its O(n) where n = |population| and for dictonary its
        O(1)
        Parameters
        ----------
        population : list of Individuals
        Returns
        -------
        list of Individuals with no duplicates.
        """
        temp = self.selBest(population,len(population));
        D = {}
        for i in temp:
            act_mat = np.array(i.individual);
            act_mat = act_mat[:,:act_mat.shape[1]-1]
            #if str(i.individual) not in D:
            if str(act_mat) not in D:
                #D[str(i.individual)] = i
                D[str(act_mat)] = i
        population = list(D.values())
        return self.selBest(population, len(population))
    
    def execute(self):
        """
        This function will start executing GA.
        The best individuals can be accessed by self.population
        
        Returns
        -------
        None.
        """
        #geneate population.
        self.genPopulation()
        
        #compute fitness of Individuals in population
        fitnesses = map(fitnessScore, self.population)
        for ind,fit in zip(self.population,fitnesses):
            ind.fitness = fit
            ind.fitness_valid = True
            
        #sort population according to fitness score
        self.population = self.selBest(self.population,len(self.population))
        
        #Iterate ngen times.
        for itr in range(1,self.ngen + 1):
            offsprings = []
            for i in range(0,len(self.population)-1,2):
                P1,P2 = self.population[i], self.population[i+1]
                O1,O2 = self.cxAndmut(P1,P2)
                
                O1.fitness = fitnessScore(O1);
                O1.fitness_valid =True
                O2.fitness = fitnessScore(O2);
                O2.fitness_valid =True
                
                #compute minimum fitness-score of parent and offspring
                fp,fo = min(P1.fitness,P2.fitness),min(O1.fitness,O2.fitness)
                
                #compute test total test cases in parents and offsprings
                lp,lo =len(P1.individual) + len(P2.individual),len(O1.individual) + len(O2.individual)
                
                #best individual of current population
                Tb = self.population[0]
                
                if fo <fp or ((fo ==fp ) and (lo<=lp)):
                    for O in [O1,O2]:
                        if len(O.individual) <= 2* len(Tb.individual):
                            offsprings.append(O)
            #add offsprings into population.
            self.population += offsprings
            
            #remove duplicate Individuals
            self.population = self.removeDuplicates(self.population)
            
            #Sort population according to the fitness-score.
            self.population = self.selBest(self.population,self.popsize)

            if self.verbose:
                print("Iteration : {}, Best fit-score : {}, |pop|: {}, |Test-Suite| :{}".format(itr,self.population[0].fitness,len(self.population),len(self.population[0].individual)))                

class SBFL():
    def __init__(self,ir,timeLimit = 10):
        self.ir = ir
        self.allinputList =[]
        self.timeLimit = timeLimit

    def run(self,tests):
        self.allinputList = tests
        
        total_tests = len(tests)
        
        #initialize ir interpreter.
        executer = Executor()
        
        #total number of compoents in ir, each line is considered as a component.
        components = len(self.ir)
        
        #Note : last column contains index of test, used for fault oracle. 
        activity_mat = np.zeros((total_tests,components + 1),dtype = 'int')
        
        for index in range(total_tests):
            inputList = self.allinputList[index]
            endLimit = time.time() + self.timeLimit 

            #get which components are executed.
            coverage,_ = executer.execute(self.ir,inputList=inputList,end =endLimit)
            
            #set executed compoent to 1
            activity_mat[index,coverage] = 1
            
            #index of test is also store in the activity matrix, 
            #later it will help to fault oracle to find whether test fails or 
            #passes.
            activity_mat[index,-1] = index
        
        return activity_mat
    
def mutateinput(inp):
    choice = random.random() 
    if  choice <0.3:
        return -inp
    else:
        if inp == 0:
            bit_len = 1
        else:
            bit_len = math.floor(math.log(abs(inp), 2) + 1)
        return inp ^ (random.getrandbits(bit_len + 1))
  
def generateTests(inputVars,total_tests):
    allinputList = []
    if inputVars == []:
        allinputList = [{} for i in range(total_tests)]
    else:
        #initially select random numbers as initial seed 
        inputDict = {}
        for var in inputVars:
            inputDict[var] = random.randint(-100,100)
        allinputList.append(inputDict)
        del inputDict
        for i in range(total_tests -1):
            inputDict = {}
            for var in inputVars:
                inputDict[var] = mutateinput(allinputList[i][var])
            allinputList.append(inputDict)
        #print("Generated Random Inputs  ",allinputList)
    return allinputList


def testsuiteGenerator(ir1,ir2,inputVars= [],Ntests = 10,timeLimit = 10,popsize = 50, cxpb = 0.5 , mutpb = 0.5,ngen = 50,verbose = True):
    #generate random tests
    original_tests = generateTests(inputVars = inputVars, total_tests= Ntests)
    
    #execute correct program to get activity matrix. it will be used by 
    #genetic algorithm to optimize the test-suite size
    s = SBFL(ir = ir1,timeLimit=timeLimit)
    A= s.run(original_tests)
    
    original_test_suites = np.array(A,dtype='int')
    original_test_suites = original_test_suites[:,:original_test_suites.shape[1]-1].tolist()
    
    #convert to list for further use.
    A = A.tolist()
    
    #optimize test-suite and get the best indivudual return by GA.
    g = GeneticAlgo(spectrum=A, popsize=popsize, cxpb=cxpb, mutpb=mutpb, ngen=ngen,verbose =verbose )
    g.execute()
    pop = g.population
    best_individual = pop[0].individual
    
    #get tests indexs
    reduced_tests = []
    for tests in best_individual:
        reduced_tests.append(original_tests[tests[-1]])
    
    reduced_act_mat = np.array(best_individual,dtype='int')
    reduced_act_mat = reduced_act_mat[:,:reduced_act_mat.shape[1]-1]
    
    #run correct and buggy program to get error vector [Fault Oracle]
    spectrum = np.zeros((len(reduced_tests),len(ir2) + 1),dtype = 'int')
    executer = Executor()
    for i,test in enumerate(reduced_tests):
        _,ir1_trltl_pos = executer.execute(ir = ir1 , end=time.time() + timeLimit, inputList=test)
        cov,ir2_trltl_pos = executer.execute(ir = ir2 , end=time.time() + timeLimit, inputList=test)
        spectrum[i,cov] = 1
        if ir1_trltl_pos == ir2_trltl_pos:
            spectrum[i,-1] = 0 # test-case passes.
        else:
            spectrum[i,-1] = 1 # test-case fails.

    return original_test_suites,original_tests,reduced_act_mat,reduced_tests,spectrum.tolist()