# coding: utf-8
from __future__ import print_function
import os
import math
import gensim
from gensim.models import word2vec
import sys
from itertools import permutations as P
import glob 
import pickle as pkl
if __name__ == '__main__':
  if '--train' in sys.argv:
    fname = sys.argv[1]
    print(fname)
    corpus = sum([open(name).read().split() for name in glob.glob("%s/*wakati"%fname)], [])
    print(corpus[:10])
    print("dumping tmp...")
    open('/tmp/w2v.tmp', 'w').write( ' '.join(corpus) )
    data = word2vec.Text8Corpus('/tmp/w2v.tmp') 
    print("calculating w2v...")
    model = word2vec.Word2Vec(data, size=256, window=5, min_count=1, workers=4)
    model.save(fname + '.w2v')

    out=model.most_similar(positive=['ゾンビ'])
    for x in out:
      print(x[0],x[1])

  if '--vectrize' in sys.argv:
    fname = sys.argv[1]
    print(fname)
    vocs = set(sum([open(name).read().split() for name in glob.glob("%s/*wakati"%fname)], []))
    #print(vocs)
    model = word2vec.Word2Vec.load(fname + '.w2v')
    word_vec = {}
    for word in vocs:
      word_vec[word] = list(model[word])
      print(word, len(list(model[word])))
    open(fname +'.pkl', 'wb').write( pkl.dumps(word_vec) )
  if '--perm' in sys.argv: 
    fname = sys.argv[1]
    print(fname)
    model = word2vec.Word2Vec.load(fname)
    terms = filter(lambda x:x!='', open('./sample/dataset.kancolle.dat').read().split('\n'))
    t_tw = {}
    for t in terms:
        #print t
        pass
    for ps in P(terms, 2):
        ps_dec = map(lambda x:x.decode('utf-8'), list(ps))
        try:
            model.similarity(ps_dec[0], ps_dec[1])
            if t_tw.get(ps[0]) == None:
                t_tw[ps[0]] = []
            t_tw[ps[0]].append( [ps[1], \
                int( model.similarity(ps_dec[0], ps_dec[1]) * 10000)] )
            t_tw[ps[0]].sort(key=lambda x:x[1]*-1)
        except KeyError as e:
            pass

    for t, tw in t_tw.items():
        """
        print t, ' '.join( \
                map(lambda x:':'.join(map(str, \
                    [x[0], x[1], (x[1]/9000. - 1)*100])), tw[:10]) )
        """
        pass
  if '--chord' in sys.argv:
    allflare = []
    import json
    for t, tw in t_tw.items():
      t = t
      shadow = []
      for i, a_tw in enumerate(tw):
          if i > 10: break
          inner_t = a_tw[0]
          inner_w = (a_tw[1]/9000. - 1)*100
          #print a_tw, inner_w
          if inner_w <= 0.: break
          shadow.append( [inner_t, inner_w] )
      allweight = sum(map(lambda x:x[1], shadow))
      flare = {}
      flare['name'] = t
      flare['size'] = allweight
      flare['imports'] = map(lambda x:x[0], shadow)
      allflare.append(flare)
    print(json.dumps(allflare) )

