# !/usr/bin/env python
# coding: utf-8
# last update: 2020-03-27

# script intends to do all the plots


import matplotlib.pyplot as plt

def plot_simple(vals, xlabel, ylabel, path_to_save_file):
    plt.plot(vals)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.savefig(path_to_save_file)

def plot_features(df): #written by Lynn Valeyry Verty, adapted by Alex Hanganu
	plt.figure(figsize=(20, 10))
	plt.pcolor(df, cmap = 'bwr')
	plt.yticks(np.arange(0.5, len(df.index), 1), df.index)
	plt.xticks(rotation=90)
	plt.xticks(np.arange(0.5, len(df.columns), 1), sorted(df.columns))
	plt.title('All Parameters', loc='center')
	plt.show()