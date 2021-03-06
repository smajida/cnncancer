#!/usr/bin/env python
# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

print('train stacked autoencoder stage 1')

import os
import sys
import csv
import numpy as np
import pickle
from PIL import Image

import tensorflow as tf

import tensorflow_ae_base
from tensorflow_ae_base import *
import tensorflow_util
import myutil

exec(open('extern_params.py').read())

#
# load input data
#
ss = 32 # sample size
if(not 'qqq_trn' in locals()):
    file_input = 'qqq_trn_w{}.npy'.format(ss)
    path_data = os.path.join(dir_input,'input_w{}'.format(ss),file_input)
    tmp = np.load(path_data)
    tmp1 = []
    for aa in range(4):
        for bb in range(4):
            tmp1.append(tmp[:,(0+aa*8):(8+aa*8),(0+bb*8):(8+bb*8),:])
    qqq_trn = np.vstack(tmp1)
    print('load input from {}'.format(path_data))

nn,ny,nx,nl = qqq_trn.shape
print('nn ny nx nl',nn,ny,nx,nl)

nf_RGB = 3
lambda_s = 1e+3
nf_risa = 32
fs_1 = 8

if(stamp1=='NA'):
    ww = tf.Variable(tf.truncated_normal([fs_1,fs_1,nf_RGB,nf_risa],stddev=0.05))
else:
    file_ww = 'ww_risa.{}.pkl'.format(stamp1)
    path_ww = os.path.join('out1',file_ww)
    tmp = pickle.load(open(path_ww,'rb'))
    ww = tf.Variable(tmp)
    #dict_tmp = pickle.load(open(path_src,'rb'))
    #ww = dict_tmp['ww']

tf_input = tf.placeholder(tf.float32, [None,ny,nx,nl])

tf_conv1 = tf.nn.conv2d(tf_input,ww,strides=[1,1,1,1],padding='VALID')
tf_deconv1 = tf.nn.conv2d_transpose(value=tf_conv1,filter=ww,output_shape=[batch_size,ny,nx,nl],strides=[1,1,1,1],padding='VALID')
tf_error = tf.reduce_mean(tf.square(tf_deconv1 - tf_input))
## tf_error = tf.nn.l2_loss(tf_deconv1 - tf_input)

qqq = tf.square(tf_conv1)
ooo = tf.reduce_sum(qqq,3,keep_dims=True)
rrr = qqq / (tf.tile(ooo,[1,1,1,nf_risa])+1e-16)
tf_local_entropy1 = tf.reduce_sum(rrr * (-tf.log(rrr+1e-16)),3)
tf_entropy = tf.reduce_mean(tf_local_entropy1)
                
tf_simple1 = tf.square(tf_conv1)
seg24 = tf.constant([0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11])
tf_t_simple1 = tf.transpose(tf_simple1)
tf_sparce1 = tf.reduce_mean(tf.sqrt(tf.segment_sum(tf_t_simple1,seg24)))

# tf_score = tf_error 
# tf_score = tf_error * lambda_s + tf_sparce1
tf_score = lambda_s * tf_error + tf_entropy

optimizer = tf.train.AdagradOptimizer(learning_rate=learning_rate)
train = optimizer.minimize(tf_score)

sess.run(tf.initialize_all_variables())

iii_bin = np.arange(batch_size,nn,batch_size)
iii_nn = np.arange(nn)
iii_batches = np.split(iii_nn,iii_bin)

for tt in range(tmax):
    if(tt % tprint==0):
        tmp = [sess.run((tf_error,tf_entropy,tf_score),{tf_input: qqq_trn[iii,]}) for iii in iii_batches]
        error_out = np.mean([xxx[0] for xxx in tmp])
        sparc_out = np.mean([xxx[1] for xxx in tmp])
        score_out = np.mean([xxx[2] for xxx in tmp])
        print('tt error sparce score',tt,error_out,sparc_out,score_out)
    np.random.shuffle(iii_nn)
    iii_batches = np.split(iii_nn,iii_bin)
    for iii in iii_batches:
        sess.run(train,feed_dict={tf_input: qqq_trn[iii,]})

if(tt % tprint != 0):
    tmp = [sess.run((tf_error,tf_entropy,tf_score),{tf_input: qqq_trn[iii,]}) for iii in iii_batches]
    error_out = np.mean([xxx[0] for xxx in tmp])
    entropy_out = np.mean([xxx[1] for xxx in tmp])
    score_out = np.mean([xxx[2] for xxx in tmp])
    print('tt error sparce score',tmax,error_out,entropy_out,score_out)

img_org = tensorflow_util.get_image_from_qqq(qqq_trn[0:8])

qqq_deconv1 = tf_deconv1.eval({tf_input: qqq_trn[0:batch_size]})
img_out = tensorflow_util.get_image_from_qqq(qqq_deconv1[0:8])
img_cmp = myutil.rbind_image(img_org,img_out)
myutil.showsave(img_cmp,file_img="vld_risa.{}.jpg".format(stamp))

print('error:',np.mean((qqq_deconv1 - qqq_trn[0:batch_size])**2))

ww_out = ww.eval()
myutil.saveObject(ww_out,'ww_risa.{}.pkl'.format(stamp))

myutil.timestamp()
print('stamp1 = \'{}\''.format(stamp))

if(False):
    img_tmp1 = get_image_from_ww(ww_out[:,:,:,0])
    img_tmp2 = get_image_from_ww(ww_out[:,:,:,1])
    img_tmp3 = myutil.rbind_image(img_tmp1,img_tmp2)
    img_tmp4 = img_tmp3
    for bb in range(1,12):
        img_tmp1 = get_image_from_ww(ww_out[:,:,:,bb*2])
        img_tmp2 = get_image_from_ww(ww_out[:,:,:,bb*2+1])
        img_tmp3 = myutil.rbind_image(img_tmp1,img_tmp2)
        img_tmp4 = myutil.cbind_image(img_tmp4,img_tmp3)
    myutil.showsave(img_tmp4,file_img='tmp.jpg')
# endif
