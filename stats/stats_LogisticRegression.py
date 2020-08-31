#!/bin/python
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import warnings; warnings.filterwarnings("ignore")
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report


class Logistic_Regression():
        
    def __init__(self, X_scaled, y_labeled, group_col, f_results, Log_ROC):

        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_labeled, test_size=0.3, random_state=0)

        logreg = LogisticRegression(C=1e5) #(solver='sag')#newton-cg, lbfgs, liblinear, sag, saga
        logreg.fit(X_train, y_train)      
        y_pred = logreg.predict(X_test)
        print("\nAccuracy of logistic regression classifier on test set: {:.2f}'".format(logreg.score(X_test, y_test))+'\n')

        # Confusion Matrix

        matrix = confusion_matrix(y_test, y_pred)
        print('\nConfusion Matrix:\n',str(matrix))

        print(classification_report(y_test, y_pred))

