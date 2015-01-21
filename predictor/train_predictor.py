#!/usr/bin/env python

#Algorithms for training and testing performance of the indie game classifier

import numpy as np
import scipy
import scipy.optimize
import MySQLdb as mdb

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

def run_logreg_training(game_matrix, success,lambda_reg=0.):
    '''
    Runs basic logistic regression training on an input data set
    theta is the parameters vector, x in the data (in this case, game features), y is success
    '''

    #Number of games
    ngames = len(game_matrix)
    #Number of features
    nfeatures = len(game_matrix[0])

    print "Regularization: lambda=",lambda_reg

    #Initialize the initial parameter guesses
    init_parameters = np.zeros(nfeatures).astype(float)

    print "Initial cost: ",logreg_cost_function(init_parameters,ngames,game_matrix,success,lambda_reg)

    res = scipy.optimize.minimize(logreg_cost_function,init_parameters,args=(nfeatures,game_matrix,success,lambda_reg),
                                  method='BFGS',jac=logreg_cost_gradient)

    parameters = res.x
    print "Status: ",res.success, res.message
    print "Final cost: ",logreg_cost_function(parameters,ngames,game_matrix,success,lambda_reg)

    return parameters

def precision(y_pred, y_truth):
    '''
    Given a prediction and a truth value, finds fraction of positives that are true (purity)
    '''
    return len(np.where((y_pred == y_truth) & (y_pred == 1))[0])/float(np.sum(y_pred))

def recall(y_pred, y_truth):
    '''
    Gives fraction of true positives which are found (completeness)
    '''
    return len(np.where((y_pred == y_truth) & (y_pred == 1))[0])/float(np.sum(y_truth))

if __name__ == '__main__':
    f = open("../login.txt")
    login_txt = f.read()
    f.close()
    login = login_txt.split()
    
    con = mdb.connect(login[0],login[1],login[2],'indiedb')
    
    with con:
        print "Getting games data..."
        cur = con.cursor()
        game_matrix, success = extract_features.process_games_from_db(cur)

    #Add the bias unit to the game matrix
    game_mat_ext = np.ones([len(game_matrix),len(game_matrix[0])+1])
    
    #Normalize the features
    xlist = np.where(game_mat_ext[:,1] != -1)[0]
    yr_avg = np.mean(game_mat_ext[xlist,1])
    game_mat_ext[xlist,1] -= yr_avg

    #Do training
    print "Beginning training..."
    
    parameters = run_logreg_training(game_mat_ext, success, lambda_reg=0.1)
    print parameters

    success_pred = hypothesis(game_mat_ext, parameters)
    success_binary = np.zeros_like(success_pred)
    success_slice = np.where(success_pred > 0)[0]
    success_binary[success_slice] += 1

    #Do quality assessment
    print "Success fraction: ",len(success), np.sum(success), np.sum(success_binary)
    print "Accuracy: ",len(np.where(success_binary == success)[0])/float(len(success))
    print "Precision: ",precision(success_binary, success)
    print "Recall: ",recall(success_binary, success)
    
    
