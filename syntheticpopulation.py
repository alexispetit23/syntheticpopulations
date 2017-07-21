#!/usr/bin/python
# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*-coding:Utf-8 -*

"""
  syntheticpopulation.py
  Auteur : Alexis Petit, PhD Student, Namur University
  Date : 2017 03 22

  This scrip analyses a population of space debris in the GEO region.
"""

import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
from scipy.stats import norm,lognorm
from random import random

def read_simulation(name_file):
  """ Read the snapshot of a simulation of the space debris environment.

  INPUT
  -----

  name_file: string
    Name of the file containing the population.

  RETURN
  ------

  population: dataframe
    The population of space debris.

  """

  f = open(name_file,'r')
  data = f.readlines()
  f.close()

  yy = int(data[1].strip().split()[0])
  mm = int(data[1].strip().split()[1])
  dd = int(data[1].strip().split()[2])
  hh = int(data[1].strip().split()[3])
  mi = int(data[1].strip().split()[4])
  ss = int(data[1].strip().split()[5])
  date = datetime(yy,mm,dd,hh,mi,ss)

  headers = data[2].strip().split()
  population = []
  for row in data[3:]:
    if 'GEOTEST' not in row:
      population.append(row.strip().split())
  population = pd.DataFrame(population,columns=headers)    

  category = {}
  for i in range(0,len(population)-1,1):
    name = population.loc[i]['NAME']
    if name not in category:
        category[name] = 1
    else:
        category[name] += 1

  print
  print '> Categories in the simulation:'      
  print '> ',category
  print

  plt.title(date.strftime('%y/%m/%d'),fontsize=14)
  plt.grid(True)
  plt.rc('xtick', labelsize=12) 
  plt.rc('ytick', labelsize=12) 
  plt.ticklabel_format(style='sci',useOffset=False)
  plt.xlabel('RAAN [deg]',fontsize=14)
  plt.ylabel('i [deg]',fontsize=14)

  for name_selected in category:
    flag = population['NAME']==name_selected
    raan = population['RAAN[deg]'][flag]
    inc = population['i[deg]'][flag]
    plt.plot(raan,inc,'o',markersize=2,label=name_selected.replace('_',' '))   
  plt.xlim([0,360])
  plt.ylim([0,20])
  plt.legend(loc='upper left',fontsize=14)
  plt.savefig('simulation')
  plt.close()
  
  return population
  
  
def read_controls(name_file,var_list,limits,nb_obj):
  """ Infer contraints from data

  INPUTS
  ------

  name_file: string 
    Name of the files used as contraints
  var_list: list
    Variables used [a,i,RAAN,...]
  limits: list

  RETURN
  ------

  controls: dataframe
    Frequencies used as contraints

  """

  #controls empty
  frequencies = {}
  laws = {}

  #read the files containing the contraints
  f = open(name_file,'r')
  data = f.readlines()
  f.close()

  headers = data[2].strip().split()
  population = []
  for row in data[3:]:
    if 'GEOTEST' not in row:
      population.append(row.strip().split())
  population = pd.DataFrame(population,columns=headers)

  print '> Plot the distribution (constraints)' 
  fig = plt.figure(figsize=(10,8))

  for k,var in enumerate(var_list):

    #we select only the objects with the tag 'EKRAN_2_DEB'
    flag = population['NAME']=='EKRAN_2_DEB'
    var_data = [float(i) for i in population[var][flag].tolist()]

    ax = fig.add_subplot(2,2,k+1)
    ax.grid(True)
    ax.set_title(var)
    #ax.hist(var_data,bins=25)
    xmin =  limits[var][0]
    xmax =  limits[var][-1]
    x = np.linspace(xmin, xmax, 100)
    if var == 'BC[m2/kg]':
      #param = lognorm.fit(var_data)
      #laws[var] = param
      #p = lognorm.pdf(x,param[0])
      mu,std = norm.fit(var_data)
      laws[var] = [mu,std]
      p = norm.pdf(x,mu,std)
    else:
      mu,std = norm.fit(var_data)
      laws[var] = [mu,std]
      p = norm.pdf(x,mu,std)
    ax.plot(x,p,'k',linewidth=2)
    ax.set_xlim([xmin,xmax])

    frequencies[var] = create_controls(var,xmin,xmax,mu,std,nb_obj,limits[var])
    print 'freq',frequencies[var]
    
  plt.savefig('controls')
  plt.close()
  
  return frequencies,laws


def create_controls(var,vmin,vmax,mu,std,nb_obj,limits):
  """ From statistical data we compute frequencies

  """
 
  counter = 0
  pop = []
  while(len(pop)<nb_obj):
    if var=='BC[m2/kg]':
      x = np.random.normal(loc=mu,scale=std)
    else:
      x = np.random.normal(loc=mu,scale=std)
    if x>vmin and x<vmax:
      pop.append(x)
      
  frequencies = np.zeros(len(limits)-1)
  for i in range(0,len(limits)-1,1):
    for var in pop:
      if (var>limits[i]) and (var<limits[i+1]):
        frequencies[i] += 1      
    
  return frequencies.tolist()

 
def pop_2_cross_table(population,var_list,n_dim):
    """ Create the initial cross table.

    INPUT
    -----

    population: dataframe
    var_list: list
    n_dim: integer

    RETURN
    ------

    cross_table: float-matrix 
      The cross table generated from the initial population.
    frequencies: dataframe
      Count the frequencies for each variables.

    """

    fig = plt.figure(figsize=(10,8))
    
    bounds = {}
    limits = {}
    frequencies = {}
    k=0
    for var in var_list:
      population[var] = population[var].convert_objects(convert_numeric=True)
      bounds[var],limits[var] = pd.cut(population[var],n_dim[var],retbins=True,labels=False)
      counts = pd.value_counts(bounds[var])
      counts = [counts.loc[i] for i in range(0,len(counts),1)]
      frequencies[var] = counts

      ax = fig.add_subplot(2,2,k+1)
      data_max = len(population[var])
      
      if var == 'BC[m2/kg]':
        mu,sigma = norm.fit(population[var])
        n, bins, patches = plt.hist(population[var],50,normed=1,facecolor='green',alpha=0.75)
        p = mlab.normpdf(bins,mu,sigma)#*data_max
        #plt.plot(bins,p,'r--',linewidth=2)
        param = lognorm.fit(population[var])
        xmin =  min(population[var])
        xmax =  max(population[var])
        x = np.linspace(xmin, xmax, 100)
        p = lognorm.pdf(x,param[0])
        plt.plot(x,p,'r--',linewidth=2)
        #plt.plot(x,p,'k',linewidth=2)
      else:
        mu,sigma = norm.fit(population[var])
        n, bins, patches = plt.hist(population[var],50,normed=1,facecolor='green',alpha=0.75)
        p = mlab.normpdf(bins,mu,sigma)#*data_max
        plt.plot(bins,p,'r--',linewidth=2)
        
      for i in range(0,n_dim[var]+1,1):
        x = min(population[var])+((max(population[var])-min(population[var])))*i/n_dim[var]
        plt.axvline(x, color='k', linestyle='--')

      k += 1
      #ax.grid(True)
      ax.set_title(var)
      
    plt.savefig('initial_frequencies')
    plt.close()
    
    cross_table = np.zeros((n_dim['a[m]'],n_dim['i[deg]'],n_dim['RAAN[deg]'],n_dim['BC[m2/kg]'])) 
    for i in range(0,len(limits['a[m]'])-1,1):
      for j in range(0,len(limits['i[deg]'])-1,1):
        for k in range(0,len(limits['RAAN[deg]'])-1,1):
          for l in range(0,len(limits['BC[m2/kg]'])-1,1):
            flag = (bounds['a[m]']==i) & (bounds['i[deg]']==j) & (bounds['RAAN[deg]']==k) & (bounds['BC[m2/kg]']==l)
            cross_table[i,j,k,l] = len(population[flag])
      
    return cross_table,frequencies,limits


def ipf_process(cross_table,frequencies,controls):
    """ Apply the IPF process.

    INPUTS
    ------

    cross_table: float-matrix
    frequencies: dataframe
    controls: dataframe
    var_list: list

    RETURN
    ------

    new_cross_table: float-matrix

    """
      
    epsilon = 10E-8
    distance = 1
    list_distance = []
    counter = 0

    while (epsilon<distance) and (counter<100):

      cross_table_saved = cross_table.copy()
      
      cross_table,total = update_variable_cross_table(cross_table,frequencies,controls) 
      
      distance = 0
      for i in range(0,n_dim['a[m]'],1):
        for j in range(0,n_dim['i[deg]'],1):
          for k in range(0,n_dim['RAAN[deg]'],1):
            for l in range(0,n_dim['BC[m2/kg]'],1):
              distance += np.abs(cross_table[i,j,k,l]-cross_table_saved[i,j,k,l])

      list_distance.append(distance)          
      counter += 1

    print cross_table

    plt.grid(True)
    plt.rc('xtick', labelsize=12) 
    plt.rc('ytick', labelsize=12) 
    plt.ticklabel_format(style='sci',useOffset=False)
    plt.xlabel('Iteration',fontsize=14)
    plt.ylabel('Distance',fontsize=14)
    plt.xlim([0,len(list_distance)-1])
    plt.yscale('log')
    plt.plot(list_distance)   
    plt.savefig('convergence')
    plt.close()   
      
    return cross_table


def update_variable_cross_table(cross_table,frequency,controls):
  """ Fitting of the cross table

  INPUTS
  ------

  cross_table: float-matrix
  frequency: dataframe
  controls: dataframes

  RETURN
  ------

  cross_table: float-matrix
  new_frequency: dataframe
      
  """
 
  new_frequency = frequency.copy()
  for item in new_frequency:
    dim = len(new_frequency[item])
    new_frequency[item] = np.zeros(dim).tolist()
  for i in range(0,len(frequency['a[m]']),1):
    for j in range(0,len(frequency['i[deg]']),1):
      for k in range(0,len(frequency['RAAN[deg]']),1):
        for l in range(0,len(frequency['BC[m2/kg]']),1):
          cross_table[i,j,k,l] = cross_table[i,j,k,l]*controls['a[m]'][i]/frequency['a[m]'][i]
          new_frequency['a[m]'][i] += cross_table[i,j,k,l]
          new_frequency['i[deg]'][j] += cross_table[i,j,k,l]
          new_frequency['RAAN[deg]'][k] += cross_table[i,j,k,l]
          new_frequency['BC[m2/kg]'][l] += cross_table[i,j,k,l]
  frequency = new_frequency.copy()
  
  new_frequency = frequency.copy()
  for item in new_frequency:
    dim = len(new_frequency[item])
    new_frequency[item] = np.zeros(dim).tolist()  
  for i in range(0,len(frequency['a[m]']),1):
    for j in range(0,len(frequency['i[deg]']),1):
      for k in range(0,len(frequency['RAAN[deg]']),1):      
        for l in range(0,len(frequency['BC[m2/kg]']),1):
          cross_table[i,j,k,l] = cross_table[i,j,k,l]*controls['i[deg]'][j]/frequency['i[deg]'][j]
          new_frequency['a[m]'][i] += cross_table[i,j,k,l]
          new_frequency['i[deg]'][j] += cross_table[i,j,k,l]      
          new_frequency['RAAN[deg]'][k] += cross_table[i,j,k,l]
          new_frequency['BC[m2/kg]'][l] += cross_table[i,j,k,l]
  frequency = new_frequency.copy() 
  
  new_frequency = frequency.copy()
  for item in new_frequency:
    dim = len(new_frequency[item])
    new_frequency[item] = np.zeros(dim).tolist()
  for i in range(0,len(frequency['a[m]']),1):
    for j in range(0,len(frequency['i[deg]']),1):
      for k in range(0,len(frequency['RAAN[deg]']),1):
        for l in range(0,len(frequency['BC[m2/kg]']),1):
          cross_table[i,j,k,l] = cross_table[i,j,k,l]*controls['RAAN[deg]'][k]/frequency['RAAN[deg]'][k]
          new_frequency['a[m]'][i] += cross_table[i,j,k,l]
          new_frequency['i[deg]'][j] += cross_table[i,j,k,l]      
          new_frequency['RAAN[deg]'][k] += cross_table[i,j,k,l]
          new_frequency['BC[m2/kg]'][l] += cross_table[i,j,k,l]
  frequency = new_frequency.copy()

  new_frequency = frequency.copy()
  for item in new_frequency:
    dim = len(new_frequency[item])
    new_frequency[item] = np.zeros(dim).tolist()
  for i in range(0,len(frequency['a[m]']),1):
    for j in range(0,len(frequency['i[deg]']),1):
      for k in range(0,len(frequency['RAAN[deg]']),1):
        for l in range(0,len(frequency['BC[m2/kg]']),1): 
          cross_table[i,j,k,l] = cross_table[i,j,k,l]*controls['BC[m2/kg]'][l]/frequency['BC[m2/kg]'][l]
          new_frequency['a[m]'][i] += cross_table[i,j,k,l]
          new_frequency['i[deg]'][j] += cross_table[i,j,k,l]      
          new_frequency['RAAN[deg]'][k] += cross_table[i,j,k,l]
          new_frequency['BC[m2/kg]'][l] += cross_table[i,j,k,l]
  frequency = new_frequency.copy()

  
  return cross_table,new_frequency
  

def cross_table_2_pop(cross_table,frequencies,limits,laws,var_list):
  """ Convert the cross table to a population of objects

  """

  population = []
  for i in range(0,len(frequencies['a[m]']),1):
    for j in range(0,len(frequencies['i[deg]']),1):
      for k in range(0,len(frequencies['RAAN[deg]']),1):
        for l in range(0,len(frequencies['BC[m2/kg]']),1):
          counter = 0
          while counter<cross_table[i,j,k,l]:
            sma = limits['a[m]'][i] + (limits['a[m]'][i+1]-limits['a[m]'][i])*random()
            while(True):
              x = random()
              inc = limits['i[deg]'][j] + (limits['i[deg]'][j+1]-limits['i[deg]'][j])*random()
              p = norm(laws['i[deg]'][0], laws['i[deg]'][1]).pdf(inc)
              if x<p:
                break             
            ecc = 0.1*random()
            while(True):
              x = random()
              raan = limits['RAAN[deg]'][k] + (limits['RAAN[deg]'][k+1]-limits['RAAN[deg]'][k])*random()
              p = norm(laws['RAAN[deg]'][0], laws['RAAN[deg]'][1]).pdf(raan)
              if x<p:
                break
            omega = 360.*random()
            ma = 360.*random()
            bc = limits['BC[m2/kg]'][l] + (limits['BC[m2/kg]'][l+1]-limits['BC[m2/kg]'][l])*random()
            population.append([sma,ecc,inc,raan,omega,ma,bc])
            counter += 1
  
  #['a[m]', 'e[-]', 'i[deg]', 'RAAN[deg]', 'Omega[deg]', 'MA[deg]', 'BC[m2/kg]', 'S[m]', 'IDNORAD', 'NAME']      
  headers = ['a[m]', 'e[-]', 'i[deg]', 'RAAN[deg]', 'Omega[deg]', 'MA[deg]', 'BC[m2/kg]']
  population = pd.DataFrame(population,columns=headers) 
        
  return population


if __name__ == "__main__": 

  # FIRST STEP: read the population coming from our simulation
  print
  print 'Read the data of the simulation'
  population = read_simulation('simulation1.txt')
  flag = population['NAME']=='EKRAN_2_DEB'
  population = population[flag]

  # SECOND STEP: create the cross-table
  print
  print 'Compute the cross-table'
  var_list = ['a[m]','i[deg]','RAAN[deg]','BC[m2/kg]']
  n_dim = {}
  n_dim['a[m]'] = 1
  n_dim['i[deg]'] = 4
  n_dim['RAAN[deg]'] = 3
  n_dim['BC[m2/kg]'] = 1

  cross_table,frequencies,limits = pop_2_cross_table(population,var_list,n_dim)
  print 'Cross-table'
  print cross_table
  print 'Frequencies'
  print frequencies
  print 'Limits'
  print limits
  print

  # THIRD STEP: calculate the controls
  nb_obj = 400
  print
  print 'Compute the contraints'
  controls,laws = read_controls('simulation1.txt',var_list,limits,nb_obj)
  print '> ',controls
  print 

  # FOURTH STEP: apply the IPF process
  new_cross_table = ipf_process(cross_table,frequencies,controls)
  #print 'New cross-table'
  #print cross_table

  #check total
  total = 0
  for i in range(0,n_dim['a[m]'],1):
    for j in range(0,n_dim['i[deg]'],1):
      for k in range(0,n_dim['RAAN[deg]'],1):
        for l in range(0,n_dim['BC[m2/kg]'],1):
          total += cross_table[i,j,k,l]
  print 'New total = ',total

  # FITH STEP: compute the synthetic population
  new_population = cross_table_2_pop(cross_table,frequencies,limits,laws,var_list)
  raan = new_population['RAAN[deg]']
  inc = new_population['i[deg]']

  #plt.grid(True)
  plt.rc('xtick', labelsize=12) 
  plt.rc('ytick', labelsize=12) 
  plt.ticklabel_format(style='sci',useOffset=False)
  plt.xlabel('RAAN [deg]',fontsize=14)
  plt.ylabel('i [deg]',fontsize=14)
  plt.plot(population['RAAN[deg]'],population['i[deg]'],'x',markersize=2,label='Synthetic population')
  plt.plot(raan,inc,'o',markersize=2,label='Simulation')
  for j in range(0,n_dim['i[deg]'],1):
    x = limits['i[deg]'][j]
    plt.axhline(x, color='k', linestyle='--')
  x = limits['i[deg]'][j+1]
  plt.axhline(x, color='k', linestyle='--')
  for k in range(0,n_dim['RAAN[deg]'],1):
    x = limits['RAAN[deg]'][k]
    plt.axvline(x, color='k', linestyle='--')
  x = limits['RAAN[deg]'][k+1]
  plt.axvline(x, color='k', linestyle='--')
  plt.xlim([290,340])
  plt.ylim([7,17])
  plt.savefig('synthetic_population')
  plt.close()
