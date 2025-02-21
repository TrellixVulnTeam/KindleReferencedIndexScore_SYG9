# coding: utf-8
import time
import math
import sys
import argparse
import pickle as pickle
import copy
import os
import codecs

import numpy as np
from chainer import cuda, Variable, FunctionSet, optimizers
import chainer.functions as F
from DeepRNN import MoreDeepRNN
make_initial_state = MoreDeepRNN.make_initial_state
import json
import random

def load_data(args):
    vocab = {}
    print('%s/%s'%(args.data_dir,args.json))
    words = ''
    line = ''
    raw = open('%s/%s' %(args.data_dir, args.json), 'r').read()
    obj = json.loads(raw)
    words = obj['contents']
    dataset = np.ndarray((len(words),), dtype=np.int32)
    dataset = np.ndarray((len(words),2, ), dtype=np.int32)
    for i, word in enumerate(words):
        if word not in vocab:
            vocab[word] = len(vocab)
        # optional-dataset
        #dataset[i] = vocab[word]
        #print(dataset[i])
        dataset[i] = np.array([vocab[word], int(random.random()*10)])
    print('corpus length:', len(words))
    print('vocab size:', len(vocab))
    return dataset, words, vocab

# arguments
parser = argparse.ArgumentParser()
parser.add_argument('--data_dir',                   type=str,   default='data/tinyshakespeare')
parser.add_argument('--checkpoint_dir',             type=str,   default='')
parser.add_argument('--json',                       type=str,   default='1.json')
parser.add_argument('--gpu',                        type=int,   default=-1)
parser.add_argument('--rnn_size',                   type=int,   default=768)
parser.add_argument('--learning_rate',              type=float, default=2e-3)
parser.add_argument('--learning_rate_decay',        type=float, default=0.97)
parser.add_argument('--learning_rate_decay_after',  type=int,   default=10)
parser.add_argument('--decay_rate',                 type=float, default=0.95)
parser.add_argument('--dropout',                    type=float, default=0.0)
parser.add_argument('--seq_length',                 type=int,   default=50)
parser.add_argument('--batchsize',                  type=int,   default=50)
parser.add_argument('--epochs',                     type=int,   default=50)
parser.add_argument('--grad_clip',                  type=int,   default=5)
parser.add_argument('--init_from',                  type=str,   default='')

args = parser.parse_args()

if args.checkpoint_dir == '':
    args.checkpoint_dir = args.data_dir
if not os.path.exists(args.checkpoint_dir):
    os.mkdir(args.checkpoint_dir)

n_epochs    = args.epochs
n_units     = args.rnn_size
batchsize   = args.batchsize
bprop_len   = args.seq_length
grad_clip   = args.grad_clip

train_data, words, vocab = load_data(args)
pickle.dump(vocab, open('%s/%s.vocab.bin'%(args.data_dir, args.json), 'wb'))
filename = args.data_dir.split('/')[1]
print('I will save a file name contains ', filename)

if len(args.init_from) > 0:
    model = pickle.load(open(args.init_from, 'rb'))
else:
    model = MoreDeepRNN(len(vocab), n_units)
if args.gpu >= 0:
    cuda.get_device(args.gpu).use()
    model.to_gpu()

optimizer = optimizers.RMSprop(lr=args.learning_rate, alpha=args.decay_rate, eps=1e-8)
optimizer.setup(model)

whole_len    = train_data.shape[0]
jump         = whole_len / batchsize
epoch        = 0
start_at     = time.time()
cur_at       = start_at
state        = make_initial_state(n_units, batchsize=batchsize)
if args.gpu >= 0:
    accum_loss   = Variable(cuda.zeros(()))
    for key, value in list(state.items()):
        value.data = cuda.to_gpu(value.data)
else:
    accum_loss   = Variable(np.zeros((), dtype=np.float32))

print('going to train {} iterations'.format(jump * n_epochs))
loss_rate = 0.0
for i in range(int(jump * n_epochs)):
    x_batch = np.array([train_data[(jump * j + i) % whole_len]
                        for j in range(batchsize)])
    y_batch = np.array([train_data[(jump * j + i + 1) % whole_len]
                        for j in range(batchsize)])

    if args.gpu >=0:
        x_batch = cuda.to_gpu(x_batch)
        y_batch = cuda.to_gpu(y_batch)

    state, loss_i = model.forward_one_step(x_batch, y_batch, state, dropout_ratio=args.dropout)
    accum_loss   += loss_i

    if (i + 1) % bprop_len == 0:  # Run truncated BPTT
        now = time.time()
        print('{}/{}, train_loss = {}, time = {:.2f}'.format((i+1)/bprop_len, jump, accum_loss.data / bprop_len, now-cur_at))
        loss_rate = accum_loss.data / bprop_len
        cur_at = now

        optimizer.zero_grads()
        accum_loss.backward()
        accum_loss.unchain_backward()  # truncate
        if args.gpu >= 0:
            accum_loss = Variable(cuda.zeros(()))
        else:
            accum_loss = Variable(np.zeros((), dtype=np.float32))
        optimizer.clip_grads(grad_clip)
        optimizer.update()
    if (i + 1) % 5000 == 0:
        print(' will save chainermodel data...')
        print( '%s/latest_deeprnn_%s_%s_%d.chainermodel'%(args.checkpoint_dir, filename, args.json, n_units) )
        copyed_obj = copy.deepcopy(model).to_cpu()
        pickle.dump(copyed_obj, open('%s/latest_deeprnn_%s_%s_%d.chainermodel'%(args.checkpoint_dir, filename, args.json, n_units), 'wb'))

    if (i + 1) % jump == 0:
        epoch += 1
        if epoch >= args.learning_rate_decay_after:
            optimizer.lr *= args.learning_rate_decay
            print('decayed learning rate by a factor {} to {}'.format(args.learning_rate_decay, optimizer.lr))
    sys.stdout.flush()
pickle.dump(copy.deepcopy(model).to_cpu(), open('%s/finished_deeprnn_%s_%s_%d.chainermodel'%(args.checkpoint_dir, filename, args.json, n_units), 'wb'))
