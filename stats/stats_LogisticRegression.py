#!/bin/python
from os import path
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import warnings; warnings.filterwarnings("ignore")
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, roc_auc_score


class Logistic_Regression():
        
    def __init__(self, X_scaled, y_labeled, group_col, path_results):

        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_labeled, test_size=0.3, random_state=0)

        logreg = LogisticRegression(C=1e5) #(solver='sag')#newton-cg, lbfgs, liblinear, sag, saga
        logreg.fit(X_train, y_train)      
        y_pred = logreg.predict(X_test)
        print("\nAccuracy of logistic regression classifier on test set: {:.2f}'".format(logreg.score(X_test, y_test))+'\n')

        # Confusion Matrix

        matrix = confusion_matrix(y_test, y_pred)
        print('\nConfusion Matrix:\n',str(matrix))
        with open(path.join(path_results, 'confusion_matrix.txt'),'w') as f:
            f.write('\nConfusion Matrix:\n')
            f.write(str(matrix)+'\n')

        print(classification_report(y_test, y_pred))
        with open(path.join(path_results, 'classification_report.txt'),'w') as f:
            f.write('\nClassification Report:\n')
            f.write(classification_report(y_test, y_pred)+'\n')

        # ROC Curve
        logit_roc_auc = roc_auc_score(y_test, logreg.predict(X_test))
        fpr, tpr, thresholds = roc_curve(y_test, logreg.predict_proba(X_test)[:,1])
        plt.figure()
        plt.plot(fpr, tpr, label='Logistic Regression (area = %0.2f)' % logit_roc_auc)
        plt.plot([0, 1], [0, 1],'r--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver operating characteristic')
        plt.legend(loc="lower right")
        plt.savefig(path.join(path_results, 'Log_ROC.png'))
#        plt.show()
        print('Logistic Regression DONE')