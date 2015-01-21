#!/usr/bin/env python

#Algorithms for training and testing performance of the indie game classifier

import numpy as np


import extract_features

def sigmoid(x):
    '''                                                                                                                                                    
    Sigmoid function, 1/(1+e^-x)                                                                                                                           
    Input: x                                                                                                                                               
    If x is a numpy array or matrix, performs operation on every element                                                                                   
    '''

    return 1./(1+np.exp(-x))

def hypothesis(x,theta):
    '''
    Hypothesis function -- assumes x is at least an array, but works on matrices
    '''
    y = sigmoid( np.dot(theta,np.transpose(x) ) )

    return y

def logreg_cost_function(theta,m,x,y,lambda_reg):
    '''
    Cost function for the multi-class regression
    Computes vector of costs for all different samples
    '''

    cost = 1./m*np.sum( -y*np.log(hypothesis(x,theta)) - (1.-y)*np.log(1-hypothesis(x,theta)) )
    #Adding regularization
    cost += lambda_reg/(2.*m)*np.sum(theta[1:]**2)

    return cost

def logreg_cost_gradient(theta,m,x,y,lambda_reg):
    '''
    Gradient of cost function for multi-class regression
    '''

    grad = 1./m*np.inner( hypothesis(x,theta)-y , np.transpose(x) )

    #Adding regularization
    grad[1:] += lambda_reg/m*theta[1:]

    return grad

def run_logreg_training():
    return

if __name__ == '__main__':
    pass
