import pandas as pd
import re
import os
from collections import Counter
import pickle
import tensorflow as tf
import numpy as np


def accuracy(labels, predictions):
    return 100*(np.sum(np.argmax(labels,1) == np.argmax(predictions,1)) / predictions.shape[0])

def getFileContents(nameOfFileToOpen):
    dataFile = open(nameOfFileToOpen)
    contents = ""
    try:
        for dataLine in dataFile:
            contents += dataLine
    except:
        contents = ''
    finally:
        dataFile.close()
    return contents

# df1 = pd.read_csv('/Users/gautamborgohain/CI Submission/Data/SEmEval_train.tsv', sep = '\t',header = None)
# df1.columns = ['Date','ID','Sentiment','Tweet']
# df2 = pd.read_excel('/Users/gautamborgohain/CI Submission/Data/SemEval Test.xlsx')
# df2.drop('Unnamed: 4',1,inplace = True)
# df2.columns = ['Date','ID','Sentiment','Tweet']
# df1 = pd.concat([df1,df2],axis = 0,)
# df1 = df1[df1.Tweet != 'Not Available']
df1 = pd.read_csv('/Users/gautamborgohain/PycharmProjects/MOSCATO/semeval_combined.csv', sep = '\t')

'''
Load the word embeddings dictionary
'''
data_dict = pickle.load(open("/Users/gautamborgohain/Desktop/semeval_embeds_DeepNL.pck",'rb'))

'''
Load the urban dictonary similar words data
'''
udDict = pickle.load(open("/Users/gautamborgohain/Desktop/ud_dict.pck",'rb'))



# Get the word frequency in the dataset
words = [word for tweet in df1.Tweet for word in tweet.split()]
c = Counter(words)
freq_words = c.most_common()[:1000]

# Look up the words in urban dictionary to confirm as the seed set
seed_dict = [word for word in freq_words  if udDict.get(word[0])]


'''
Bing Lu Lexicon
'''
HL_posLoc = '/Users/gautamborgohain/PycharmProjects/DT_Labs/PLayground/Gautam_Borg/HuLiuLexicon/positive-words.txt'
HL_negLoc = '/Users/gautamborgohain/PycharmProjects/DT_Labs/PLayground/Gautam_Borg/HuLiuLexicon/negative-words.txt'

poshand = open(HL_posLoc)
neghand = open(HL_negLoc)
poslist = [re.sub(r'\n','',line) for line in poshand]
neglist = [re.sub(r'\n','',line) for line in neghand]

'''
MPQA lexicon (Wilson et al)
'''
subjLexLoc = '/Users/gautamborgohain/PycharmProjects/Twitter_target_dependent_SA/subjectivity.csv'
subjLex = pd.read_csv(subjLexLoc)
neg_subj_list = []
pos_subj_list = []
for index,row in subjLex.iterrows():
    if row.priorpolarity == 'negative':
        neg_subj_list.append(row.word1)
    elif row.priorpolarity == 'positive':
        pos_subj_list.append(row.word1)


# pos_seeds = []
# neg_seeds = []
# neu_seeds = []
# for seed in seed_dict:
#     if seed[0] in poslist or seed[0] in pos_subj_list:
#         pos_seeds.append(seed[0])
#     elif seed[0] in neglist or seed[0] in neg_subj_list:
#         neg_seeds.append(seed[0])
#     else:
#         neu_seeds.append(seed[0])


'''
From the classified words, manually do some labelling and then load back
'''
pos_seeds = []
neg_seeds = []
neu_seeds = []

f = open('/Users/gautamborgohain/Desktop/pos_seeds.txt', mode = 'r')
for word in f.readlines():
    pos_seeds.append(re.sub('\n','',word))
f.close()
f = open('/Users/gautamborgohain/Desktop/neg_seeds.txt', mode = 'r')
for word in f.readlines():
    neg_seeds.append(re.sub('\n','',word))
f.close()
f = open('/Users/gautamborgohain/Desktop/neu_seeds.txt', mode = 'r')
for word in f.readlines():
    neu_seeds.append(re.sub('\n','',word))
f.close()


# Create a list with the expansion of this seed sets

expnd_pos_words = [expansion for word in pos_seeds for expansion in udDict.get(word) if data_dict.get(expansion)]
expnd_neg_words = [expansion for word in neg_seeds for expansion in udDict.get(word) if data_dict.get(expansion)]
expnd_neu_words = [expansion for word in neu_seeds for expansion in udDict.get(word) if data_dict.get(expansion)]

# There are too many neutral terms, so picking just 900 of them for now.. originally around 5900, the classification is badely skewed due to this
expnd_neu_words = expnd_neu_words[:900]

#Dictionary with the words and their polarities
combined_pol_dict = dict()
for word in expnd_pos_words:
    combined_pol_dict[word] = 1
for word in expnd_neg_words:
    combined_pol_dict[word] = -1
for word in expnd_neu_words:
    combined_pol_dict[word] = 0

#The datasets that will be sent for training and also the full vocabulary
all_X = [embd for word,embd in data_dict.items()]
X = [data_dict[word] for word in combined_pol_dict]
Y = [[1 if y == 1 else 0,1 if y == -1 else 0,1 if y == 0 else 0] for word,y in combined_pol_dict.items()]

'''
Tensor flow softmax
'''

size = 100 # Embedding size
graph = tf.Graph()
with graph.as_default():
    x = tf.placeholder(tf.float32, [None,size])
    all_words = tf.constant(all_X)
    W = tf.Variable(tf.zeros([size, 3]))
    b = tf.Variable(tf.zeros([3]))
    logits = tf.matmul(x, W) + b
    y_ = tf.placeholder(tf.float32, [None, 3])
    print_logits = tf.Print(logits,[logits])
    loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits,y_))
    optimizer = tf.train.AdagradOptimizer(0.5).minimize(loss)
    training_predictions = tf.nn.softmax(logits)
    all_predictions = tf.nn.softmax(tf.matmul(all_words,W) + b)


iters = 401

with tf.Session(graph = graph) as session:
    tf.initialize_all_variables().run()
    for step in range(iters):
        feed_dict = {x : X, y_ : Y}
        l,_,tr_predictions,all_preds = session.run([loss,optimizer,training_predictions,all_predictions],feed_dict=feed_dict)
        if step %100 == 0:
            print('Loss at Step ', step, ' : ', l)
            print('Training Accuracy : ', accuracy(Y,tr_predictions))

#All the words list
data_dict_words = [word for word in data_dict]

# Dictionary for words and their predictions
result_dict = dict()

for word,probs in zip(data_dict_words,all_preds):
    result_dict[word]=probs


'''
Final lexicon

method A:
Check pos and neg classes for value greater than 0.5 -  This is whats written in their paper, however, what about the neutral ones?

'''

final_pos_lexicon = dict()
final_neg_lexicon = dict()
for word,probs in result_dict.items():
    for index,prob in zip(range(3),probs):
        if prob>=0.5:
            if index == 0:
                final_pos_lexicon[word] = prob
            elif index == 1:
                final_neg_lexicon[word] = prob

print(len(final_pos_lexicon), len(final_neg_lexicon))

final_pos_lexicon = sorted(final_pos_lexicon.items(), key=lambda item: (item[1], item[0]),reverse=True)
final_neg_lexicon = sorted(final_neg_lexicon.items(), key=lambda item: (item[1], item[0]),reverse=True)


f = open('/Users/gautamborgohain/Desktop/pos_lexicon.txt', mode = 'x')
for word,prob in final_pos_lexicon:
    f.writelines(word + ' ' + str(prob) + '\n')
f.close()
f = open('/Users/gautamborgohain/Desktop/neg_lexicon.txt', mode = 'x')
for word,prob in final_neg_lexicon:
    f.writelines(word + ' ' + str(prob) + '\n')
f.close()