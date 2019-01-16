import tensorflow as tf
import numpy as np
import math
from extract_training_data import extract_training_data
import matplotlib.pyplot as plt
from ml_helpers_new import one_hot_matrix, create_placeholders, initialize_parameters, forward_propagation, compute_cost, predict, random_mini_batches
from timeit import default_timer as timer

#disables AVX warning from being displayed
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

def model(X_train, Y_train, X_dev, Y_dev, numOutputNodes, learning_rate = 0.0001,
          iterations = 5000, minibatch_size = 32, layer1 = 12, layer2 = 8, beta = 0, dropout = 0.5, istanh1 = True, istanh2 = True, batchnorm = True, print_cost=True):
    """ Three-layer NN to predict Fe coordination numbers around oxygen.
        Default is L2 regularization and Adam. Return optimized parameters.

        Arguments:
        ----------------------------
        X_train : array (170, 64% of data)

        Y_train : array (numOutputNodes, 64% of data)

        X_dev : array (170, 16% of data)

        Y_dev : array(numOutputNodes, 16% of data)

        numOutputNodes: int
            Determined by examning the maximum Fe coordination number of each oxygen.
        
        learning_rate, iterations, minibatch_size: as named

        layer1, layer2: number of nodes in the first and second hidden layers

        beta: regularization parameter for L2 regularization in the cost function

        dropout: probability of keeping a node in dropout

        istanh1, istanh2: determines whether the first and second layers use a tanh or relu activation function (True: tanh, False: relu)

        print_cost: boolean, decides whether or not to print the cost during training

        Returns:
        -----------------------------
        parameters : dict
            weights and biases of each layer.{'W1':W1, 'b1':b1, 'W2':W2, 'b2':b2, 'W3':W3, 'b3':b3}
    """
    
    # reset all variables to allow the network to be trained multiple times with different hyperparameters
    sess = tf.Session()
    tf.reset_default_graph()

    # tf.set_random_seed(1)                             # to keep consistent results
    seed = 1                                          # to keep consistent results
    n_x = X_train.shape[0]                            # n_x : input size (the other dimension is the number of examples in the train set)
    n_y = Y_train.shape[0]                            # n_y : output size
    costs = []                                        # holds data for graphing

    # Create Placeholders of shape (n_x, n_y)
    X, Y = create_placeholders(n_x, n_y)
    parameters = initialize_parameters(layer1, layer2, numOutputNodes)  # Initialize parameters
    training = tf.placeholder_with_default(False, shape=(), name='training') # Create a boolean to use for implementing batch norm and dropout correctly

    # Forward propagation: Build the forward propagation in the tensorflow graph
    Z3 = forward_propagation(X, parameters, training, istanh1, istanh2, batchnorm, dropout)

    # Cost function: Add cost function to tensorflow graph
    cost = compute_cost(Z3, Y, parameters, beta)

    # update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS) # this section used to implement batch normalization
    # with tf.control_dependencies(update_ops):
    #     # Backpropagation: Define the tensorflow optimizer. Use an AdamOptimizer.
    #     optimizer = tf.train.AdamOptimizer(learning_rate).minimize(cost)
    optimizer = tf.train.AdamOptimizer(learning_rate).minimize(cost)
    
    # Initialize all the variables
    init = tf.global_variables_initializer()

    # Calculate the correct predictions
    correct_prediction = tf.equal(tf.argmax(Z3), tf.argmax(Y))
        
    # Calculate accuracy on the test set
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))

    # Start the session to compute the tensorflow graph
    with tf.Session() as sess:
        sess.run(init)

        # Print the hyperparameters for this particular model
        print('Learning Rate: %s, Mini-Batch Size: %d, Beta: %s, %d Nodes in Layer 1, %d Nodes in Layer 2, %d Output Nodes, %d Iterations, %s Dropout Prob, First Layer Tanh: %s, Second Layer Tanh: %s, Batch Norm: %s' \
        % (str(learning_rate).rstrip('0'), minibatch_size, str(beta).rstrip('0'), layer1, layer2, numOutputNodes, iterations, str(dropout).rstrip('0'), istanh1, istanh2, batchnorm))
        
        for epoch in range(iterations):
            epoch_cost = 0.                       # Defines a cost related to an epoch
            seed = seed + 1
            minibatches = random_mini_batches(X_train, Y_train, minibatch_size, seed)
            num_minibatches = len(minibatches) 

            for minibatch in minibatches:
                # Select a minibatch
                (minibatch_X, minibatch_Y) = minibatch
                
                # Run the session on one minibatch, and add the cost to the epoch cost
                _ , minibatch_cost = sess.run([optimizer, cost], feed_dict={X: minibatch_X, Y: minibatch_Y, training: True})
                epoch_cost += minibatch_cost / num_minibatches
            
            # Print the cost every epoch
            # if print_cost == True and epoch % 100 == 0:
            #     print("Cost after iteration %i: %f" % (epoch, epoch_cost))
            # if print_cost == True and epoch % 5 == 0:
            #     costs.append(epoch_cost)
            if print_cost == True and epoch % 250 == 0: # used during testing to ensure gradient descent is working properly
                train_accuracy = accuracy.eval({X: X_train, Y: Y_train, training: False})
                print("Training cost after iteration %i: %f, accuracy: %f" % (epoch, epoch_cost, train_accuracy))
                
                dev_cost = sess.run(cost, feed_dict={X:X_dev, Y: Y_dev, training: False})
                dev_accuracy = accuracy.eval({X: X_dev, Y: Y_dev, training: False})
                print("Dev cost after iteration %i: %f, accuracy: %f" % (epoch, dev_cost, dev_accuracy))

        # # Plot the cost
        # if print_cost:
        #     iter_num = np.arange(iterations / 5) * 5
        #     plt.plot(iter_num, np.squeeze(costs))
        #     plt.ylabel('cost')
        #     plt.xlabel('iterations')
        #     # plt.title("Learning rate =" + str(learning_rate))
        #     plt.show()

        # Save the parameters in a variable
        parameters = sess.run(parameters)
    
        train_acc = accuracy.eval({X: X_train, Y: Y_train, training: False})
        dev_acc = accuracy.eval({X: X_dev, Y: Y_dev, training: False})
        accs = [train_acc, dev_acc]

        # test_acc = accuracy.eval({X: X_test, Y: Y_test, training: False}) # use this later when doing the final test on the selected set of hyperparameters
        # print("Test Accuracy:", test_acc)

        # print("Train Accuracy:", train_acc)
        # print("Dev Accuracy:", dev_acc)

    return accs, parameters

def train_multiple_models(X_train, Y_train, X_dev, Y_dev, numOutputNodes, iterations, hyperparams, print_cost = True):
    """ Allows for the training of different settings of hyperparameters in one function.
        
        Arguments:
        ----------------------------
        X_train, Y_train, X_dev, Y_dev, numOutputNodes, iterations, print_cost: used in model()
        hyperparams: a list of dictionaries of hyperparameters for testing

        Returns:
        ----------------------------
        results: a dictionary of the dev accuracy corresponding to each setting of hyperparameters
        best: a list of the settings of hyperparameters with the lowest dev set error
        params[best]: the parameters corresponding to the best hyperparameter setting
    """
    
    results = {}
    params = {}

    try:
        # extract the hyperparameters from one item in hyperparams
        for h in hyperparams:
            learning_rate = h['learning_rate'] 
            layer1 = h['layer1']
            layer2 = h['layer2']
            minibatch_size = h['minibatch_size']
            beta = h['beta']
            dropout = h['dropout']
            istanh1 = h['istanh1']
            istanh2 = h['istanh2']
            batchnorm = h['batchnorm']
            
            # train the model with the given hyperparameters
            accs, parameters = model(X_train, Y_train, X_dev, Y_dev, numOutputNodes, learning_rate, iterations, minibatch_size, layer1, layer2, beta, dropout, istanh1, istanh2, batchnorm, print_cost)
            
            results[frozenset(h.items())] = accs[1] # store the dev test accuracies in a dictionary
            params[frozenset(h.items())] = parameters # do the same for the learned parameters, to be retrieved at the end
    
    except KeyboardInterrupt: # allow for exiting the for loop in case we want to stop testing all the hyperparameters; to use, press Ctrl+C in terminal
        pass

    best = max(results, key=results.get) # finds what setting of hyperparameters had the highest dev accuracy

    return results, list(best), params[best]


# def final_evaluation(X_test, Y_test, parameters): # currently not functional
#     """ Evaluates the learned parameters on the test set.

#         Arguments:
#         ----------------------------
#         X_test, Y_test: test set
#         parameters: the learned parameters resulting from gradient descent

#         Returns:
#         ----------------------------
#         prediction: the predicted labels
#         actual: the actual, correct labels
#         test_acc: the percentage of examples currently identified
#     """

#     prediction = np.array(predict(X_test, parameters))
#     actual = np.array(Y_test.argmax(axis=0))

#     compare = np.equal(prediction, actual) # compares the two arrays element-wise, returns an array with True when both are equal
#     test_acc = np.round(np.sum(compare) / compare.size, 8) # sum the array and divide by its size to find the final test accuracy

#     return (prediction, actual, test_acc)

if __name__ == "__main__":

    start = timer()
    X_train, X_dev, X_test, Y1, Y2, Y3, numOutputNodes = extract_training_data(cutoff_radius = 2.6)
    
    # multi-class classification; convert from array(1, divider) to a one-hot matrix of array(numOutputNodes, divider)
    Y_train = one_hot_matrix(Y1.squeeze(), numOutputNodes)
    Y_dev = one_hot_matrix(Y2.squeeze(), numOutputNodes)
    Y_test = one_hot_matrix(Y3.squeeze(), numOutputNodes)

    # sets of hyperparameters to test, in a grid search
    learning_rates = [0.0001]
    layer1s = [5, 25, 125]  # Liang has tried: 14/9, 12/8, 10/8, 7/6
    layer2s = [5, 25, 125]
    minibatch_sizes = [16]
    betas = [0.03]
    dropouts = [1.0]
    istanh1s = [False]
    istanh2s = [True]
    batchnorms = [True]

    # list comprehension to create sets of hyperparameters for testing
    hyperparams = [{'learning_rate': a, 'layer1': b, 'layer2': c, 'minibatch_size': d, 'beta': e, 'dropout': f, 'istanh1': g, 'istanh2': h, 'batchnorm': i} for a in learning_rates for b in layer1s \
    for c in layer2s for d in minibatch_sizes for e in betas for f in dropouts for g in istanh1s for h in istanh2s for i in batchnorms]

    results, best, params = train_multiple_models(X_train, Y_train, X_dev, Y_dev, numOutputNodes, 3001, hyperparams, print_cost = True)
    #prediction, actual, test_acc = final_evaluation(X_test, Y_test, params)

    print(results)
    print("Best Hyperparameters:", str(best))
    #print("Predict:", str(prediction))
    #print("Actuals:", str(actual))
    #print("Test Accuracy:", str(test_acc))

    # print how long the training took in total
    end = timer()
    time = end - start
    print("Time taken:", math.floor(time/3600), "hours,", math.floor((time/3600 - math.floor(time/3600)) * 60), "minutes, and", round((time/60 - math.floor(time/60)) * 60, 2), "seconds")