# coding: utf-8

import pandas as pd
import numpy as np
import pickle
import re
from nltk.stem import WordNetLemmatizer

lemmatizer = WordNetLemmatizer()


# Hidden Markov Model
class LabelParser():
    def __init__(self, objects, augmentation):
        self.objects = objects
        self.A = None
        self.B = None
        self.Pi = None
        self.Q_count = None
        self.O_count = None
        self.O = None
        self.Q = None
        self.show_path = False
        self.aug = augmentation
        self.build_model()

    def build_model(self):
        # Retrieve states (Q) and observations  (O) and their counts.
        self.Q = sorted(list(set(sum([x.tags for x in self.objects], []))))
        self.O = sorted(list(set(sum([x.split for x in self.objects], []))))
        # Tag sequence as presented to the model
        self.Q_seq = [x.tags for x in self.objects]

        # Word sequence as presented to the model
        self.W_seq = [x.split for x in self.objects]

        # Initialize empty transition matrix A and emission matrix B
        self.A = pd.DataFrame(columns=self.Q, index=self.Q).fillna(0.)
        self.B = pd.DataFrame(columns=self.Q, index=self.O).fillna(0.)
        self.Pi = pd.DataFrame(columns=['P'], index=self.Q).fillna(0.)

        ### Fill Transition Matrix A ###
        # Count the transitions from the current to the next in B_mat and divide by the total.
        for sub in self.Q_seq:
            x = iter(sub)
            count = 0
            next(x)
            while (True):
                try:
                    current = sub[count]
                    count += 1
                    trans = next(x)
                    self.A[trans][current] += 1
                except:
                    break

        self.A = self.A.apply(normalize, axis=0)

        # for q in self.Q:
        #    self.A[q] = self.A[q] / float(sum(self.A[q]))

        self.A = self.A.fillna(0.)
        self.A['VOV']['VOV'] = 0.
        self.A['misc-VOS']['ANNO'] = 0.
        self.A['ANNO']['misc-VOS'] = 0.
        self.A['ADAN']['ADAN'] = 0.
        self.A['ADVOS']['ADVOS'] = 0.
        if ('ADNA' in self.A.index):
            self.A['ADNA']['ADNA'] = 0.
        if ('ADDES' in self.A.index):
            self.A['ADDES']['ADDES'] = 0.

        ### Fill Emission Matrix B ###
        # Count all occurrences
        # self.C = pd.DataFrame(columns=self.B.columns, index=self.O).fillna(0.)

        for q, w in zip(self.Q_seq, self.W_seq):
            for qs, ws in zip(q, w):
                self.B[qs][ws] += 1
        self.B = self.B.apply(normalize, axis=1)

        ### Start Probability Matrix Pi ###
        for q in self.Q_seq:
            self.Pi['P'][q[0]] += 1

        # for q in self.Q:
        #    self.Pi['P'][q] = 1./len(self.Q)
        # self.Pi['P'] = self.Pi['P'] / float(len(self.Q))

        self.Pi['P'] = self.Pi['P'] / float(sum(self.Pi['P']))

        # Room for constraints
        self.Pi.loc['VOO'] = 0
        self.Pi.loc['misc-VOS'] = 0
        self.Pi.loc['INTVOS'] = 0
        self.Pi.loc['INTAN'] = 0

        # Initialize Viterbi parameters

        self.transProb = self.A.to_numpy()
        initProbs = self.Pi['P'].to_numpy()
        #  transform into list of lists
        self.initialProb = np.asarray([[el] for el in initProbs])
        self.obsProb = self.B
        self.tags = self.A.columns
        self.N = len(self.Q)

    def _obs(self, obs):
        shape = len(self.obsProb.columns)
        # return self.obsProb.ix[obs].as_matrix().reshape(shape,1)
        return self.obsProb.loc[obs].to_numpy().reshape(shape, 1)

    def _viterbi(self, obs):
        trellis = np.zeros((self.N, len(obs)), dtype='float64')
        backpt = np.ones((self.N, len(obs)), 'int32') * -1
        try:
            trellis[:, 0] = np.squeeze(self.initialProb * self._obs(obs[0]))
        except:
            trellis[:, 0] = np.squeeze(self.initialProb * np.ones((len(self.initialProb), 1)))

        for t in range(1, len(obs)):
            try:
                T = (trellis[:, t - 1, None].dot(self._obs(obs[t]).T) * self.transProb).max(0)
            except:
                T = (trellis[:, t - 1, None].dot(np.ones((len(self.initialProb), 1)).T) * self.transProb).max(0)
            if not np.any(T):
                T = (trellis[:, t - 1, None].dot(np.ones((len(self.initialProb), 1)).T) * self.transProb).max(0)

            trellis[:, t] = T
            backpt[:, t] = (np.tile(trellis[:, t - 1, None], [1, self.N]) * self.transProb).argmax(0)

        tokens = [trellis[:, -1].argmax()]
        for i in range(len(obs) - 1, 0, -1):
            tokens.append(backpt[tokens[-1], i])
        return [self.tags[i] for i in tokens[::-1]]

    def parse_label(self, label):
        predicted_tags = self._viterbi(split_label(label))
        predicted_style = vote_style(predicted_tags)
        result = ParsedLabel(label, predicted_tags)
        # print('label', label, 'tags', predicted_tags, 'style', predicted_style)
        # print('business objects', result.bos, "actions", result.actions)
        return result


class ParsedLabel():
    def __init__(self, label, tags):
        self.label = label
        self.splitlabel = split_label(label)
        self.tags = tags
        self.bos = self.findObjects(self.tags)
        self.actions = self.findActions(self.tags)

    def findObjects(self, tags):
        return [self.splitlabel[i] for i, tag in enumerate(self.tags) if tag in OBJECT]

    def findActions(self, tags):
        return [self.splitlabel[i] for i, tag in enumerate(self.tags) if tag in ACTION]


class AugmentObject():

    def __init__(self, item):
        self.label = item.Label
        self.style = item.Style
        self.split = item.Split
        self.tags = item.Tags.split()


class DataObject():

    def __init__(self, item):
        self.label = item.Label
        self.style = item.Style
        self.action = item.Action
        self.bobject = item['Business Object']
        self.split, self.tags = parse_tags(item)


def parse_augment_list(data):
    result = []
    for index, row in data.iterrows():
        result.append(AugmentObject(row))
    return result


def normalize(x):
    return x / sum(x)


def initialize_augmentation_matrix(columns):
    return pd.DataFrame(columns=columns)


def fill_augmentation_matrix(dataObjects, columns):
    augmentation_matrix = initialize_augmentation_matrix(columns)

    for item in dataObjects:
        row = pd.DataFrame(columns=columns, index=[item.label]).fillna(0.)
        for tag in item.tags:
            row[tag] = row[tag] + 1
        augmentation_matrix = augmentation_matrix.append(row)

    augmentation_matrix = augmentation_matrix.groupby(augmentation_matrix.index).sum()

    return augmentation_matrix


def parse_tags(item):
    w, t = split_tags(item.Tags)
    return w, t


def split_tags(tags):
    w = []
    t = []
    tagsets = tags.split(',')
    tagsets = tagsets[0:-1]

    for tagset in tagsets:
        word = tagset.split('<>')[0].strip(' ')
        tag = tagset.split('<>')[1].strip(' ')
        w.append(word)
        t.append(tag)

    return w, t


def data_to_object(dataframe):
    objects = []
    for index, row in dataframe.iterrows():
        objects.append(DataObject(row))
    return objects


def action_object(samples, model):
    label_list = []
    true_list = []
    pred_list = []

    for obj in samples:
        pred = model.viterbi(obj.split)
        word = obj.split
        true = obj.tags

        label_list.append(obj.label)
        true_list.append(true)
        pred_list.append(pred)

        # print str('Label: ' + str(word) + '\npredicted: ' + str(pred) +\
        # '\nactual: ' + str(true) + '\nType: ' + str(obj.style) + '\n\n')
    return label_list, true_list, pred_list


def tag_style(tag):
    if tag in VOS:
        return 'VOS'
    elif tag in NA:
        return 'NA'
    elif tag in DES:
        return 'DES'
    elif tag in AN:
        return 'AN'
    else:
        return ''


def vote_style(tags):
    styles = {'VOS': 0, 'AN': 0, 'NA': 0, 'DES': 0}
    for tag in tags:
        try:
            style = tag_style(tag)
            styles[style] += 1
        except:
            pass
    return max(styles, key=styles.get)


# In[ ]:

ACTION = 'VOV VOIV VOV-E ANV ANIV ANINGV OF_VERB-AN NAV OF_VERB-NA DESV OF_VERB_DES'
OBJECT = 'VOO VOIO misc-VOS ANO ANNO ANIO ANINGO ANOO misc-AN NAO misc-NA DESO misc-DES OF_VERB-VOS OF-VOS'.split()
VOS = ['MODIFIERVOS', '3RDSPVOS', 'VOO', 'ADVOS', 'AND-VOS', 'C-VOS', 'VOV', 'misc-VOS', 'AD_VOS', 'MISC_VOS', 'OF-VOS',
       'VOIV', 'VOIO', 'OF_VERB-VOS', 'VOV-E']
AN = ['MODIFIERAN', '3RDSPAN', 'misc-AN', 'ADAN', 'AND-AN', 'OF-AN', 'C-AN', 'AN_OF', 'AD_AN', 'ANO', 'ANV', 'ANNO',
      'ANNV', 'ANIO', 'ANIV', 'ANINGO', 'ANOV', 'ANINGV', 'ANOO', 'OF_VERB-AN']
NA = ['MODIFIERNA', '3RDSPNA', 'NAO', 'NAV', 'OF_NA', 'AND-NA', 'AD_NA', 'C-NA', 'misc-NA', 'OF-NA', 'ADNA',
      'OF_VERB-NA', ]
DES = ['MODIFIERDES', '3RDSPDES', 'OF-DES', 'misc-DES', 'AD_DES', 'AND-DES', 'ADDES', 'C-DES', 'DESV', 'DESO',
       'OF_VERB-DES', 'DESV-P']
STYLES = ['AN', 'NA', 'VOS', 'DES']

PARSER_PATH = "./labelparser/trainedparser.p"


def train_parser(parserPath):
    full_set = pd.read_csv('labelparser/CSV/COMPLETE_V19.csv', sep=';', keep_default_na=False)
    AUG_set = data_to_object(pd.read_csv('labelparser/CSV/aug_list.csv', sep=';', keep_default_na=False))

    train_objects = data_to_object(full_set)
    parser = LabelParser(train_objects + AUG_set, None)
    pickle.dump(parser, open(parserPath, "wb"))
    return parser


def load_trained_parser(path):
    return pickle.load(open(path, "rb"))


def load_default_parser():
    return load_trained_parser(PARSER_PATH)


def split_label(label):
    # result = label.replace('_', ' ', regex=False)
    result = re.split('[^a-zA-Z]', label)
    result = [w.lower() for w in result]
    return result


def split_and_lemmatize_label(label):
    words = split_label(label)
    lemmas = [lemmatize_word(w) for w in words]
    return lemmas


def lemmatize_word(word):
    lemma = lemmatizer.lemmatize(word, pos='v')
    # lemma = lemmatizer.lemmatize(lemma, pos='n')
    return lemma


def differ_by_one_word(label1, label2):
    (diff1, diff2) = _get_list_differences(label1, label2)
    return len(diff1) == 1 and len(diff2) == 1


def differ_by_negation(label1, label2):
    (diff1, diff2) = _get_list_differences(label1, label2)
    return diff1 == ["not"] or diff2 == ["not"]


def _get_list_differences(label1, label2):
    list1 = split_and_lemmatize_label(label1)
    list2 = split_and_lemmatize_label(label2)
    diff1 = [w for w in list1 if not w in list2]
    diff2 = [w for w in list2 if not w in list1]
    return diff1, diff2


def get_differences(label1, label2):
    list1 = split_and_lemmatize_label(label1)
    list2 = split_and_lemmatize_label(label2)
    (diff1, diff2) = _get_list_differences(label1, label2)
    if len(diff1) == 1 and len(diff2) == 1:
        return "".join(diff1), "".join(diff2)
    return "", ""
