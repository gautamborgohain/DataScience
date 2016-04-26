from vaderSentiment.vaderSentiment import sentiment as vaderS
from sklearn.metrics import accuracy_score,f1_score,classification_report
import pandas as pd
import numpy as np


dataLoc = '/Users/gautamborgohain/Desktop/Tweets_labeled_325.xlsx'
data_unlab = pd.read_excel(dataLoc)
negs = data_unlab[data_unlab.Sentiment_2 == -1]
poss = data_unlab[data_unlab.Sentiment_2 == 1]
neuts = data_unlab[data_unlab.Sentiment_2 == 0]

frames = [neuts.sample(1200),poss,negs.sample(700)]
newdf = pd.concat(frames)
newdf.index = np.arange(len(newdf))# Need to reindex to join properly

X = newdf.Tweet
y = newdf.Sentiment_2

predicitons= []

for tweet in X:
    tweet = tweet.encode('ascii','ignore')
    predicitons.append(vaderS(tweet))

result = []
for pred in predicitons:
    prediction = 0
    pos = pred.get('pos')
    neg = pred.get('neg')
    neu = pred.get('neu')
    if(pos>neg and  pos> neu):
        prediction = 1
    elif(neg>pos and neg > neu):
        prediction = -1
    result.append(prediction)


df = pd.DataFrame()
df['Preds'] = result
df['True'] = y

df.to_csv('/Users/gautamborgohain/Desktop/vader.csv')

print(accuracy_score(y,result))
print(f1_score(y,result))
print(classification_report(y,result))