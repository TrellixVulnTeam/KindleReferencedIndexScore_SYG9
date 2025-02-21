#!/usr/bin/env python

# python train_facade.py -g 0 -i ./facade/base --out result_facade --snapshot_interval 10000

from __future__ import print_function
import argparse
import os

import chainer
from chainer import training
from chainer.training import extensions
from chainer import serializers

from Net import Encoder
from Net import Decoder
from Net import Discriminator
from Net import Encoder2
from Net import Decoder2
from Net import Discriminator2
from Updater import Updater as Updater

#from Dataset import VecDataset as Dataset
#from Dataset import SixthDataset as Dataset
from Dataset import FontDataset as Dataset
from Visualizer import out_image
ALL_NUM = int(6622/2)
train_range = (1, int(ALL_NUM*0.8))
test_range  = (int(ALL_NUM*0.8)+1, ALL_NUM)
def main():
    parser = argparse.ArgumentParser(description='chainer implementation of pix2pix')
    parser.add_argument('--batchsize', '-b', type=int, default=1,
                        help='Number of images in each mini-batch')
    parser.add_argument('--epoch', '-e', type=int, default=500,
                        help='Number of sweeps over the dataset to train')
    parser.add_argument('--gpu', '-g', type=int, default=-1,
                        help='GPU ID (negative value indicates CPU)')
    parser.add_argument('--dataset', '-i', default='./facade/base',
                        help='Directory of image files.')
    parser.add_argument('--out', '-o', default='result',
                        help='Directory to output the result')
    parser.add_argument('--resume', '-r', default='',
                        help='Resume the training from snapshot')
    parser.add_argument('--seed', type=int, default=0,
                        help='Random seed')
    #parser.add_argument('--snapshot_interval', type=int, default=1000,
    #                    help='Interval of snapshot')
    parser.add_argument('--snapshot_interval', type=int, default=10000,
                        help='Interval of snapshot')
    parser.add_argument('--display_interval', type=int, default=100,
                        help='Interval of displaying log to console')
    args = parser.parse_args()

    print('GPU: {}'.format(args.gpu))
    print('# Minibatch-size: {}'.format(args.batchsize))
    print('# epoch: {}'.format(args.epoch))
    print('')

    # Set up a neural network to train
    IN_CH = 4
    OUT_CH = 3
    enc  = Encoder(in_ch=IN_CH)
    dec  = Decoder(out_ch=OUT_CH)
    dis  = Discriminator(in_ch=IN_CH, out_ch=OUT_CH)
    enc2 = Encoder2(in_ch=IN_CH)
    dec2 = Decoder2(out_ch=OUT_CH)    
    dis2 = Discriminator2(in_ch=IN_CH, out_ch=OUT_CH)
    if args.gpu >= 0:
        chainer.cuda.get_device(args.gpu).use()  # Make a specified GPU current
        enc.to_gpu()  # Copy the model to the GPU
        dec.to_gpu()
        dis.to_gpu()
        enc2.to_gpu()
        dec2.to_gpu()
        dis2.to_gpu()

    # Setup an optimizer
    def make_optimizer(model, alpha=0.0002, beta1=0.5):
        optimizer = chainer.optimizers.Adam(alpha=alpha, beta1=beta1)
        optimizer.setup(model)
        optimizer.add_hook(chainer.optimizer.WeightDecay(0.00001), 'hook_dec')
        return optimizer
    opt_enc  = make_optimizer(enc)
    opt_dec  = make_optimizer(dec)
    opt_dis  = make_optimizer(dis)
    opt_enc2 = make_optimizer(enc2)
    opt_dec2 = make_optimizer(dec2)
    opt_dis2 = make_optimizer(dis2)

    train_d = Dataset(args.dataset, data_range=train_range)
    test_d = Dataset(args.dataset, data_range=test_range)
    #train_iter = chainer.iterators.MultiprocessIterator(train_d, args.batchsize, n_processes=4)
    #test_iter = chainer.iterators.MultiprocessIterator(test_d, args.batchsize, n_processes=4)
    train_iter = chainer.iterators.SerialIterator(train_d, args.batchsize)
    test_iter = chainer.iterators.SerialIterator(test_d, args.batchsize)

    # Set up a trainer
    updater = Updater(
        models=(enc, dec, dis, enc2, dec2, dis2),
        iterator={
            'main': train_iter,
            'test': test_iter},
        optimizer={
            'enc': opt_enc, 
            'dec': opt_dec, 
            'dis': opt_dis,
            'enc2': opt_enc2,
            'dec2': opt_dec2,
            'dis2': opt_dec2,
            },
        device=args.gpu)
    trainer = training.Trainer(updater, (args.epoch, 'epoch'), out=args.out)

    snapshot_interval = (args.snapshot_interval, 'iteration')
    display_interval = (args.display_interval, 'iteration')
    trainer.extend(extensions.snapshot(
        filename='snapshot_iter_{.updater.iteration}.npz'),
                   trigger=snapshot_interval)
    trainer.extend(extensions.snapshot_object(
        enc, 'enc_iter_{.updater.iteration}.npz'), trigger=snapshot_interval)
    trainer.extend(extensions.snapshot_object(
        dec, 'dec_iter_{.updater.iteration}.npz'), trigger=snapshot_interval)
    trainer.extend(extensions.snapshot_object(
        dis, 'dis_iter_{.updater.iteration}.npz'), trigger=snapshot_interval)
    trainer.extend(extensions.LogReport(trigger=display_interval))
    trainer.extend(extensions.PrintReport([
        'epoch', 'iteration', 'enc/loss', 'dec/loss', 'dis/loss', 'enc2/loss', 'dec2/loss', 'dis2/loss'
    ]), trigger=display_interval)
    trainer.extend(extensions.ProgressBar(update_interval=10))
    trainer.extend(
        out_image(
            updater, enc, dec, enc2, dec2,
            5, 5, args.seed, args.out, IN_CH),
        trigger=snapshot_interval)

    if args.resume:
        # Resume from a snapshot
        chainer.serializers.load_npz(args.resume, trainer)

    # Run the training
    trainer.run()

if __name__ == '__main__':
    main()
