#!/bin/python
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import warnings; warnings.filterwarnings("ignore")
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

class Logistic_Regression():
		
    def __init__(self, data, group_col, f_results, Log_ROC):

        plt.rc("font", size=14)
        open(f_results,'w').close()

        groups = []
        for val in data[group_col]:
            if val not in groups:
                groups.append(val)
        if len(groups) == 2:
            print('2 groups detected: ', groups[0],'; ', groups[1])
            data.loc[data[group_col] == groups[0], group_col] = 0
            data.loc[data[group_col] == groups[1], group_col] = 1

        # Create dummy variables. That is variables with only two values, zero and one.
        # cat_vars=['job','marital','education','default','housing','loan',
                  # 'contact','month','day_of_week','poutcome']
        # for var in cat_vars:
        #     cat_list='var'+'_'+var
        #     cat_list = pd.get_dummies(data[var], prefix=var)
        #     data1=data.join(cat_list)
        #     data=data1

        # data_vars=data.columns.values.tolist()
        # to_keep=[i for i in data_vars if i not in cat_vars]

        # Our final data columns will be:
        # data_final=data[to_keep]
        # data_final.columns.values
		
        data1 = data.drop(columns=['id'])

        X = data1.loc[:, data1.columns != group_col]
        y = data1.loc[:, data1.columns == group_col]



        # '''Over-sampling using SMOTE'''
        # from imblearn.over_sampling import SMOTE

        # os = SMOTE(random_state=0)
        # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
        # columns = X_train.columns

        # os_data_X,os_data_y=os.fit_sample(X_train, y_train)
        # os_data_X = pd.DataFrame(data=os_data_X,columns=columns )
        # os_data_y= pd.DataFrame(data=os_data_y,columns=[group_col])

        # # we can Check the numbers of our data
        # with open(f_results,'a') as f:
            # f.write("length of oversampled data is "+str(len(os_data_X))+'\n')
            # f.write("Number of controls in oversampled data"+str(len(os_data_y[os_data_y[group_col]==0]))+'\n')
            # f.write("Number of patients "+str(len(os_data_y[os_data_y[group_col]==1]))+'\n')
            # f.write("Proportion of controls in oversampled data is "+str(len(os_data_y[os_data_y[group_col]==0])/len(os_data_X))+'\n')
            # f.write("Proportion of patients in oversampled data is "+str(len(os_data_y[os_data_y[group_col]==1])/len(os_data_X))+'\n')

        # # Now we have a perfect balanced data! You may have noticed that 
        # # I over-sampled only on the training data, this way none of the information in the test data 
        # # is being used to create synthetic observations, therefore, no 
        # # information will bleed from test data into the model training

        # '''Recursive Feature Elimination'''
        # data_final_vars=data1.columns.values.tolist()
        # os_data_X.to_csv("C:/Users/Jessica/Desktop/tmp.csv")
        # y=[group_col]
        # X=[i for i in data_final_vars if i not in y]

        # from sklearn.feature_selection import RFE

        logreg = LogisticRegression(solver='sag')#newton-cg, lbfgs, liblinear, sag, saga

        # rfe = RFE(logreg, 20)
        # rfe = rfe.fit(os_data_X, os_data_y.values.ravel())
				
        # cols = []
        # for val in X:
            # if rfe.support_[X.index(val)] == True:
                # cols.append(val)
        # with open(f_results,'a') as f:
            # f.write("\n Recursive Feature Eliminations:\n    Support: "+str(rfe.support_)+'\n')
            # f.write("\n    Columns: "+str(cols)+'\n')
        # X=os_data_X[cols]
        # y=os_data_y[group_col]
		
        # from statsmodels.formula.api import ols# For statistics, statsmodels =>5.0
        # y = np.array(os_data_y[group_col])
        # cols005 = []
        # for col in cols:
            # x = np.array(os_data_X[col])
            # data_tmp = pd.DataFrame({'x':x,col:y})
            # model = ols(col+" ~ x", data_tmp).fit()
            # if model.pvalues.x < 0.05:
                # cols005.append(col)
        # with open(f_results,'a') as f:
            # f.write("\n    Columns p<0.05: "+str(cols005)+'\n')
        # X=os_data_X[cols005]
		
        # Logistic Regression Model Fitting

        from sklearn.metrics import confusion_matrix
        from sklearn.metrics import classification_report

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
        try:
            logreg.fit(X_train, y_train)		
		
            # Predicting the test set results and calculating the accuracy

            y_pred = logreg.predict(X_test)
            with open(f_results,'a') as f:
                f.write("\nAccuracy of logistic regression classifier on test set: {:.2f}'".format(logreg.score(X_test, y_test))+'\n')
        except ValueError as e:
            print(e)

        # Accuracy of logistic regression classifier on test set: 0.74		
		
        # Confusion Matrix

        confusion_matrix = confusion_matrix(y_test, y_pred)
        with open(f_results,'a') as f:
            f.write('\nConfusion Matrix:\n')
            f.write(str(confusion_matrix)+'\n')

        # [[a b]
        # [c d]]
        # The result is telling us that we have a+d correct predictions 
        # and c+b incorrect predictions.		
		
        '''Compute precision, recall, F-measure and support

        To quote from Scikit Learn:
        The precision is the ratio tp / (tp + fp) where tp is the number of true positives and 
        fp the number of false positives. The precision is intuitively the ability of the classifier 
        to not label a sample as positive if it is negative.

        The recall is the ratio tp / (tp + fn) where tp is the number of true positives and fn the 
        number of false negatives. The recall is intuitively the ability of the classifier to find 
        all the positive samples.

        The F-beta score can be interpreted as a weighted harmonic mean of the precision and recall, 
        where an F-beta score reaches its best value at 1 and worst score at 0.

        The F-beta score weights the recall more than the precision by a factor of beta. beta = 1.0 
        means recall and precision are equally important.

        The support is the number of occurrences of each class in y_test'''

        with open(f_results,'a') as f:
            f.write('\nClassification Report:\n')
            f.write(classification_report(y_test, y_pred)+'\n')
        '''Interpretation: Of the entire test set, 74% of the promoted term deposit were the term 
        deposit that the customers liked. Of the entire test set, 74% of the customer’s preferred 
        term deposits that were promoted.'''
		
        # ROC Curve
        from sklearn.metrics import roc_auc_score
        from sklearn.metrics import roc_curve
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
        plt.savefig(Log_ROC)
        plt.show()
        print('Logistic Regression DONE')

        '''The receiver operating characteristic (ROC) curve is another 
        common tool used with binary classifiers. The dotted line 
        represents the ROC curve of a purely random classifier; a good 
        classifier stays as far away from that line as possible 
        (toward the top-left corner).'''
		
