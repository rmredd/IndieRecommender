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
    init_parameters = np.random.uniform(-0.1,0.1,nfeatures)

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
    if np.sum(y_pred) == 0:
        #If there are no predicted positives, return zero
        return 0.
    return len(np.where((y_pred == y_truth) & (y_pred == 1))[0])/float(np.sum(y_pred))

def recall(y_pred, y_truth):
    '''
    Gives fraction of true positives which are found (completeness)
    '''

    return len(np.where((y_pred == y_truth) & (y_pred == 1))[0])/float(np.sum(y_truth))

def f1_score(y_pred, y_truth):
    p = precision(y_pred, y_truth)
    r = recall(y_pred, y_truth)
    if p == 0 and r == 0:
        return 0.
    return 2*p*r/(p+r)

def estimate_threshold(success_prediction, success):
    '''
    Estimates the best threshold to use for predictive purposes, based on F1 score
    '''

    thresholds = np.array(range(100))*0.01
    f1_test = np.zeros_like(thresholds)
    for i in range(len(thresholds)):
        success_binary = np.zeros_like(success_prediction)
        success_binary[np.where(success_prediction > thresholds[i])[0]] += 1
        f1_test[i] = f1_score(success_binary, success)
    return thresholds[np.argmax(f1_test)]

def run_generalized_training_and_test(game_matrix, success, lambda_reg, training_function, cost_function):
    '''
    Given input data and a chosen algorithm, does training and test; returns fit parameters
    Note that this is generalized, so different algorithms can be tested; assumes that inputs to the
    training function are game_matrix, success, and lambda_reg (or another single scalar value)
    '''

    ngames = len(game_matrix)
    #Randomly select 80% of training data
    slice_permute = np.random.permutation(ngames)
    ngames_train = int(np.floor(0.8*ngames))
    slice_train = slice_permute[:ngames_train]
    slice_test = slice_permute[ngames_train:]
    print "Beginning initial training..."
    parameters = training_function(game_matrix[slice_train], success[slice_train], lambda_reg=lambda_reg)
    print "Getting cost and results on test set..."

    print "Test cost: ",cost_function(parameters,ngames-ngames_train,game_matrix[slice_test],success[slice_test],lambda_reg)
    #Get prediction of success
    success_pred = hypothesis(game_matrix[slice_test], parameters)
    success_binary = np.zeros_like(success_pred)
    success_slice = np.where(success_pred > 0.5)[0]
    success_binary[success_slice] += 1
    print np.min(success_pred), np.max(success_pred)

    print "Success fraction: ",len(success[slice_test]), np.sum(success[slice_test]), np.sum(success_binary)
    print "Accuracy: ",len(np.where(success_binary == success[slice_test])[0])/float(ngames-ngames_train),np.sum(success_binary)
    print "Precision: ",precision(success_binary, success[slice_test])
    print "Recall: ",recall(success_binary, success[slice_test])
    print "F1 score: ",f1_score(success_binary, success[slice_test])

    return parameters

def store_parameters_in_database(name, threshold, year_avg, parameters, feature_list, cur, remake_table=False):
    '''
    Stores a single set of fitting parameters in a database
    
    This also stores the offset used in the year data, and the prediction threshold
    The first parameter is the name for the metric the parameters are based on, and will
    be the name entered in the database
    The last input parameter is a cursor for the relevant database
    
    Finally, there's a flag for making the table anew, if the parameter set changes
    '''

    if remake_table:
        cur.execute("DROP TABLE IF EXISTS Parameters")
        create_command = "CREATE TABLE Parameters(Id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(40), threshold FLOAT, year_avg FLOAT"
        for feature in feature_list:
            create_command += ", "+feature+" FLOAT"
        create_command += ")"
        cur.execute(create_command)

    #Insert this set of parameter values into the table
    insert_command = "INSERT INTO Parameters (name, threshold, year_avg"
    for feature in feature_list:
        insert_command += ", "+feature
    insert_command += ") VALUES ('"+name+"', "+str(threshold)+", "+str(year_avg)
    for parameter in parameters:
        insert_command += ", "+str(parameter)
    insert_command += ")"
    cur.execute(insert_command)

    return

if __name__ == '__main__':
    f = open("../login.txt")
    login_txt = f.read()
    f.close()
    login = login_txt.split()
    
    con = mdb.connect(login[0],login[1],login[2],'indiedb')
    
    with con:
        print "Getting games data..."
        cur = con.cursor()
        game_matrix, games_df = extract_features.process_games_from_db(cur)
        success = extract_features.make_full_success_vector(games_df,8.,50.)

    #Add the bias unit to the game matrix
    game_mat_ext = np.ones([len(game_matrix),len(game_matrix[0])+1])
    game_mat_ext[:,1:] = game_matrix
    
    #Normalize the features
    xlist = np.where(game_mat_ext[:,1] != -1)[0]
    yr_avg = np.mean(game_mat_ext[xlist,1])
    game_mat_ext[xlist,1] -= yr_avg

    #Do training
    print "Running training using logistic regression..."
    lambda_reg = 0.001
    parameters = run_generalized_training_and_test(game_mat_ext, success, lambda_reg, run_logreg_training, logreg_cost_function)
    print parameters
    
    
