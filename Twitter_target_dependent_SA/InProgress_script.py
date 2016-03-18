import pandas
from sklearn.feature_extraction.text import CountVectorizer
import re
from nltk import pos_tag
from nltk import word_tokenize
from nltk.corpus import stopwords
from sklearn.svm import LinearSVC
from pandas import crosstab
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_curve, classification_report


import os
os.environ['CLASSPATH'] = '/Users/gautamborgohain/stanford-postagger-full-2015-04-20/stanford-postagger.jar:/Users/gautamborgohain/stanford-ner-2015-04-20/stanford-ner.jar:/Users/gautamborgohain/stanford-parser-full-2015-04-20/stanford-parser.jar:/Users/gautamborgohain/stanford-parser-full-2015-04-20/stanford-parser-3.5.2-models.jar'
os.environ['STANFORD_MODELS'] = '/Users/gautamborgohain/stanford-postagger-full-2015-04-20/models:/Users/gautamborgohain/stanford-ner-2015-04-20/classifiers'



target = 'Sentiment_SVM'
# raw_data = pd.read_excel('/Users/gautamborgohain/Desktop/DATA/data_new.xlsx')


def regex_stuff(tweet):
    # Convert to lower case
    tweet = tweet.lower()
    # Convert www.* or https?://* to URL
    tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', ' ', tweet)
    # Convert @username to AT_USER
    tweet = re.sub('@smrt_singapore','AT_SMRT_SINGAPORE', tweet)
    tweet = re.sub('@[^\s]+', 'AT_USER', tweet)
    tweet = re.sub('@', ' ', tweet)
    # Remove additional white spaces
    tweet = re.sub('[\s]+', ' ', tweet)
    # Replace #word with word
    # tweet = re.sub(r'#([^\s]+)', r'\1', tweet)
    # trim
    tweet = tweet.rstrip()
    #tweet = tweet.strip('\'"')

    return tweet

def removeStopWords(tokens):
    stopwordsList = stopwords.words('english')
    stopwordsList.append('AT_USER')
    stopwordsList.append('URL')
    stopwordsList.append('at_user')
    stopwordsList.append('url')
    filtered_tokens = [word for word in tokens if word not in stopwordsList]
    return filtered_tokens


def removeBadTweets(tweetsdf):
    newDF = pandas.DataFrame(columns=tweetsdf.columns)
    baddatacount = 1
    for i in range(1, len(tweetsdf)):
        tweet = tweetsdf.get_value(i, 'Tweet')
        tweet = regex_stuff(tweet)  # remove using the regex function
        tweet = tweet.encode('ascii', 'ignore').decode('ascii')  # remove the weird characters
        if re.search(r'i\'m at [a-z ]* mrt ', tweet) or tweet.startswith('i\'m at'):
            baddatacount += 1
        else:
            tweetsdf = tweetsdf.set_value(i, 'Tweet', tweet)
            newDF = newDF.append(tweetsdf[i:i + 1])
            # print(tweetsdf.ix[i])

    print("Completed, Bad tweets count = ", baddatacount)
    print(newDF.head())

    return newDF



def getPOStagfeatures(frame):
    """

    :rtype: pandas dataframe
    """
    tagsoftweet = []
    reg = re.compile(r'at_user|rt|,')
    count = 1
    for tweet in frame['Tweet']:
        tweet = re.sub(reg, '', tweet)  # stripping it off stuff
        print('Tagging tweet', count)
        postaggedtweet = pos_tag(word_tokenize(tweet))  # this one is pos atgged..list inside list : token[1] for tag
        tags = []
        for token in postaggedtweet:
            tags.append(token[1])
        tagsoftweet.append(' '.join(tags))
        count += 1

    vectorizer = CountVectorizer(min_df=1)
    tweetmatrix = vectorizer.fit_transform(tagsoftweet).toarray()
    columns = vectorizer.get_feature_names()
    columns = [word.upper() for word in columns]  # uppercasing to avoid conflict of in and other words
    df = pandas.DataFrame(data=tweetmatrix, columns=columns)
    print('Completed POS tagging')
    return df


def getSubjectvityfeatures(frame):
    """

    :rtype: pandas dataframe
    """
    lexicon = pandas.read_csv('/Users/gautamborgohain/PycharmProjects/SentimentAnalyzer/subjectivity.csv')
    tweet_tags = []
    count_tweet = 1
    for tweet in frame['Tweet']:
        tweet = cleantweet(tweet)
        typeList = []
        priorpolarityList = []
        count_word = 0  # this counter is for the pos tagging. traces the words in the tweet so that the idrect index of the tag can be accesses
        print('Performing subjectivity analysis of Tweet ', count_tweet)
        count_tweet += 1
        for word in word_tokenize(tweet):
            result = lexicon[lexicon.word1 == word]
            if len(result) != 0:  # word is there in the lexicon
                if len(result) == 1:  # this case is handling the ones where the there is only one record of the word
                    typeList.append(result.iloc[0][0])
                    priorpolarityList.append(result.iloc[0][5])
                if len(result) > 1:  # this is if there are more than one instances of the owrd in the lexicon then the pos tag is checked
                    print('Have to tag POS, Hold On!')
                    poslist = pos_tag(word_tokenize(tweet))
                    postag = poslist[count_word][1]

                    if postag in ['NN', 'NNP', 'NNS',
                                  'NNPS']:  # make the POS tags to the format used by the MPQA lexicon
                        postag = 'noun'
                    elif postag in ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']:
                        postag = 'verb'
                    elif postag in ['RB', 'RBR', 'RBS']:
                        postag = 'adverb'
                    elif postag in ['JJ', 'JJR', 'JJS']:
                        postag = 'adj'

                    second_result = result[result.pos1 == postag]
                    if len(second_result) != 0:  # this is to check if the pos tag that the word was tagged is there in the lexicon for that word
                        typeList.append(second_result.iloc[0][0])
                        priorpolarityList.append(second_result.iloc[0][5])

            count_word += 1

        tweet_tags.append(' '.join(typeList) + ' ' + ' '.join(priorpolarityList))

    isListEmpty = True
    for data in tweet_tags:
        if (data != " "):
            isListEmpty = False

    if(not isListEmpty):
        vectorizer = CountVectorizer(min_df=1)
        tweetmatrix = vectorizer.fit_transform(tweet_tags).toarray()
        columns = vectorizer.get_feature_names()
        columns = [word.upper() for word in columns]  # uppercasing to avoid conflict of positive negative
        df = pandas.DataFrame(data=tweetmatrix, columns=columns)
        print('Completed Subjective Analysis')
        return df

    else:
         return "No Subjectivity data found"

def cleantweet(tweet):
    tweet = re.sub('url|at_user|rt|\.', '', tweet)  ## removing these from the tweets
    return tweet


def target_features(frame):
    tweet_target_features = []
    for tweet in frame['Tweet']:
        tweet = cleantweet(tweet)
        tags = get_hastags(tweet)
        keywords = ['SMRT', 'mrt', 'MRT', 'smrt', 'Singapore_MRT',"AT_SMRT_SINGAPORE"]
        tokens = word_tokenize(tweet)
        tokens = removeStopWords(tokens)
        targets_feature = []
        for keyword in keywords:
            if keyword in tags:  ## If i replace elif it if - Thing to note here is that the words which are hash tags will be counted twice here one from tokens and one from hashtags
                ind = tags.index(keyword)
                tag = tags[ind]
                feature = tag + '_hash'
                targets_feature.append(feature)
            elif keyword in tokens:
                ind = tokens.index(keyword)
                tag = tokens[ind]  # this is the target
                adjectives = getAdjectves(tweet)  # This will get all the adjectives, not just one
                features = []
                for adjective in adjectives:
                    adjective = re.sub('-', '_',
                                       adjective)  # this to take care of probelesm for - like east-west/ north-south.. now east_west
                    features.append(tag + '_' + adjective)
                feature = ' '.join(features)
                targets_feature.append(feature)

        tweet_target_features.append(' '.join(targets_feature))
    print('modified',tweet_target_features)

    isListEmpty = True
    for data in tweet_target_features:
        if (data != ''):
            isListEmpty = False

    if(not isListEmpty):
        vectorizer = CountVectorizer(min_df=1)
        tweetmatrix = vectorizer.fit_transform(tweet_target_features).toarray()
        columns = vectorizer.get_feature_names()
        print(columns)
        columns = [word.upper() for word in columns]  # uppercasing to avoid conflict of positive negative
        df = pandas.DataFrame(data=tweetmatrix, columns=columns)
        return df
    else:
         return "No Target dependant data found"

def get_hastags(tweet):
    hash_tags = re.findall('#([^ ]*)', tweet)
    return hash_tags


def getAdjectves(tweet):# verify with the lexicon
    postags = ['JJ', 'JJR', 'JJS']
    tokens = []
    pos_tags = pos_tag(word_tokenize(tweet))
    pos_tags_1 = []
    words_1 = []
    for pos in pos_tags:
        pos_tags_1.append(pos[1])

    for pos in pos_tags:
        words_1.append(pos[0])

    for postag in postags:
        if postag in pos_tags_1:
            inds = all_indices(postag, pos_tags_1)
            for ind in inds:
                tokens.append(words_1[ind])

    return tokens


def all_indices(value, qlist):
    indices = []
    idx = -1
    while True:
        try:
            idx = qlist.index(value, idx + 1)
            indices.append(idx)
        except ValueError:
            break
    return indices


def get_hashTagSentiments(frame):
    tweets = []
    for tweet in frame['Tweet']:
        tweet = cleantweet(tweet)
        tags = get_hastags(tweet)
        tweets.append(" ".join(tags))

    frame.loc[:,'Tweet'] = tweets
    df = getSubjectvityfeatures(frame)
    if(isinstance(df,pandas.DataFrame)):
        columns = df.columns
        new_columns = []
        for column in columns:
            new_columns.append('TAG_' + column)
        df.columns = new_columns
        return df
    else:
        return "Subjectivity on hash tags not found"



# This will be the main processor where the features in the data frame are going to be created.
def getCountVector(frame, getSWM=True, getSubj=True, getPOSTags=True, getTargetFeats=True, getHashTagFeats=True):
    vectorizer = CountVectorizer(min_df=1)
    tweets = []

    # this part is just to get rid of the emoticons and stuff making it impossible to write to csv
    try:
        # UCS-4
        highpoints = re.compile(u'[U00010000-U0010ffff]')
    except re.error:
        # UCS-2
        highpoints = re.compile(u'[uD800-uDBFF][uDC00-uDFFF]')
    for tweet in frame['Tweet']:
        tweet = highpoints.sub('', tweet)
        tweet = tweet.encode('ascii', 'ignore').decode('ascii')
        tweet = cleantweet(tweet)  # cleaning
        tweet = ' '.join(removeStopWords(word_tokenize(tweet)))
        tweets.append(tweet)

    documentmatrix = vectorizer.fit_transform(tweets).toarray()
    columns = vectorizer.get_feature_names()
    df = pandas.DataFrame(data=documentmatrix, columns=columns)



    # Negations

    # Emoticon

    # Punctuation

    # Elongated words

    # URL ??


    df = df.join(frame[target])
    return df



#
# raw_data = pandas.read_excel('/Users/gautamborgohain/Desktop/SA Files/data_toLabel.xlsx')
#
#
# new_df = removeBadTweets(raw_data)
# sub = new_df
# processed = getCountVector(sub)
#
# posdf = getPOStagfeatures(sub)
# processed = processed.join(posdf)
#
# subjframe = getSubjectvityfeatures(sub)
# if(isinstance(subjframe,pandas.DataFrame)):
#     processed = processed.join(subjframe)
# else:
#     print(subjframe)
#
# targetframe = target_features(sub)
# if(isinstance(targetframe,pandas.DataFrame)):
#     processed = processed.join(targetframe)
# else:
#     print(targetframe)
#
#
# hashframe = get_hashTagSentiments(sub)
# if(isinstance(hashframe,pandas.DataFrame)):
#     processed = processed.join(hashframe)
# else:
#     print(hashframe)

# processed['Sentiment_SVM'].fillna(0,inplace=True)
#
# classifier = LinearSVC()
# training_set = processed.sample(frac=0.6, random_state=1)
# testing_set = processed.loc[~processed.index.isin(training_set.index)]
#
# classifier.fit(training_set, training_set[target])  # cross_validation.cross_val_score(classifier,training_set,training_set[config.get['target']],scoring = 'f1')
# predictions_training = classifier.predict(training_set)
# training_set['Predictions'] = predictions_training
# # training_set.join(predictions_training,'Predictions')
# training_true = training_set[target]
# predictions_testing = classifier.predict(testing_set)
# testing_set['Predictions'] = predictions_testing
# # testing_set.join(predictions_testing,'Predictions')
# testing_true = testing_set[target]
#
# accuracy_training = accuracy_score(training_true, predictions_training)
# accuracy_testing = accuracy_score(testing_true, predictions_testing)
#
# print(accuracy_training,"----",accuracy_testing)
#
# crosstab(training_set[target], training_set['Predictions'])
#
# crosstab(testing_set[target], testing_set['Predictions'])

