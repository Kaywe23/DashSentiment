import csv
import tensorflow as tf
import pickle
import numpy as np
from tensorflow.python.lib.io import file_io
import argparse
from nltk.tokenize import word_tokenize
import nltk
nltk.download('punkt')
nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer
import io
import csv
import pandas as pd
import sys
reload(sys)
sys.setdefaultencoding('latin-1')
from datetime import datetime
import time
import math as math
from time import *

lemmatizer = WordNetLemmatizer()
from StringIO import StringIO


hidden_nodes_1 = 2638
hidden_nodes_2 = int(hidden_nodes_1 * 0.5)

beta=0.001
n_classes = 2
batch_size = 100
hm_epochs = 1
batch_count = 100
display_step = 1
logs_path = './tmp/Test.py/' + datetime.now().isoformat()
csv_file='/home/user/train_converted_vermischt.csv'
csv_file2='/home/user/vector_test_converted.csv'
checkpoint='model_DashApp.ckpt'


with open('lexikon2.pickle', mode='rb') as p:
    lexikon = pickle.load(p)





graph = tf.Graph()
with graph.as_default():

    tf_train_dataset = tf.placeholder('float')
    tf_train_labels = tf.placeholder('float')

    #Hidden RELU layer 1
    weights_1 = tf.Variable(tf.truncated_normal([2638, hidden_nodes_1], stddev=math.sqrt(2.0 / (2638))))
    biases_1 = tf.Variable(tf.random_normal([hidden_nodes_1]))

    #Hidden RELU layer 2
    weights_2 = tf.Variable(tf.truncated_normal([hidden_nodes_1, hidden_nodes_2], stddev=math.sqrt(2.0 / hidden_nodes_1)))
    biases_2 = tf.Variable(tf.random_normal([hidden_nodes_2]))

    # Output layer
    weights_3 = tf.Variable(tf.truncated_normal([hidden_nodes_2, n_classes], stddev=math.sqrt(2.0 / hidden_nodes_2)))
    biases_3 = tf.Variable(tf.random_normal([n_classes]))



    # Hidden RELU layer 1
    logits_1 = tf.matmul(tf_train_dataset, weights_1) + biases_1
    hidden_layer_1 = tf.nn.relu(logits_1)

    # Dropout on hidden layer: RELU layer
    keep_prob = tf.placeholder("float")
    hidden_layer_1_dropout = tf.nn.dropout(hidden_layer_1, keep_prob)

    # Hidden RELU layer 2
    logits_2 = tf.matmul(hidden_layer_1_dropout, weights_2) + biases_2
    hidden_layer_2 = tf.nn.relu(logits_2)

    # Dropout on hidden layer: RELU layer
    hidden_layer_2_dropout = tf.nn.dropout(hidden_layer_2, keep_prob)

    # Output layer
    logits_3 = tf.matmul(hidden_layer_2_dropout, weights_3) + biases_3



    # Minimize error using cross entropy
    cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits_3, labels=tf_train_labels))
    # Loss function with L2 Regularization with decaying learning rate beta=0.5
    regularizers = tf.nn.l2_loss(weights_1) + tf.nn.l2_loss(weights_2) + \
                    tf.nn.l2_loss(weights_3)
    cost = tf.reduce_mean(cost + beta * regularizers)

    # Gradient Descent
    #optimizer = tf.train.AdamOptimizer(learning_rate=0.0001).minimize(cost)
    # Decaying learning rate
    global_step = tf.Variable(0)  # count the number of steps taken.
    start_learning_rate = 0.001
    learning_rate = tf.train.exponential_decay(start_learning_rate, global_step, 100000, 0.96, staircase=True)
    optimizer = tf.train.GradientDescentOptimizer(learning_rate).minimize(cost, global_step=global_step)


    # Predictions for the training
    train_prediction = tf.nn.softmax(logits_3)

    #define Checkpoint
    saver = tf.train.Saver()
    tf_log = 'tf.log'

    #summary
    correct = tf.equal(tf.argmax(train_prediction, 1), tf.argmax(tf_train_labels, 1))
    accuracy = tf.reduce_mean(tf.cast(correct, tf.float32))
    cost_summary = tf.summary.scalar("cost", cost)
    acc_summary = tf.summary.scalar("accuracy", accuracy)

    summary_op = tf.summary.merge_all()

    feature_sets = []
    labels = []
    counter = 0
    with tf.gfile.Open(csv_file2, 'rb') as gc_file:
        lines2 = gc_file.readlines()

        for zeile in lines2:
            counter+=1
            try:
                features = list(eval(zeile.split('::')[0]))
                label = list(eval(zeile.split('::')[1]))
                feature_sets.append(features)
                labels.append(label)
            except:
                pass
            if counter >= 1000:
                break

        test_1 = np.array(feature_sets)
        valid_dataset = test_1

        test_2 = np.array(labels)
        valid_labels = test_2





def trainDNN():



    with tf.Session(graph=graph) as sess:

        tf.global_variables_initializer().run()
        print("Initialized")

        writer = tf.summary.FileWriter(logs_path, graph=graph)
        print('Start Training')

        try:
            epoch = int(open(tf_log,'r').read().split('\n')[-2])+1
            print('START:',epoch)
        except:
            epoch=1

        for epoch in range(hm_epochs):
            t1=clock()
            if epoch != 1:
                saver.restore(sess, checkpoint)
            avg_cost=0.
            avg_trainacc=0.

            with tf.gfile.Open(csv_file, 'rb') as gcs_file:
                lines = gcs_file.readlines()

                zaehler = 0
                for zeile in lines:
                    zaehler += 1
                    label = zeile.split(':::')[0]
                    tweet = zeile.split(':::')[1]
                    woerter = word_tokenize(tweet.lower())
                    woerter = [lemmatizer.lemmatize(i) for i in woerter]
                    features = np.zeros(len(lexikon))
                    for wort in woerter:
                        if wort.lower() in lexikon:
                            indexWert = lexikon.index(wort.lower())
                            features[indexWert] += 1

                    train_dataset = np.array([list(features)])
                    train_labels = np.array([eval(label)])

                    feed_dict = {tf_train_dataset: np.array(train_dataset), tf_train_labels: np.array(train_labels),
                                 keep_prob: 0.5}
                    _, c, predictions, summary = sess.run([optimizer, cost, train_prediction, summary_op],
                                                          feed_dict=feed_dict)
                    writer.add_summary(summary, epoch * batch_count + zaehler)

                    avg_cost += c / batch_count
                    avg_trainacc += (accuracy.eval(
                        {tf_train_dataset: train_dataset, tf_train_labels: train_labels, keep_prob: 1.0})) / batch_count

                    if zaehler >= batch_count:
                        break

                    if (zaehler % 1000 == 0):
                        print("Minibatch loss at step {}: {}".format(zaehler, c))
                        print("Validation accuracy: {:.9f}".format(accuracy.eval(
                            {tf_train_dataset: valid_dataset, tf_train_labels: valid_labels, keep_prob: 1.0})))
                    t2 = clock()
            saver.save(sess, checkpoint)
            t = t2 - t1
            if epoch % display_step == 0:
                print "Epoche:", '%04d' % (epoch + 1), "of", '%04d' % (hm_epochs), "average cost=", "{:.9f}".format(avg_cost), \
                        "Time=", "{:.9f}".format(t), "s,", "Epoch Trainaccuracy: {}".format(avg_trainacc)

            with open(tf_log, 'a') as f:
                f.write(str(epoch) + '\n')



        feature_sets = []
        labels = []
        with tf.gfile.Open(csv_file2, 'rb') as gc_file:
            lines2 = gc_file.readlines()

            for zeile in lines2:
                try:
                    features = list(eval(zeile.split('::')[0]))
                    label = list(eval(zeile.split('::')[1]))
                    feature_sets.append(features)
                    labels.append(label)
                except:
                    pass

            test_x = np.array(feature_sets)
            test_datasets = test_x

            test_y = np.array(labels)
            test_labels = test_y
            print('Test Set', test_datasets.shape, test_labels.shape)



            writer.flush()


            print 'Test Accuracy:',accuracy.eval({tf_train_dataset: test_datasets, tf_train_labels: test_labels, keep_prob:1.0})

#trainDNN()

def useDNN(input_data):

    with tf.Session(graph=graph) as sess:
        tf.global_variables_initializer().run()
        saver.restore(sess, checkpoint)
        woerter = word_tokenize(input_data.lower())
        woerter = [lemmatizer.lemmatize(i) for i in woerter]
        features = np.zeros(len(lexikon))
        for wort in woerter:
            if wort.lower() in lexikon:
                indexWert = lexikon.index(wort.lower())
                features[indexWert] += 1

        features = np.array(list(features))
        result = (sess.run(tf.argmax(logits_3.eval(feed_dict={tf_train_dataset: [features],keep_prob:1.0 }), 1)))
        if result[0] == 0:
            return -1
        elif result[0] == 1:
            return 1




