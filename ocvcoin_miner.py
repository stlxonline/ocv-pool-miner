#!/usr/bin/env python3

import urllib.request
import urllib.error
import urllib.parse
import base64
import json
import hashlib
import struct
import random, string
import time
import os
import sys

import secrets
import numpy as np
import cv2
import platform
import ssl
import multiprocessing

from test_framework.segwit_addr import (
    decode_segwit_address
)
from test_framework.blocktools import (
    create_block,
    NORMAL_GBT_REQUEST_PARAMS,
    TIME_GENESIS_BLOCK,
    script_BIP34_coinbase_height,
    add_witness_commitment
)
from test_framework.messages import (
    CBlock,
    CBlockHeader,
    BLOCK_HEADER_SIZE,
)
from test_framework.messages import (
    CBlock,
    COIN,
    COutPoint,
    CTransaction,
    CTxIn,
    CTxOut
)


CURRENT_MINER_VERSION = "2.0.0.0"


# JSON-HTTP RPC Configuration

## PUBLIC RPC SERVER
## THIS CAN WORK SLOWLY OR BE OUT OF SERVICE SOMETIMES!
RPC_URL = "https://ocv.mergedpools.com/ocvrpc.php"
RPC_USER = "NOT REQUIRED" 
RPC_PASS = "NOT REQUIRED" 

## THE FASTEST AND GUARANTEED SOLUTION
## EDIT AND UNCOMMENT, FOR CONNECT TO YOUR OWN RPC SERVER
#RPC_URL = "http://127.0.0.1:8332"
#RPC_USER = "ocvcoinrpc" 
#RPC_PASS = "YourNewRpcServerPassword"

"""
How to enable your own RPC server?

For Windows 
Step 1: Install Ocvcoin Core (https://youtu.be/z3Eh1TgPu78)
Step 2: Create a file located C:/Users/your windows user name/AppData/Roaming/Ocvcoin/ocvcoin.conf and paste the following into it.
Step 3: Start POW SERVER and Ocvcoin Core

rpcuser=ocvcoinrpc
rpcpassword=YourNewRpcServerPassword
rpcallowip=0.0.0.0/0
rpcbind=0.0.0.0
daemon=1
server=1



If you have installed to ubuntu with autoinstall script, it is already active and you can write down the username and password given to you at the end of the installation. If you forgot, open /root/.ocvcoin/ocvcoin.conf and look.
"""


FILTER_KERNEL = np.array(
              [
                [0.0, -1.0, 0.0], 
                [-1.0, 5.0, -1.0],
                [0.0, -1.0, 0.0]
              ]
              )

FILTER_KERNEL = FILTER_KERNEL/(np.sum(FILTER_KERNEL) if np.sum(FILTER_KERNEL)!=0 else 1)
NEW_IMAGE_REFERANCE_BYTES = bytearray(1782)

def new_init_image():
    global final_init_img
    global block_header
    
    #24*24 24bit bmp
    final_init_img = bytearray(b'\x42\x4D\xF6\x06\x00\x00\x00\x00\x00\x00\x36\x00\x00\x00\x28\x00\x00\x00\x18\x00\x00\x00\x18\x00\x00\x00\x01\x00\x18\x00\x00\x00\x00\x00\xC0\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')


    start_hash = block_header[0:76]

    i = 0
    while i < 27:
        start_hash = hashlib.sha512(start_hash).digest()
        final_init_img = final_init_img + start_hash
        i += 1

    i = 0
    while i < 1782:
        NEW_IMAGE_REFERANCE_BYTES[i] = final_init_img[i]
        i += 1
    final_init_img = np.asarray(final_init_img, dtype="uint8")



def new_hash_block():
    global final_init_img
    global block_header
    


    
    img_src = cv2.imdecode(final_init_img, cv2.IMREAD_COLOR)



    img_src = cv2.bilateralFilter(img_src, 15, 75, 75)


    
    img_src = cv2.filter2D(img_src,-1,FILTER_KERNEL)

    img_src = cv2.blur(img_src, (5, 5))

    img_src = cv2.GaussianBlur(img_src, (5, 5),cv2.BORDER_DEFAULT)

    img_src = cv2.medianBlur(img_src, 5)



    is_success, im_buf_arr = cv2.imencode(".bmp", img_src)
    byte_im = im_buf_arr.tobytes()


    return hashlib.sha256(byte_im+block_header).digest()


def new_hash_block_for_testing(block_data):


    #24*24 24bit bmp
    init_image_bytes = bytearray(b'\x42\x4D\xF6\x06\x00\x00\x00\x00\x00\x00\x36\x00\x00\x00\x28\x00\x00\x00\x18\x00\x00\x00\x18\x00\x00\x00\x01\x00\x18\x00\x00\x00\x00\x00\xC0\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')


    start_hash = block_data[0:76]

    i = 0
    while i < 27:
        start_hash = hashlib.sha512(start_hash).digest()
        init_image_bytes = init_image_bytes + start_hash
        i += 1
        
   


    nonce_bytes = block_data[76:80]




    i = 54 #first 54byte bmp header
    j = 0
    while i < 1782:        
        init_image_bytes[i] = init_image_bytes[i] ^ nonce_bytes[j]
        j += 1
        i += 1        
        if j == 4:
            j = 0


    nparr = np.asarray(init_image_bytes, dtype="uint8")
    img_src = cv2.imdecode(nparr, cv2.IMREAD_COLOR)



    img_src = cv2.bilateralFilter(img_src, 15, 75, 75)

    kernel = np.array(
                  [
                    [0.0, -1.0, 0.0], 
                    [-1.0, 5.0, -1.0],
                    [0.0, -1.0, 0.0]
                  ]
                  )

    kernel = kernel/(np.sum(kernel) if np.sum(kernel)!=0 else 1)
    
    img_src = cv2.filter2D(img_src,-1,kernel)

    img_src = cv2.blur(img_src, (5, 5))

    img_src = cv2.GaussianBlur(img_src, (5, 5),cv2.BORDER_DEFAULT)

    img_src = cv2.medianBlur(img_src, 5)



    is_success, im_buf_arr = cv2.imencode(".bmp", img_src)
    byte_im = im_buf_arr.tobytes()


    return hashlib.sha256(byte_im+block_data).digest()
    
    
    
def create_coinbase_via_bech32_addr(height, bech32_20byte_hash, coinbasevalue, extra_output_script=None):
    
    coinbase = CTransaction()
    coinbase.vin.append(CTxIn(COutPoint(0, 0xffffffff), script_BIP34_coinbase_height(height), 0xffffffff))
    coinbaseoutput = CTxOut()

    coinbaseoutput.nValue = coinbasevalue
    coinbaseoutput.scriptPubKey = b'\x00\x14'+bech32_20byte_hash
    
    coinbase.vout = [coinbaseoutput]
    if extra_output_script is not None:
        coinbaseoutput2 = CTxOut()
        coinbaseoutput2.nValue = 0
        coinbaseoutput2.scriptPubKey = extra_output_script
        coinbase.vout.append(coinbaseoutput2)
    coinbase.calc_sha256()
    return coinbase
def screen_clear():
   # for mac and linux(here, os.name is 'posix')
   if os.name == 'posix':
      _ = os.system('clear')
   else:
      # for windows platfrom
      _ = os.system('cls')



#32*32 24bit randomized bmp
INIT_IMAGE_BYTES = bytearray(b'\x42\x4d\x36\x0c\x00\x00\x00\x00\x00\x00\x36\x00\x00\x00\x28\x00\x00\x00\x20\x00\x00\x00\x20\x00\x00\x00\x01\x00\x18\x00\x00\x00\x00\x00\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x37\xec\x6a\xf6\x1a\xd3\x9f\xa5\xc4\x0b\x0c\x36\x65\xff\x6e\x2c\x2e\x54\xd0\x7d\xa8\xae\xa1\x1a\xbd\x61\x75\x0a\x6f\x02\xfd\x4e\x3b\x2f\x6d\xf5\x28\x8c\x62\x44\x5c\x01\x70\x69\xce\xc2\xb8\x7b\x19\xcb\x31\xba\x1e\x85\xbc\x91\xfd\xab\xf9\x46\x73\x55\x2b\x53\x09\xfd\x79\x7f\x00\xd0\x21\x20\x31\x9a\xff\x4f\x8b\x93\x45\x27\xe1\xd0\x92\x29\x41\x7c\x1b\xd9\xe0\xe4\x0c\xc4\x75\xb5\x45\xdc\x22\x4d\x38\xef\xf3\x24\x6c\xa3\x5a\x8f\x82\xa6\x2e\x1a\x44\xe3\x76\xa4\xd3\x9d\xd3\x95\x11\x36\x7e\x9f\xb4\x09\x08\x1a\xe8\x43\x8a\x50\xbf\x5f\xa7\x48\xb0\x88\xed\xcb\x4e\xb6\x3d\x24\xf0\x07\xc0\xb7\x75\x84\x87\x8c\xe5\x9d\x82\x06\x3d\x78\x07\xa7\x65\x37\x62\x98\xb0\xb2\x6a\x24\xcf\x43\x75\x3f\xd4\xaa\xf4\x48\xf9\xe9\x71\x16\x81\xd2\x4a\xe9\x39\x90\xbe\x63\x3b\xb7\x23\x5d\x82\x5d\x1d\x44\x6a\xd0\x3d\xbd\x05\xb0\x37\x63\x9d\x42\x4a\xcf\x1c\xf2\x17\x31\xec\x21\xc8\x44\xcb\x1a\x6b\xd4\x9f\xa9\xfc\x16\x26\xce\x48\xd5\xbd\xe4\xaa\xef\x82\xf4\xea\x3b\xd1\x22\xa5\xa2\xc9\x95\x51\x3f\x24\xea\xc0\xfb\x13\x68\x77\x36\x16\x88\x96\xe0\x21\xe9\x85\x14\x96\x2c\x8c\x86\xa2\x12\xea\xea\xde\xa0\x97\x24\x32\xe5\xf8\x98\xd1\x9e\x1d\x1e\xe2\xff\x1d\xee\x52\x2d\x46\x04\x6b\x69\x56\x09\xe9\xcd\xb8\xa2\x43\x88\x09\xa3\x38\xc0\xbc\x41\x19\x52\x04\x3b\xe9\x7d\xe4\x9a\x55\xe7\x66\x51\xbb\x4e\x5e\xbc\x3f\x67\xfe\xa2\xb9\xda\xaf\x46\xa9\xc7\xdd\x9b\xc6\xa2\x14\xc8\xe7\x3a\x47\x99\x5a\x28\x4d\x58\x09\x30\xb3\x0d\xe7\x19\xa8\x33\x44\xef\x60\x1a\x3c\xb5\x27\x54\x56\xda\x3d\xec\x58\xfb\x68\x4e\xb4\x10\xde\x32\x66\x1a\x55\x65\x2b\xa9\xd7\x76\xa9\xf9\x9f\xd4\x7e\x85\xc9\xdb\x5d\xe6\x4f\xa9\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf9\xba\xf0\x67\x0f\xc2\x40\x80\x47\xff\xff\xff\x44\xe8\x44\xc3\xff\x23\x0e\x90\x68\xee\xa5\x66\x4f\x36\x0d\xe1\x8e\xe9\x6c\xd0\xfc\x10\x50\xca\xdf\x30\xa3\x5f\x35\xbf\x16\xbc\xc0\xf1\x9d\x6b\xc9\xf7\x39\x30\x52\x39\xd3\xbe\xd3\x79\x59\x47\x99\xa3\x8d\x01\xb3\x68\x87\x2d\x98\x6c\x09\x64\x93\xac\xe1\x8a\x1a\xc1\x06\x8b\xcd\xb1\x8f\x64\x6a\x6f\x4b\x6d\x50\x54\x54\x49\xc1\x16\x08\x67\x42\x9f\x9b\x31\x0c\xef\x58\xb2\x88\x3a\x86\x4e\x24\x66\x42\x4e\x6f\x10\x04\x2a\xb8\xf3\x3f\xef\xd0\xe7\x84\x80\x1e\x02\x95\x0c\x6e\xd0\x69\x59\xbd\x36\xc5\x2c\x1a\xc2\x31\xbe\xad\xa7\xb1\x8b\x51\xfc\x82\x7e\x77\x44\x6a\x88\x7f\xe0\x05\x5e\x59\x2f\x3a\x95\x63\x80\xd0\x3a\x51\x5b\xad\x7a\xab\x65\x92\xcb\xcc\x8f\xca\x0e\x94\x6c\x4b\xa9\xae\x59\x40\xe3\x45\x7c\x1c\xeb\x9e\x2a\xe5\x85\x3d\xcf\xd7\x0a\x15\x2e\x97\xc9\xac\x18\xda\x3d\x34\x9d\xc8\x37\xde\xbf\x64\xc1\x2c\xba\xf0\x96\xd0\x0f\x87\xb7\xa7\x24\xe8\x60\xae\xa5\xb7\x44\xd3\x35\x99\x2a\xb6\x22\x3e\xd6\x2d\x05\xcc\xc2\xdd\x5d\x18\xc8\x45\xa2\x01\x83\x59\x3c\xf0\xcb\xbb\xf2\xf9\x19\x79\xb5\xd4\x06\xf6\x9f\x13\xfa\x2f\x35\x17\x2b\x51\x3a\xb6\x25\xa3\x06\x22\x01\xff\x2b\xde\x14\xcd\xca\x32\x16\xbc\xa4\x36\x71\xdf\x2f\xe0\x75\x10\x24\x1f\x03\x3a\x66\x78\xd1\x16\x81\xb5\xe2\xe1\x5d\x0e\x30\x05\x49\xd9\xdb\xcc\xde\xd7\x83\xe1\xb1\x48\xaf\x7d\x4a\x11\xbc\xb5\x9f\x71\x26\x8d\x47\x9d\x2c\xe7\x1b\x05\x0f\x5e\x3d\x17\x0f\x78\x2e\xd6\x03\x8e\x47\x62\x7e\x10\x56\xf2\xad\x95\x42\x6a\x9a\xab\xae\xc8\x71\x7f\xc0\xde\x94\xbf\x17\x0a\x27\xb3\x2b\x85\x11\x15\x47\x6b\xd5\xf8\x67\x38\xdf\xd6\xff\xff\xff\x6f\xd2\x0c\x1d\x3d\x2c\xde\xf2\xe7\xff\xff\xff\x44\xc2\x9d\xd3\x42\xe2\x3f\x27\x3e\xd8\x39\xbb\xa9\xcc\x86\x64\x7b\xc2\x36\x90\xcb\x43\x38\x2e\x2b\x7d\xd6\xc4\xab\x0d\x65\xdf\x16\x25\x53\x86\x67\x30\x2e\x9f\xe9\x4a\x17\xf8\xaf\x49\xc2\x3e\xb2\xa4\x6d\xf2\x01\xfb\x28\x3c\xf8\xf2\x3a\x22\xd9\x42\x85\xbc\x0b\xd6\x93\x04\x99\xd1\x6f\x98\x3a\x57\x96\x2e\x65\x3b\xc1\x25\x9d\x95\xa2\x9a\x9e\x89\x84\xa8\xf6\x32\x19\xa2\x80\xd0\x88\x47\xbb\xdb\x2c\x52\x4d\x75\x6b\x20\x65\x48\x37\x53\x9a\xe8\xfd\x03\xe0\x3c\x22\xac\x8c\xfe\x29\xa0\xd9\xda\x6d\xee\xbe\x45\x32\x42\xf6\x91\x0f\xdc\x54\x5e\xdd\x83\x93\x67\xdd\x2d\x44\xb2\x91\x3e\xdb\xcd\xeb\xd4\x5a\xb2\x81\xa7\x80\x53\xdd\xcf\x44\x46\x29\x18\x3c\x62\x5a\x30\x7b\x3f\xfa\x59\x15\x4d\xbc\x44\x46\x41\xa7\x28\xa5\xed\xc2\xa1\x55\xa6\xe9\x39\xc5\x2a\x79\x8f\xba\xa5\x21\x55\x6c\x53\x1b\x2e\x5d\x9b\x21\x2a\x96\xab\xa0\xf6\x64\x45\xfb\xcc\x46\xb6\x9a\xdc\x6e\xe3\x04\x46\x11\x80\xde\xde\xc3\x6a\xc8\xf1\xc0\x3b\x6a\x1f\xf9\x2b\xbb\xf6\x54\x04\xac\x59\x45\x1b\x32\x80\xdf\xbc\x32\x53\x00\xfb\x3a\x7a\x0c\xd2\xbc\xd1\x88\xe7\x72\x49\x62\x50\xa2\x67\x4d\xaa\xa9\x7b\xe7\xbc\xc6\xea\x70\xe8\x43\xa2\x7f\xdf\x22\x98\xce\x82\x7d\x09\x55\x58\x1e\x7c\xa7\x39\xee\xa3\xa8\x7d\x19\xec\x84\x7f\xbf\x84\xf1\x85\x83\x13\xb2\x6f\x70\x8d\xda\x25\xbf\x3b\xe5\xf7\x89\x03\x07\xcc\x06\x98\x0e\xeb\x3b\x1c\x84\xfe\x4d\x7b\xbb\x5d\x8e\x11\x1e\x05\x9c\x0a\xc0\x21\xd2\x6c\x58\x11\x0a\xb2\x44\xd7\x5c\xff\x06\x3c\x14\x7d\xa1\x9f\xee\x9a\x45\x04\xac\x9b\x40\x82\xb6\x1f\x57\xe3\x80\x64\xe2\x8f\x81\x8e\xee\xff\xff\xff\x2e\xe9\x2b\xe9\x0c\x65\x47\xf8\x6a\xff\xff\xff\x43\x64\x27\xfb\xf7\xe9\x8e\x7e\x9d\x8f\xed\x2c\xef\xb3\x0a\x83\x6c\x07\x17\x64\x7c\x7a\xd0\x93\xa8\x74\xb6\x13\x89\x3e\x74\xe3\xdc\xc8\xdb\x15\xf5\xf2\x7c\xdf\xc8\x36\xc8\x6f\x6a\xba\x65\x21\x0d\xad\xae\x62\xda\xc4\x67\x79\x8c\x54\x9f\x66\x8c\x84\xc3\xc7\x29\x0e\x13\x53\xc5\x89\x94\x25\x12\x6c\xac\x3c\x48\x90\x49\xb0\x43\xec\x42\xdd\x0b\x7b\xa6\x23\xdb\x00\x4e\xfc\x4e\x62\x85\x7e\x7a\xa7\x86\x25\x24\x3d\x8a\x2d\x4a\x01\x50\xeb\xb5\x84\x8d\x2f\x64\xe4\xe8\xcd\x66\x00\xa3\x67\x94\x9e\xcf\x27\x97\x4d\x83\x3f\x9b\xba\x3b\x84\x86\x45\xfe\x12\x0e\x14\x25\x46\x6e\x7a\x3c\x5a\x5e\x53\x2a\xd3\x4a\x9c\xf5\x67\xef\x7f\xdc\x54\x41\x30\x08\xf5\x66\xf1\x03\xcc\x75\xfc\x47\x2d\x1f\xfc\x42\xf9\x4f\x27\xd1\x1d\x0e\xb5\x99\x0f\x82\x08\xc6\xe9\x35\x9c\xce\xca\xc1\x65\xe6\xdb\x28\xdf\xcc\xbf\x49\x57\xa3\x10\x1f\x23\xa6\xce\xd5\x00\x51\xbe\xf1\x94\x69\xbc\xe7\xef\x34\xc7\x0e\xb2\x9b\x51\xec\x00\xf0\xb4\xa3\x7b\xdc\xac\x07\x9e\x7a\xc3\xa9\x0a\xd3\xfc\x51\xac\xb4\x03\x93\x72\x46\xdd\xd9\x02\x36\x4a\xbd\x8b\x79\x0a\xdc\x01\x4d\xa1\x83\x68\x57\x31\x21\x46\x10\x39\xe3\x39\x42\x5b\x77\xcd\x24\x69\x9c\x03\x22\xba\xf2\xeb\xb9\x1a\x04\x74\x4b\x64\x0b\x71\x8f\xe9\x96\x14\x11\x6e\xd7\xc0\x5b\x30\xb1\xc9\x78\xd1\x85\xd7\x51\xd3\xce\x54\x53\xab\xd2\x6d\xf6\xd2\x12\xed\xf0\x0c\x5a\x9a\xa1\x62\x3e\x75\xd6\x78\xbd\x5d\xbc\xa8\xa4\x21\x1c\xae\x6e\xdf\x41\x4e\x4e\xae\x24\x6b\xef\x9f\x64\xbc\x45\xf8\x92\xf0\xe0\x09\x7f\x41\x70\x59\x1f\x47\x8e\x00\xba\xcb\x4a\x98\xf2\xe9\x8f\xe2\x16\x64\x09\xff\xff\xff\x1d\xce\x98\x56\x70\x00\xf3\x13\xdf\xff\xff\xff\x9a\xf0\x3c\x39\x3c\xf0\x7b\x8f\xfc\xb4\xfd\x8a\xe4\x2a\x0b\x81\x72\xb2\xd6\xcf\xdb\x94\x6f\x45\xd9\xa2\xaa\xfb\xf5\x44\xab\x81\xfa\xd2\x28\xd9\x9e\x41\xa3\xec\x1c\x4c\xaf\xdc\x4f\x44\x25\x7a\xae\x59\x1c\x7a\xab\x5e\xb3\xb7\x38\xb5\xd7\xf1\x93\xad\xa0\x21\x2a\x98\x69\x74\xb6\x21\x9d\x52\x69\xbf\x0d\xfa\x7e\x0f\x02\x68\x95\xfe\xb5\xdf\x63\x84\x80\x24\xd9\x59\x23\xb9\xc7\x04\x1e\x12\xe0\xda\xc1\x83\x5f\x62\x77\x9c\xb0\x54\x99\x87\x54\x89\x69\xd2\x48\x82\x54\x8b\x5f\x8f\x1c\xd9\xa5\x5e\x08\x9a\x03\xa3\x6d\x96\xb3\x9a\x2a\x96\xa0\xd5\x59\xbd\xa7\xa5\xe8\x17\xac\xcb\x30\x51\xd8\xcf\xf3\x3a\x57\x59\x8a\x7e\x8d\xc2\x22\x2f\x0d\xff\x24\x32\xae\xf2\xbe\xa8\x23\x92\xb3\x3d\x81\x95\x93\x98\xdc\xd1\x85\xb6\xea\xbf\x91\x27\xb2\xf0\x62\x0e\x26\xe0\xf7\x6b\x4d\xcb\xac\xa2\xd0\x8e\x23\x41\x1d\xd8\x2f\xb1\x9b\x03\x76\x3f\x88\xac\x56\xa2\x91\x8d\xfb\x2d\x53\xa1\x5e\x8a\xb8\x12\x77\x43\xc9\x4f\xb7\xbd\x2a\x10\xee\x58\xdd\xc4\xe4\x1e\xa3\x09\x8f\x20\x14\xb0\x40\xd3\x44\x52\x07\x4d\x69\xb6\x20\x8e\xcb\x60\x51\xfd\x92\x5b\x39\x18\xec\x50\xc0\x40\x2e\x19\x7b\xd7\x05\x06\x7f\x90\x34\x92\xdd\x0c\x98\xd0\x77\xca\x3b\x47\x1d\x64\x9c\x97\x2c\x40\x2b\x02\x99\x28\x9c\x46\x78\xe6\x24\xa7\x00\x0a\x07\x43\xde\x21\xac\xe5\xbd\x70\x67\xc3\x39\x6e\xff\xa7\xcf\x64\xdd\xd2\x6e\xb8\xa6\xbd\xe4\xd7\xb8\x24\x48\x89\xb9\xc4\x42\x66\xd4\xb8\xd4\xa3\xab\xf3\x67\x28\x1e\xc2\x48\x90\x1a\xfe\xa8\xa9\x9f\x1f\x17\xda\x61\x61\x55\x70\x3a\x11\x87\x41\x01\xee\x9a\xe9\x74\x17\x81\x76\x4b\xf0\x17\x8a\x65\xff\xff\xff\xa3\x3d\xf9\x31\x6d\x35\x5f\xc8\x8c\xff\xff\xff\x1e\xa6\x67\xda\x5f\x9a\xdd\x9c\xe1\x34\x32\x96\xc2\xb3\x49\x4a\xa3\x55\x84\x56\xfe\x91\x28\xbf\x55\x24\xb0\x8e\x88\x49\x41\x0c\x27\x43\x96\xe7\xd1\xb2\x15\xa8\x3f\x50\x60\xa5\x7e\x26\x32\xfb\x01\xe5\xb4\xcd\x33\x00\xdf\x5f\xc9\xd1\x32\x0a\x83\xb4\xab\x42\x01\xa5\x37\x43\x61\x9e\x80\x52\x1f\x76\xc2\x51\xcf\x20\x93\xcd\x00\x52\x16\xb1\x11\xad\xac\x15\xda\xab\x6f\xdd\x32\x30\x42\x3c\x2f\x9a\xd3\x8d\x65\x9a\xb5\x11\xda\x6e\x18\x49\x52\x17\x8b\xc0\x9a\x37\xbc\x7d\x0e\xd7\xfc\xb1\xe0\xa9\xd1\xed\xf0\x4c\x8c\xd9\x02\xd0\x94\x63\x5a\x24\xa7\xe0\x4c\x53\x95\xea\xfe\x87\x7e\x4e\x62\xc2\xdd\x72\x75\x7e\xad\xd8\x63\xf8\xe6\x1a\x57\x62\x92\xfb\xb1\x4a\x9e\xaf\x05\x0c\x0e\x9f\x75\x61\xeb\xa4\xd9\xc6\x4b\x05\x54\x7e\x9c\xda\x4e\x09\xbb\x82\x43\x1f\x0c\x0b\x19\x70\xfa\x98\xce\x5d\xd8\x12\xa7\xb4\x1c\x2b\xc1\x6f\xf2\xd2\xdb\x49\xf9\x7d\x97\xd4\xe7\xbc\x1b\x65\x01\xbc\x22\xed\xfe\xf9\x6c\xa2\x61\x50\x99\x54\x98\x4c\xe5\x27\x98\x9e\x75\x91\x6f\x3e\x4f\xf9\x7e\xfd\xe4\x28\x0a\x85\x99\xf9\xe6\xa6\x8b\x36\x11\xca\x74\x32\xba\x0e\x99\x4e\x0e\x53\xcd\xce\xaf\x05\x78\x23\xc4\x3c\xf6\x77\x08\xb8\x3b\xc2\x53\x51\x92\x5d\x8b\xb1\x27\x63\xa7\xc7\xe3\x81\x85\x7c\x29\xb0\xe8\xeb\x43\x43\xfe\xc8\xef\x5a\xdd\x73\xdf\xed\x3b\x5a\x5c\x2e\x00\x35\xbe\xa8\x2c\x2b\x19\x1f\x08\xb1\x94\xb1\xae\xdb\x27\x9a\xe4\x69\x88\xcd\xd9\xb1\xc6\x9e\x9e\xe4\xa3\x58\xe8\xd1\xc8\x74\xd3\xba\x58\x67\x69\x79\xf7\x19\x4a\x49\xb5\xd3\x71\x4f\xe1\x68\x1c\x7c\x8a\xb1\x05\x31\x19\x32\xd1\xc7\x71\xc0\xe2\x12\xe0\xff\xff\xff\x81\x08\x7c\xb7\xb6\xc6\x3a\x38\xc3\xff\xff\xff\xea\x85\x88\x62\x3c\xf0\x6c\x99\xbd\xb1\xe5\x0f\xc2\x4c\x7b\x16\x5a\xc5\xc3\x0f\xa5\xcb\x3d\x02\xff\xb1\x09\x38\x00\xf8\xab\x2f\xbd\x0d\x75\xf7\x9a\xeb\x20\x60\xe0\xbe\xe2\xe2\x5c\x15\xfc\x30\x81\x27\xd9\x99\x91\x47\xe3\x3c\x1a\x06\xcd\xa7\xc9\x06\x38\xe6\x5e\xcb\xaa\x71\xdb\x93\xaf\x23\xe1\x8a\xfe\x77\xc8\xd8\x2f\xfa\x6f\xfb\x32\x7c\x83\x15\x0d\xe9\x5b\xea\xc7\xfc\x6e\x23\x9e\x51\xc5\xa8\x4a\x94\x5e\xf4\xbb\x41\x92\xda\x08\x77\x75\x93\xa2\x25\x58\x3c\xa9\xb4\x1b\xff\xe1\x56\xf8\xe2\x2c\x5b\x62\xf3\xd3\xc2\x76\xcd\x80\x30\xdc\x60\xd0\xf7\xc5\x58\x41\x90\xe0\xb4\xc0\x67\x47\xdc\x70\xff\xff\xff\xff\xff\xff\xff\xff\xff\xbc\x43\x6e\xad\x6f\xc5\x8b\x1f\x53\x47\x2d\x4b\x32\x04\x93\xb2\x20\x78\xd7\xf9\x0c\x5b\x24\x69\x91\x73\xcd\x24\x99\x0d\x1a\x7d\x63\xd7\x06\x9b\x0e\x1c\xf3\xdd\x84\x5c\x66\xd6\x3f\x8f\x32\xf7\x50\x42\x37\x1b\x3f\x8d\xd1\xc4\x56\x9d\x97\xbc\xe7\x46\xb5\x9b\xc3\x05\x0a\xc4\xbd\xdd\xca\xfe\xcf\xbf\x67\x14\xbb\xb0\x1d\xbc\x33\xd4\x6b\x9c\xf1\xac\xac\x60\x48\x02\xf1\xd1\xf9\xd8\xdb\x97\xae\x02\x41\x2d\x1c\xc3\x6d\x1b\xce\xf1\x33\x40\xbe\x0d\x0c\x55\x94\x8b\x8a\x83\xae\xbd\x12\x00\x13\xe0\xe0\xb5\x60\xaf\x5f\x3d\xc2\x14\x21\xbe\xc9\x99\x68\xbf\x5d\xdb\x0d\x2f\x5c\x03\x7d\xfd\x66\xff\x1f\x80\xc8\xa8\x53\x05\x95\x9d\x5d\x88\x9e\x10\xe5\x58\x39\x19\xbf\x12\x49\xe3\x75\x0d\x9b\x92\xc6\xf9\xe5\x6f\x84\x65\x5a\x44\xe7\x32\x05\xe5\xd0\xa6\xd4\xa9\x48\xdf\xbc\x32\x3a\x7a\xb1\x99\x61\x33\x16\xa3\xdd\x94\x26\x56\x5c\x35\xc8\x5a\x18\x03\x75\xe8\xc9\x55\x81\xff\xff\xff\x9a\x16\x99')

def init_image():
    global final_init_img
    global block_header
    
    final_init_img = bytearray(len(INIT_IMAGE_BYTES))
    for i in range(len(INIT_IMAGE_BYTES)):
        final_init_img[i] = INIT_IMAGE_BYTES[i]
    
    block_header_len = len(block_header)

    i = 54
    j = 0
    while i < 3126 and j < block_header_len:
        final_init_img[i] = block_header[j]
        i += 1
        j += 1


    j = 0
    while i < 3126:
        if final_init_img[i] != 0xff:
            final_init_img[i] = final_init_img[i] ^ block_header[j]
            j += 1
        i += 1
    
        if j == block_header_len:
            j = 0

    final_init_img = np.asarray(final_init_img, dtype="uint8")



def hash_block(algo_selector):
    global final_init_img
    global block_header
    


    
    img_src = cv2.imdecode(final_init_img, cv2.IMREAD_COLOR)


    if algo_selector == 0:
        img_src = cv2.bilateralFilter(img_src, 15, 75, 75)
    elif algo_selector == 1:
        img_src = cv2.fastNlMeansDenoisingColored(img_src)

    elif algo_selector == 2:
        
        img_src = cv2.filter2D(img_src,-1,FILTER_KERNEL)

    elif algo_selector == 3:
        img_src = cv2.blur(img_src, (5, 5))


    elif algo_selector == 4:
        img_src = cv2.GaussianBlur(img_src, (5, 5),cv2.BORDER_DEFAULT)


    elif algo_selector == 5:
        img_src = cv2.medianBlur(img_src, 5)


    is_success, im_buf_arr = cv2.imencode(".bmp", img_src)
    byte_im = im_buf_arr.tobytes()


    return hashlib.sha256(byte_im+block_header).digest()[::-1]


def hash_block_for_testing(block_data):


    #32*32 24bit randomized bmp
    init_image_bytes = bytearray(b'\x42\x4d\x36\x0c\x00\x00\x00\x00\x00\x00\x36\x00\x00\x00\x28\x00\x00\x00\x20\x00\x00\x00\x20\x00\x00\x00\x01\x00\x18\x00\x00\x00\x00\x00\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x37\xec\x6a\xf6\x1a\xd3\x9f\xa5\xc4\x0b\x0c\x36\x65\xff\x6e\x2c\x2e\x54\xd0\x7d\xa8\xae\xa1\x1a\xbd\x61\x75\x0a\x6f\x02\xfd\x4e\x3b\x2f\x6d\xf5\x28\x8c\x62\x44\x5c\x01\x70\x69\xce\xc2\xb8\x7b\x19\xcb\x31\xba\x1e\x85\xbc\x91\xfd\xab\xf9\x46\x73\x55\x2b\x53\x09\xfd\x79\x7f\x00\xd0\x21\x20\x31\x9a\xff\x4f\x8b\x93\x45\x27\xe1\xd0\x92\x29\x41\x7c\x1b\xd9\xe0\xe4\x0c\xc4\x75\xb5\x45\xdc\x22\x4d\x38\xef\xf3\x24\x6c\xa3\x5a\x8f\x82\xa6\x2e\x1a\x44\xe3\x76\xa4\xd3\x9d\xd3\x95\x11\x36\x7e\x9f\xb4\x09\x08\x1a\xe8\x43\x8a\x50\xbf\x5f\xa7\x48\xb0\x88\xed\xcb\x4e\xb6\x3d\x24\xf0\x07\xc0\xb7\x75\x84\x87\x8c\xe5\x9d\x82\x06\x3d\x78\x07\xa7\x65\x37\x62\x98\xb0\xb2\x6a\x24\xcf\x43\x75\x3f\xd4\xaa\xf4\x48\xf9\xe9\x71\x16\x81\xd2\x4a\xe9\x39\x90\xbe\x63\x3b\xb7\x23\x5d\x82\x5d\x1d\x44\x6a\xd0\x3d\xbd\x05\xb0\x37\x63\x9d\x42\x4a\xcf\x1c\xf2\x17\x31\xec\x21\xc8\x44\xcb\x1a\x6b\xd4\x9f\xa9\xfc\x16\x26\xce\x48\xd5\xbd\xe4\xaa\xef\x82\xf4\xea\x3b\xd1\x22\xa5\xa2\xc9\x95\x51\x3f\x24\xea\xc0\xfb\x13\x68\x77\x36\x16\x88\x96\xe0\x21\xe9\x85\x14\x96\x2c\x8c\x86\xa2\x12\xea\xea\xde\xa0\x97\x24\x32\xe5\xf8\x98\xd1\x9e\x1d\x1e\xe2\xff\x1d\xee\x52\x2d\x46\x04\x6b\x69\x56\x09\xe9\xcd\xb8\xa2\x43\x88\x09\xa3\x38\xc0\xbc\x41\x19\x52\x04\x3b\xe9\x7d\xe4\x9a\x55\xe7\x66\x51\xbb\x4e\x5e\xbc\x3f\x67\xfe\xa2\xb9\xda\xaf\x46\xa9\xc7\xdd\x9b\xc6\xa2\x14\xc8\xe7\x3a\x47\x99\x5a\x28\x4d\x58\x09\x30\xb3\x0d\xe7\x19\xa8\x33\x44\xef\x60\x1a\x3c\xb5\x27\x54\x56\xda\x3d\xec\x58\xfb\x68\x4e\xb4\x10\xde\x32\x66\x1a\x55\x65\x2b\xa9\xd7\x76\xa9\xf9\x9f\xd4\x7e\x85\xc9\xdb\x5d\xe6\x4f\xa9\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf9\xba\xf0\x67\x0f\xc2\x40\x80\x47\xff\xff\xff\x44\xe8\x44\xc3\xff\x23\x0e\x90\x68\xee\xa5\x66\x4f\x36\x0d\xe1\x8e\xe9\x6c\xd0\xfc\x10\x50\xca\xdf\x30\xa3\x5f\x35\xbf\x16\xbc\xc0\xf1\x9d\x6b\xc9\xf7\x39\x30\x52\x39\xd3\xbe\xd3\x79\x59\x47\x99\xa3\x8d\x01\xb3\x68\x87\x2d\x98\x6c\x09\x64\x93\xac\xe1\x8a\x1a\xc1\x06\x8b\xcd\xb1\x8f\x64\x6a\x6f\x4b\x6d\x50\x54\x54\x49\xc1\x16\x08\x67\x42\x9f\x9b\x31\x0c\xef\x58\xb2\x88\x3a\x86\x4e\x24\x66\x42\x4e\x6f\x10\x04\x2a\xb8\xf3\x3f\xef\xd0\xe7\x84\x80\x1e\x02\x95\x0c\x6e\xd0\x69\x59\xbd\x36\xc5\x2c\x1a\xc2\x31\xbe\xad\xa7\xb1\x8b\x51\xfc\x82\x7e\x77\x44\x6a\x88\x7f\xe0\x05\x5e\x59\x2f\x3a\x95\x63\x80\xd0\x3a\x51\x5b\xad\x7a\xab\x65\x92\xcb\xcc\x8f\xca\x0e\x94\x6c\x4b\xa9\xae\x59\x40\xe3\x45\x7c\x1c\xeb\x9e\x2a\xe5\x85\x3d\xcf\xd7\x0a\x15\x2e\x97\xc9\xac\x18\xda\x3d\x34\x9d\xc8\x37\xde\xbf\x64\xc1\x2c\xba\xf0\x96\xd0\x0f\x87\xb7\xa7\x24\xe8\x60\xae\xa5\xb7\x44\xd3\x35\x99\x2a\xb6\x22\x3e\xd6\x2d\x05\xcc\xc2\xdd\x5d\x18\xc8\x45\xa2\x01\x83\x59\x3c\xf0\xcb\xbb\xf2\xf9\x19\x79\xb5\xd4\x06\xf6\x9f\x13\xfa\x2f\x35\x17\x2b\x51\x3a\xb6\x25\xa3\x06\x22\x01\xff\x2b\xde\x14\xcd\xca\x32\x16\xbc\xa4\x36\x71\xdf\x2f\xe0\x75\x10\x24\x1f\x03\x3a\x66\x78\xd1\x16\x81\xb5\xe2\xe1\x5d\x0e\x30\x05\x49\xd9\xdb\xcc\xde\xd7\x83\xe1\xb1\x48\xaf\x7d\x4a\x11\xbc\xb5\x9f\x71\x26\x8d\x47\x9d\x2c\xe7\x1b\x05\x0f\x5e\x3d\x17\x0f\x78\x2e\xd6\x03\x8e\x47\x62\x7e\x10\x56\xf2\xad\x95\x42\x6a\x9a\xab\xae\xc8\x71\x7f\xc0\xde\x94\xbf\x17\x0a\x27\xb3\x2b\x85\x11\x15\x47\x6b\xd5\xf8\x67\x38\xdf\xd6\xff\xff\xff\x6f\xd2\x0c\x1d\x3d\x2c\xde\xf2\xe7\xff\xff\xff\x44\xc2\x9d\xd3\x42\xe2\x3f\x27\x3e\xd8\x39\xbb\xa9\xcc\x86\x64\x7b\xc2\x36\x90\xcb\x43\x38\x2e\x2b\x7d\xd6\xc4\xab\x0d\x65\xdf\x16\x25\x53\x86\x67\x30\x2e\x9f\xe9\x4a\x17\xf8\xaf\x49\xc2\x3e\xb2\xa4\x6d\xf2\x01\xfb\x28\x3c\xf8\xf2\x3a\x22\xd9\x42\x85\xbc\x0b\xd6\x93\x04\x99\xd1\x6f\x98\x3a\x57\x96\x2e\x65\x3b\xc1\x25\x9d\x95\xa2\x9a\x9e\x89\x84\xa8\xf6\x32\x19\xa2\x80\xd0\x88\x47\xbb\xdb\x2c\x52\x4d\x75\x6b\x20\x65\x48\x37\x53\x9a\xe8\xfd\x03\xe0\x3c\x22\xac\x8c\xfe\x29\xa0\xd9\xda\x6d\xee\xbe\x45\x32\x42\xf6\x91\x0f\xdc\x54\x5e\xdd\x83\x93\x67\xdd\x2d\x44\xb2\x91\x3e\xdb\xcd\xeb\xd4\x5a\xb2\x81\xa7\x80\x53\xdd\xcf\x44\x46\x29\x18\x3c\x62\x5a\x30\x7b\x3f\xfa\x59\x15\x4d\xbc\x44\x46\x41\xa7\x28\xa5\xed\xc2\xa1\x55\xa6\xe9\x39\xc5\x2a\x79\x8f\xba\xa5\x21\x55\x6c\x53\x1b\x2e\x5d\x9b\x21\x2a\x96\xab\xa0\xf6\x64\x45\xfb\xcc\x46\xb6\x9a\xdc\x6e\xe3\x04\x46\x11\x80\xde\xde\xc3\x6a\xc8\xf1\xc0\x3b\x6a\x1f\xf9\x2b\xbb\xf6\x54\x04\xac\x59\x45\x1b\x32\x80\xdf\xbc\x32\x53\x00\xfb\x3a\x7a\x0c\xd2\xbc\xd1\x88\xe7\x72\x49\x62\x50\xa2\x67\x4d\xaa\xa9\x7b\xe7\xbc\xc6\xea\x70\xe8\x43\xa2\x7f\xdf\x22\x98\xce\x82\x7d\x09\x55\x58\x1e\x7c\xa7\x39\xee\xa3\xa8\x7d\x19\xec\x84\x7f\xbf\x84\xf1\x85\x83\x13\xb2\x6f\x70\x8d\xda\x25\xbf\x3b\xe5\xf7\x89\x03\x07\xcc\x06\x98\x0e\xeb\x3b\x1c\x84\xfe\x4d\x7b\xbb\x5d\x8e\x11\x1e\x05\x9c\x0a\xc0\x21\xd2\x6c\x58\x11\x0a\xb2\x44\xd7\x5c\xff\x06\x3c\x14\x7d\xa1\x9f\xee\x9a\x45\x04\xac\x9b\x40\x82\xb6\x1f\x57\xe3\x80\x64\xe2\x8f\x81\x8e\xee\xff\xff\xff\x2e\xe9\x2b\xe9\x0c\x65\x47\xf8\x6a\xff\xff\xff\x43\x64\x27\xfb\xf7\xe9\x8e\x7e\x9d\x8f\xed\x2c\xef\xb3\x0a\x83\x6c\x07\x17\x64\x7c\x7a\xd0\x93\xa8\x74\xb6\x13\x89\x3e\x74\xe3\xdc\xc8\xdb\x15\xf5\xf2\x7c\xdf\xc8\x36\xc8\x6f\x6a\xba\x65\x21\x0d\xad\xae\x62\xda\xc4\x67\x79\x8c\x54\x9f\x66\x8c\x84\xc3\xc7\x29\x0e\x13\x53\xc5\x89\x94\x25\x12\x6c\xac\x3c\x48\x90\x49\xb0\x43\xec\x42\xdd\x0b\x7b\xa6\x23\xdb\x00\x4e\xfc\x4e\x62\x85\x7e\x7a\xa7\x86\x25\x24\x3d\x8a\x2d\x4a\x01\x50\xeb\xb5\x84\x8d\x2f\x64\xe4\xe8\xcd\x66\x00\xa3\x67\x94\x9e\xcf\x27\x97\x4d\x83\x3f\x9b\xba\x3b\x84\x86\x45\xfe\x12\x0e\x14\x25\x46\x6e\x7a\x3c\x5a\x5e\x53\x2a\xd3\x4a\x9c\xf5\x67\xef\x7f\xdc\x54\x41\x30\x08\xf5\x66\xf1\x03\xcc\x75\xfc\x47\x2d\x1f\xfc\x42\xf9\x4f\x27\xd1\x1d\x0e\xb5\x99\x0f\x82\x08\xc6\xe9\x35\x9c\xce\xca\xc1\x65\xe6\xdb\x28\xdf\xcc\xbf\x49\x57\xa3\x10\x1f\x23\xa6\xce\xd5\x00\x51\xbe\xf1\x94\x69\xbc\xe7\xef\x34\xc7\x0e\xb2\x9b\x51\xec\x00\xf0\xb4\xa3\x7b\xdc\xac\x07\x9e\x7a\xc3\xa9\x0a\xd3\xfc\x51\xac\xb4\x03\x93\x72\x46\xdd\xd9\x02\x36\x4a\xbd\x8b\x79\x0a\xdc\x01\x4d\xa1\x83\x68\x57\x31\x21\x46\x10\x39\xe3\x39\x42\x5b\x77\xcd\x24\x69\x9c\x03\x22\xba\xf2\xeb\xb9\x1a\x04\x74\x4b\x64\x0b\x71\x8f\xe9\x96\x14\x11\x6e\xd7\xc0\x5b\x30\xb1\xc9\x78\xd1\x85\xd7\x51\xd3\xce\x54\x53\xab\xd2\x6d\xf6\xd2\x12\xed\xf0\x0c\x5a\x9a\xa1\x62\x3e\x75\xd6\x78\xbd\x5d\xbc\xa8\xa4\x21\x1c\xae\x6e\xdf\x41\x4e\x4e\xae\x24\x6b\xef\x9f\x64\xbc\x45\xf8\x92\xf0\xe0\x09\x7f\x41\x70\x59\x1f\x47\x8e\x00\xba\xcb\x4a\x98\xf2\xe9\x8f\xe2\x16\x64\x09\xff\xff\xff\x1d\xce\x98\x56\x70\x00\xf3\x13\xdf\xff\xff\xff\x9a\xf0\x3c\x39\x3c\xf0\x7b\x8f\xfc\xb4\xfd\x8a\xe4\x2a\x0b\x81\x72\xb2\xd6\xcf\xdb\x94\x6f\x45\xd9\xa2\xaa\xfb\xf5\x44\xab\x81\xfa\xd2\x28\xd9\x9e\x41\xa3\xec\x1c\x4c\xaf\xdc\x4f\x44\x25\x7a\xae\x59\x1c\x7a\xab\x5e\xb3\xb7\x38\xb5\xd7\xf1\x93\xad\xa0\x21\x2a\x98\x69\x74\xb6\x21\x9d\x52\x69\xbf\x0d\xfa\x7e\x0f\x02\x68\x95\xfe\xb5\xdf\x63\x84\x80\x24\xd9\x59\x23\xb9\xc7\x04\x1e\x12\xe0\xda\xc1\x83\x5f\x62\x77\x9c\xb0\x54\x99\x87\x54\x89\x69\xd2\x48\x82\x54\x8b\x5f\x8f\x1c\xd9\xa5\x5e\x08\x9a\x03\xa3\x6d\x96\xb3\x9a\x2a\x96\xa0\xd5\x59\xbd\xa7\xa5\xe8\x17\xac\xcb\x30\x51\xd8\xcf\xf3\x3a\x57\x59\x8a\x7e\x8d\xc2\x22\x2f\x0d\xff\x24\x32\xae\xf2\xbe\xa8\x23\x92\xb3\x3d\x81\x95\x93\x98\xdc\xd1\x85\xb6\xea\xbf\x91\x27\xb2\xf0\x62\x0e\x26\xe0\xf7\x6b\x4d\xcb\xac\xa2\xd0\x8e\x23\x41\x1d\xd8\x2f\xb1\x9b\x03\x76\x3f\x88\xac\x56\xa2\x91\x8d\xfb\x2d\x53\xa1\x5e\x8a\xb8\x12\x77\x43\xc9\x4f\xb7\xbd\x2a\x10\xee\x58\xdd\xc4\xe4\x1e\xa3\x09\x8f\x20\x14\xb0\x40\xd3\x44\x52\x07\x4d\x69\xb6\x20\x8e\xcb\x60\x51\xfd\x92\x5b\x39\x18\xec\x50\xc0\x40\x2e\x19\x7b\xd7\x05\x06\x7f\x90\x34\x92\xdd\x0c\x98\xd0\x77\xca\x3b\x47\x1d\x64\x9c\x97\x2c\x40\x2b\x02\x99\x28\x9c\x46\x78\xe6\x24\xa7\x00\x0a\x07\x43\xde\x21\xac\xe5\xbd\x70\x67\xc3\x39\x6e\xff\xa7\xcf\x64\xdd\xd2\x6e\xb8\xa6\xbd\xe4\xd7\xb8\x24\x48\x89\xb9\xc4\x42\x66\xd4\xb8\xd4\xa3\xab\xf3\x67\x28\x1e\xc2\x48\x90\x1a\xfe\xa8\xa9\x9f\x1f\x17\xda\x61\x61\x55\x70\x3a\x11\x87\x41\x01\xee\x9a\xe9\x74\x17\x81\x76\x4b\xf0\x17\x8a\x65\xff\xff\xff\xa3\x3d\xf9\x31\x6d\x35\x5f\xc8\x8c\xff\xff\xff\x1e\xa6\x67\xda\x5f\x9a\xdd\x9c\xe1\x34\x32\x96\xc2\xb3\x49\x4a\xa3\x55\x84\x56\xfe\x91\x28\xbf\x55\x24\xb0\x8e\x88\x49\x41\x0c\x27\x43\x96\xe7\xd1\xb2\x15\xa8\x3f\x50\x60\xa5\x7e\x26\x32\xfb\x01\xe5\xb4\xcd\x33\x00\xdf\x5f\xc9\xd1\x32\x0a\x83\xb4\xab\x42\x01\xa5\x37\x43\x61\x9e\x80\x52\x1f\x76\xc2\x51\xcf\x20\x93\xcd\x00\x52\x16\xb1\x11\xad\xac\x15\xda\xab\x6f\xdd\x32\x30\x42\x3c\x2f\x9a\xd3\x8d\x65\x9a\xb5\x11\xda\x6e\x18\x49\x52\x17\x8b\xc0\x9a\x37\xbc\x7d\x0e\xd7\xfc\xb1\xe0\xa9\xd1\xed\xf0\x4c\x8c\xd9\x02\xd0\x94\x63\x5a\x24\xa7\xe0\x4c\x53\x95\xea\xfe\x87\x7e\x4e\x62\xc2\xdd\x72\x75\x7e\xad\xd8\x63\xf8\xe6\x1a\x57\x62\x92\xfb\xb1\x4a\x9e\xaf\x05\x0c\x0e\x9f\x75\x61\xeb\xa4\xd9\xc6\x4b\x05\x54\x7e\x9c\xda\x4e\x09\xbb\x82\x43\x1f\x0c\x0b\x19\x70\xfa\x98\xce\x5d\xd8\x12\xa7\xb4\x1c\x2b\xc1\x6f\xf2\xd2\xdb\x49\xf9\x7d\x97\xd4\xe7\xbc\x1b\x65\x01\xbc\x22\xed\xfe\xf9\x6c\xa2\x61\x50\x99\x54\x98\x4c\xe5\x27\x98\x9e\x75\x91\x6f\x3e\x4f\xf9\x7e\xfd\xe4\x28\x0a\x85\x99\xf9\xe6\xa6\x8b\x36\x11\xca\x74\x32\xba\x0e\x99\x4e\x0e\x53\xcd\xce\xaf\x05\x78\x23\xc4\x3c\xf6\x77\x08\xb8\x3b\xc2\x53\x51\x92\x5d\x8b\xb1\x27\x63\xa7\xc7\xe3\x81\x85\x7c\x29\xb0\xe8\xeb\x43\x43\xfe\xc8\xef\x5a\xdd\x73\xdf\xed\x3b\x5a\x5c\x2e\x00\x35\xbe\xa8\x2c\x2b\x19\x1f\x08\xb1\x94\xb1\xae\xdb\x27\x9a\xe4\x69\x88\xcd\xd9\xb1\xc6\x9e\x9e\xe4\xa3\x58\xe8\xd1\xc8\x74\xd3\xba\x58\x67\x69\x79\xf7\x19\x4a\x49\xb5\xd3\x71\x4f\xe1\x68\x1c\x7c\x8a\xb1\x05\x31\x19\x32\xd1\xc7\x71\xc0\xe2\x12\xe0\xff\xff\xff\x81\x08\x7c\xb7\xb6\xc6\x3a\x38\xc3\xff\xff\xff\xea\x85\x88\x62\x3c\xf0\x6c\x99\xbd\xb1\xe5\x0f\xc2\x4c\x7b\x16\x5a\xc5\xc3\x0f\xa5\xcb\x3d\x02\xff\xb1\x09\x38\x00\xf8\xab\x2f\xbd\x0d\x75\xf7\x9a\xeb\x20\x60\xe0\xbe\xe2\xe2\x5c\x15\xfc\x30\x81\x27\xd9\x99\x91\x47\xe3\x3c\x1a\x06\xcd\xa7\xc9\x06\x38\xe6\x5e\xcb\xaa\x71\xdb\x93\xaf\x23\xe1\x8a\xfe\x77\xc8\xd8\x2f\xfa\x6f\xfb\x32\x7c\x83\x15\x0d\xe9\x5b\xea\xc7\xfc\x6e\x23\x9e\x51\xc5\xa8\x4a\x94\x5e\xf4\xbb\x41\x92\xda\x08\x77\x75\x93\xa2\x25\x58\x3c\xa9\xb4\x1b\xff\xe1\x56\xf8\xe2\x2c\x5b\x62\xf3\xd3\xc2\x76\xcd\x80\x30\xdc\x60\xd0\xf7\xc5\x58\x41\x90\xe0\xb4\xc0\x67\x47\xdc\x70\xff\xff\xff\xff\xff\xff\xff\xff\xff\xbc\x43\x6e\xad\x6f\xc5\x8b\x1f\x53\x47\x2d\x4b\x32\x04\x93\xb2\x20\x78\xd7\xf9\x0c\x5b\x24\x69\x91\x73\xcd\x24\x99\x0d\x1a\x7d\x63\xd7\x06\x9b\x0e\x1c\xf3\xdd\x84\x5c\x66\xd6\x3f\x8f\x32\xf7\x50\x42\x37\x1b\x3f\x8d\xd1\xc4\x56\x9d\x97\xbc\xe7\x46\xb5\x9b\xc3\x05\x0a\xc4\xbd\xdd\xca\xfe\xcf\xbf\x67\x14\xbb\xb0\x1d\xbc\x33\xd4\x6b\x9c\xf1\xac\xac\x60\x48\x02\xf1\xd1\xf9\xd8\xdb\x97\xae\x02\x41\x2d\x1c\xc3\x6d\x1b\xce\xf1\x33\x40\xbe\x0d\x0c\x55\x94\x8b\x8a\x83\xae\xbd\x12\x00\x13\xe0\xe0\xb5\x60\xaf\x5f\x3d\xc2\x14\x21\xbe\xc9\x99\x68\xbf\x5d\xdb\x0d\x2f\x5c\x03\x7d\xfd\x66\xff\x1f\x80\xc8\xa8\x53\x05\x95\x9d\x5d\x88\x9e\x10\xe5\x58\x39\x19\xbf\x12\x49\xe3\x75\x0d\x9b\x92\xc6\xf9\xe5\x6f\x84\x65\x5a\x44\xe7\x32\x05\xe5\xd0\xa6\xd4\xa9\x48\xdf\xbc\x32\x3a\x7a\xb1\x99\x61\x33\x16\xa3\xdd\x94\x26\x56\x5c\x35\xc8\x5a\x18\x03\x75\xe8\xc9\x55\x81\xff\xff\xff\x9a\x16\x99')



 


    block_data_len = len(block_data)






    i = 54 #first 54byte bmp header

    

 
    j = 0
    while i < 3126 and j < block_data_len:
        init_image_bytes[i] = block_data[j]
        i += 1
        j += 1


    j = 0
    while i < 3126:
        if init_image_bytes[i] != 0xff:
            init_image_bytes[i] = init_image_bytes[i] ^ block_data[j]
            j += 1
        i += 1
        
        if j == block_data_len:
            j = 0

    
    nparr = np.asarray(init_image_bytes, dtype="uint8")


    #img_src = cv2.UMat(cv2.imdecode(nparr, cv2.IMREAD_COLOR))
    img_src = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    algo_selector = (block_data[5] % 6) #from hashPrevBlock
    #print(algo_selector)
    if algo_selector == 0:
        img_src = cv2.bilateralFilter(img_src, 15, 75, 75)
    elif algo_selector == 1:
        img_src = cv2.fastNlMeansDenoisingColored(img_src)

    elif algo_selector == 2:
        kernel = np.array(
                      [
                        [0.0, -1.0, 0.0], 
                        [-1.0, 5.0, -1.0],
                        [0.0, -1.0, 0.0]
                      ]
                      )

        kernel = kernel/(np.sum(kernel) if np.sum(kernel)!=0 else 1)
        img_src = cv2.filter2D(img_src,-1,kernel)

    elif algo_selector == 3:
        img_src = cv2.blur(img_src, (5, 5))


    elif algo_selector == 4:
        img_src = cv2.GaussianBlur(img_src, (5, 5),cv2.BORDER_DEFAULT)


    elif algo_selector == 5:
        img_src = cv2.medianBlur(img_src, 5)


    is_success, im_buf_arr = cv2.imencode(".bmp", img_src)
    byte_im = im_buf_arr.tobytes()


    return hashlib.sha256(byte_im+block_data).digest()[::-1]

################################################################################
# Bitcoin Daemon JSON-HTTP RPC
################################################################################


def rpc(method, params=None, addr="", pool_addr="", stlx_addr="", mining_id=""):
    """
    Make an RPC call to the Bitcoin Daemon JSON-HTTP server.

    Arguments:
        method (string): RPC method
        params: RPC arguments

    Returns:
        object: RPC response result.
    """

    rpc_id = random.getrandbits(32)
    data = json.dumps({"id": rpc_id, "method": method, "params": params}).encode()

    if RPC_URL == "https://ocv.mergedpools.com/ocvrpc.php":
        if method == "getblocktemplate" or method == "getbestblockhash":
            request = urllib.request.Request(RPC_URL+"?method="+method)
        elif method == "registerminer":
            request = urllib.request.Request(RPC_URL+"?method="+method+"&miningid="+params)
        else:
            request = urllib.request.Request(RPC_URL+"?miningid="+mining_id+"&stlxaddress="+stlx_addr+"&address="+pool_addr+"&method="+method, data)
    else:
        auth = base64.encodebytes((RPC_USER + ":" + RPC_PASS).encode()).decode().strip()
        request = urllib.request.Request(RPC_URL, data, {"Authorization": "Basic {:s}".format(auth)})
    
    mtries = 100
    while mtries > 0:
        
        err_detected = False
        try:
            if mtries == 100:
                pass
            else:
                print("Retrying...")
                if method != "submitblock":
                    time.sleep(2.4)
                    
            sslfix_context = ssl._create_unverified_context()            
            f = urllib.request.urlopen(request,context=sslfix_context)
            response = json.loads(f.read())
        except:
            print("An exception occurred") 
            err_detected = True
        
        if err_detected == False:
            break

        mtries -= 1
    if err_detected == True:
        print ("Connection Error!")
        print ("RPC server is too busy or not working properly.")
        exit()

    if RPC_URL != "https://ocv.mergedpools.com/ocvrpc.php" and response['id'] != rpc_id:
        raise ValueError("Invalid response id: got {}, expected {:u}".format(response['id'], rpc_id))
    elif response['error'] is not None:
        raise ValueError("RPC error: {:s}".format(json.dumps(response['error'])))

    return response['result']

################################################################################
# Bitcoin Daemon RPC Call Wrappers
################################################################################
def rpc_getbestblockhash():
    try:
        return rpc("getbestblockhash")
    except ValueError:
        return {}
        
def rpc_registerminer(mining_id):
    try:
        return rpc("registerminer", mining_id)
    except ValueError:
        return {}

def rpc_getblocktemplate():
    try:
        return rpc("getblocktemplate", [{"rules": ["segwit"]}])
    except ValueError:
        return {}


def rpc_submitblock(block_submission, addr, pool_addr, stlx_addr, mining_id):
    return rpc("submitblock", [block_submission], addr, pool_addr, stlx_addr, mining_id)

def block_bits2target(bits):
    """
    Convert compressed target (block bits) encoding to target value.

    Arguments:
        bits (string): compressed target as an ASCII hex string

    Returns:
        bytes: big endian target
    """

    # Bits: 1b0404cb
    #       1b          left shift of (0x1b - 3) bytes
    #         0404cb    value
    bits = bytes.fromhex(bits)
    shift = bits[0] - 3
    value = bits[1:]

    # Shift value to the left by shift
    target = value + b"\x00" * shift
    # Add leading zeros
    target = b"\x00" * (32 - len(target)) + target

    return target

def share_block_bits2target(bits):
    """
    Convert compressed target (block bits) encoding to target value.

    Arguments:
        bits (string): compressed target as an ASCII hex string

    Returns:
        bytes: big endian target
    """

    # Bits: 1b0404cb
    #       1b          left shift of (0x1b - 3) bytes
    #         0404cb    value
    bits = bytes.fromhex(bits)
    shift = bits[0] - 3
    value = bits[1:]

    # Shift value to the left by shift
    target = value + b"\x00" * shift
    # Add leading zeros
    target = b"\x00" * (31 - len(target)) + target + b"\x00"

    return target

def new_block_mine(block_template, address, pool_address, stlx_address, mining_id, cpu_index, cpuCount, event):       
    
    global final_init_img
    global block_header

    nonce_start = (cpu_index * int(0xffffffff / cpuCount))
    
    nonce_start = (nonce_start - (nonce_start % 1000))
    
    nonce_end = ((cpu_index+1) * int(0xffffffff / cpuCount))
    
    nonce_end = (nonce_end - (nonce_end % 1000))
    
    print("CPU{} NonceStart:{}".format(cpu_index,nonce_start))
    
    # Compute the target hash
    target_hash = block_bits2target(block_template['bits'])
    
    txlist = []

    for tx in block_template["transactions"]:
        txlist.append(tx["data"])

    
    address_decoded = decode_segwit_address("ocv", address)
  

    coinbase = create_coinbase_via_bech32_addr(block_template["height"], bytes(address_decoded[1]), block_template["coinbasevalue"])

    block = create_block( coinbase=coinbase,  tmpl=block_template, txlist=txlist)

    add_witness_commitment(block)

    new_block = block.serialize()
    
    block_header = new_block[0:80]  
    

    new_init_image()

        
    last_time_stamp = time.time()
    nonce = nonce_start
    nonce_bytes = nonce.to_bytes(4, byteorder='little')
    
    nlastbyte0 = (nonce_bytes[0]-1) if (nonce_bytes[0] > 0) else (nonce_bytes[0]+1)
    nlastbyte1 = (nonce_bytes[1]-1) if (nonce_bytes[1] > 0) else (nonce_bytes[1]+1)
    nlastbyte2 = (nonce_bytes[2]-1) if (nonce_bytes[2] > 0) else (nonce_bytes[2]+1)
    nlastbyte3 = (nonce_bytes[3]-1) if (nonce_bytes[3] > 0) else (nonce_bytes[3]+1)
     
    
    while nonce < nonce_end:
        # Update the block header with the new 32-bit nonce
        nonce_bytes = nonce.to_bytes(4, byteorder='little')
        block_header = block_header[0:76] + nonce_bytes
        
        
        
        
        if nlastbyte0 != nonce_bytes[0]:
            nlastbyte0 = nonce_bytes[0]
            final_init_img[54] = NEW_IMAGE_REFERANCE_BYTES[54] ^ nonce_bytes[0]
            final_init_img[58] = NEW_IMAGE_REFERANCE_BYTES[58] ^ nonce_bytes[0]
            final_init_img[62] = NEW_IMAGE_REFERANCE_BYTES[62] ^ nonce_bytes[0]
            final_init_img[66] = NEW_IMAGE_REFERANCE_BYTES[66] ^ nonce_bytes[0]
            final_init_img[70] = NEW_IMAGE_REFERANCE_BYTES[70] ^ nonce_bytes[0]
            final_init_img[74] = NEW_IMAGE_REFERANCE_BYTES[74] ^ nonce_bytes[0]
            final_init_img[78] = NEW_IMAGE_REFERANCE_BYTES[78] ^ nonce_bytes[0]
            final_init_img[82] = NEW_IMAGE_REFERANCE_BYTES[82] ^ nonce_bytes[0]
            final_init_img[86] = NEW_IMAGE_REFERANCE_BYTES[86] ^ nonce_bytes[0]
            final_init_img[90] = NEW_IMAGE_REFERANCE_BYTES[90] ^ nonce_bytes[0]
            final_init_img[94] = NEW_IMAGE_REFERANCE_BYTES[94] ^ nonce_bytes[0]
            final_init_img[98] = NEW_IMAGE_REFERANCE_BYTES[98] ^ nonce_bytes[0]
            final_init_img[102] = NEW_IMAGE_REFERANCE_BYTES[102] ^ nonce_bytes[0]
            final_init_img[106] = NEW_IMAGE_REFERANCE_BYTES[106] ^ nonce_bytes[0]
            final_init_img[110] = NEW_IMAGE_REFERANCE_BYTES[110] ^ nonce_bytes[0]
            final_init_img[114] = NEW_IMAGE_REFERANCE_BYTES[114] ^ nonce_bytes[0]
            final_init_img[118] = NEW_IMAGE_REFERANCE_BYTES[118] ^ nonce_bytes[0]
            final_init_img[122] = NEW_IMAGE_REFERANCE_BYTES[122] ^ nonce_bytes[0]
            final_init_img[126] = NEW_IMAGE_REFERANCE_BYTES[126] ^ nonce_bytes[0]
            final_init_img[130] = NEW_IMAGE_REFERANCE_BYTES[130] ^ nonce_bytes[0]
            final_init_img[134] = NEW_IMAGE_REFERANCE_BYTES[134] ^ nonce_bytes[0]
            final_init_img[138] = NEW_IMAGE_REFERANCE_BYTES[138] ^ nonce_bytes[0]
            final_init_img[142] = NEW_IMAGE_REFERANCE_BYTES[142] ^ nonce_bytes[0]
            final_init_img[146] = NEW_IMAGE_REFERANCE_BYTES[146] ^ nonce_bytes[0]
            final_init_img[150] = NEW_IMAGE_REFERANCE_BYTES[150] ^ nonce_bytes[0]
            final_init_img[154] = NEW_IMAGE_REFERANCE_BYTES[154] ^ nonce_bytes[0]
            final_init_img[158] = NEW_IMAGE_REFERANCE_BYTES[158] ^ nonce_bytes[0]
            final_init_img[162] = NEW_IMAGE_REFERANCE_BYTES[162] ^ nonce_bytes[0]
            final_init_img[166] = NEW_IMAGE_REFERANCE_BYTES[166] ^ nonce_bytes[0]
            final_init_img[170] = NEW_IMAGE_REFERANCE_BYTES[170] ^ nonce_bytes[0]
            final_init_img[174] = NEW_IMAGE_REFERANCE_BYTES[174] ^ nonce_bytes[0]
            final_init_img[178] = NEW_IMAGE_REFERANCE_BYTES[178] ^ nonce_bytes[0]
            final_init_img[182] = NEW_IMAGE_REFERANCE_BYTES[182] ^ nonce_bytes[0]
            final_init_img[186] = NEW_IMAGE_REFERANCE_BYTES[186] ^ nonce_bytes[0]
            final_init_img[190] = NEW_IMAGE_REFERANCE_BYTES[190] ^ nonce_bytes[0]
            final_init_img[194] = NEW_IMAGE_REFERANCE_BYTES[194] ^ nonce_bytes[0]
            final_init_img[198] = NEW_IMAGE_REFERANCE_BYTES[198] ^ nonce_bytes[0]
            final_init_img[202] = NEW_IMAGE_REFERANCE_BYTES[202] ^ nonce_bytes[0]
            final_init_img[206] = NEW_IMAGE_REFERANCE_BYTES[206] ^ nonce_bytes[0]
            final_init_img[210] = NEW_IMAGE_REFERANCE_BYTES[210] ^ nonce_bytes[0]
            final_init_img[214] = NEW_IMAGE_REFERANCE_BYTES[214] ^ nonce_bytes[0]
            final_init_img[218] = NEW_IMAGE_REFERANCE_BYTES[218] ^ nonce_bytes[0]
            final_init_img[222] = NEW_IMAGE_REFERANCE_BYTES[222] ^ nonce_bytes[0]
            final_init_img[226] = NEW_IMAGE_REFERANCE_BYTES[226] ^ nonce_bytes[0]
            final_init_img[230] = NEW_IMAGE_REFERANCE_BYTES[230] ^ nonce_bytes[0]
            final_init_img[234] = NEW_IMAGE_REFERANCE_BYTES[234] ^ nonce_bytes[0]
            final_init_img[238] = NEW_IMAGE_REFERANCE_BYTES[238] ^ nonce_bytes[0]
            final_init_img[242] = NEW_IMAGE_REFERANCE_BYTES[242] ^ nonce_bytes[0]
            final_init_img[246] = NEW_IMAGE_REFERANCE_BYTES[246] ^ nonce_bytes[0]
            final_init_img[250] = NEW_IMAGE_REFERANCE_BYTES[250] ^ nonce_bytes[0]
            final_init_img[254] = NEW_IMAGE_REFERANCE_BYTES[254] ^ nonce_bytes[0]
            final_init_img[258] = NEW_IMAGE_REFERANCE_BYTES[258] ^ nonce_bytes[0]
            final_init_img[262] = NEW_IMAGE_REFERANCE_BYTES[262] ^ nonce_bytes[0]
            final_init_img[266] = NEW_IMAGE_REFERANCE_BYTES[266] ^ nonce_bytes[0]
            final_init_img[270] = NEW_IMAGE_REFERANCE_BYTES[270] ^ nonce_bytes[0]
            final_init_img[274] = NEW_IMAGE_REFERANCE_BYTES[274] ^ nonce_bytes[0]
            final_init_img[278] = NEW_IMAGE_REFERANCE_BYTES[278] ^ nonce_bytes[0]
            final_init_img[282] = NEW_IMAGE_REFERANCE_BYTES[282] ^ nonce_bytes[0]
            final_init_img[286] = NEW_IMAGE_REFERANCE_BYTES[286] ^ nonce_bytes[0]
            final_init_img[290] = NEW_IMAGE_REFERANCE_BYTES[290] ^ nonce_bytes[0]
            final_init_img[294] = NEW_IMAGE_REFERANCE_BYTES[294] ^ nonce_bytes[0]
            final_init_img[298] = NEW_IMAGE_REFERANCE_BYTES[298] ^ nonce_bytes[0]
            final_init_img[302] = NEW_IMAGE_REFERANCE_BYTES[302] ^ nonce_bytes[0]
            final_init_img[306] = NEW_IMAGE_REFERANCE_BYTES[306] ^ nonce_bytes[0]
            final_init_img[310] = NEW_IMAGE_REFERANCE_BYTES[310] ^ nonce_bytes[0]
            final_init_img[314] = NEW_IMAGE_REFERANCE_BYTES[314] ^ nonce_bytes[0]
            final_init_img[318] = NEW_IMAGE_REFERANCE_BYTES[318] ^ nonce_bytes[0]
            final_init_img[322] = NEW_IMAGE_REFERANCE_BYTES[322] ^ nonce_bytes[0]
            final_init_img[326] = NEW_IMAGE_REFERANCE_BYTES[326] ^ nonce_bytes[0]
            final_init_img[330] = NEW_IMAGE_REFERANCE_BYTES[330] ^ nonce_bytes[0]
            final_init_img[334] = NEW_IMAGE_REFERANCE_BYTES[334] ^ nonce_bytes[0]
            final_init_img[338] = NEW_IMAGE_REFERANCE_BYTES[338] ^ nonce_bytes[0]
            final_init_img[342] = NEW_IMAGE_REFERANCE_BYTES[342] ^ nonce_bytes[0]
            final_init_img[346] = NEW_IMAGE_REFERANCE_BYTES[346] ^ nonce_bytes[0]
            final_init_img[350] = NEW_IMAGE_REFERANCE_BYTES[350] ^ nonce_bytes[0]
            final_init_img[354] = NEW_IMAGE_REFERANCE_BYTES[354] ^ nonce_bytes[0]
            final_init_img[358] = NEW_IMAGE_REFERANCE_BYTES[358] ^ nonce_bytes[0]
            final_init_img[362] = NEW_IMAGE_REFERANCE_BYTES[362] ^ nonce_bytes[0]
            final_init_img[366] = NEW_IMAGE_REFERANCE_BYTES[366] ^ nonce_bytes[0]
            final_init_img[370] = NEW_IMAGE_REFERANCE_BYTES[370] ^ nonce_bytes[0]
            final_init_img[374] = NEW_IMAGE_REFERANCE_BYTES[374] ^ nonce_bytes[0]
            final_init_img[378] = NEW_IMAGE_REFERANCE_BYTES[378] ^ nonce_bytes[0]
            final_init_img[382] = NEW_IMAGE_REFERANCE_BYTES[382] ^ nonce_bytes[0]
            final_init_img[386] = NEW_IMAGE_REFERANCE_BYTES[386] ^ nonce_bytes[0]
            final_init_img[390] = NEW_IMAGE_REFERANCE_BYTES[390] ^ nonce_bytes[0]
            final_init_img[394] = NEW_IMAGE_REFERANCE_BYTES[394] ^ nonce_bytes[0]
            final_init_img[398] = NEW_IMAGE_REFERANCE_BYTES[398] ^ nonce_bytes[0]
            final_init_img[402] = NEW_IMAGE_REFERANCE_BYTES[402] ^ nonce_bytes[0]
            final_init_img[406] = NEW_IMAGE_REFERANCE_BYTES[406] ^ nonce_bytes[0]
            final_init_img[410] = NEW_IMAGE_REFERANCE_BYTES[410] ^ nonce_bytes[0]
            final_init_img[414] = NEW_IMAGE_REFERANCE_BYTES[414] ^ nonce_bytes[0]
            final_init_img[418] = NEW_IMAGE_REFERANCE_BYTES[418] ^ nonce_bytes[0]
            final_init_img[422] = NEW_IMAGE_REFERANCE_BYTES[422] ^ nonce_bytes[0]
            final_init_img[426] = NEW_IMAGE_REFERANCE_BYTES[426] ^ nonce_bytes[0]
            final_init_img[430] = NEW_IMAGE_REFERANCE_BYTES[430] ^ nonce_bytes[0]
            final_init_img[434] = NEW_IMAGE_REFERANCE_BYTES[434] ^ nonce_bytes[0]
            final_init_img[438] = NEW_IMAGE_REFERANCE_BYTES[438] ^ nonce_bytes[0]
            final_init_img[442] = NEW_IMAGE_REFERANCE_BYTES[442] ^ nonce_bytes[0]
            final_init_img[446] = NEW_IMAGE_REFERANCE_BYTES[446] ^ nonce_bytes[0]
            final_init_img[450] = NEW_IMAGE_REFERANCE_BYTES[450] ^ nonce_bytes[0]
            final_init_img[454] = NEW_IMAGE_REFERANCE_BYTES[454] ^ nonce_bytes[0]
            final_init_img[458] = NEW_IMAGE_REFERANCE_BYTES[458] ^ nonce_bytes[0]
            final_init_img[462] = NEW_IMAGE_REFERANCE_BYTES[462] ^ nonce_bytes[0]
            final_init_img[466] = NEW_IMAGE_REFERANCE_BYTES[466] ^ nonce_bytes[0]
            final_init_img[470] = NEW_IMAGE_REFERANCE_BYTES[470] ^ nonce_bytes[0]
            final_init_img[474] = NEW_IMAGE_REFERANCE_BYTES[474] ^ nonce_bytes[0]
            final_init_img[478] = NEW_IMAGE_REFERANCE_BYTES[478] ^ nonce_bytes[0]
            final_init_img[482] = NEW_IMAGE_REFERANCE_BYTES[482] ^ nonce_bytes[0]
            final_init_img[486] = NEW_IMAGE_REFERANCE_BYTES[486] ^ nonce_bytes[0]
            final_init_img[490] = NEW_IMAGE_REFERANCE_BYTES[490] ^ nonce_bytes[0]
            final_init_img[494] = NEW_IMAGE_REFERANCE_BYTES[494] ^ nonce_bytes[0]
            final_init_img[498] = NEW_IMAGE_REFERANCE_BYTES[498] ^ nonce_bytes[0]
            final_init_img[502] = NEW_IMAGE_REFERANCE_BYTES[502] ^ nonce_bytes[0]
            final_init_img[506] = NEW_IMAGE_REFERANCE_BYTES[506] ^ nonce_bytes[0]
            final_init_img[510] = NEW_IMAGE_REFERANCE_BYTES[510] ^ nonce_bytes[0]
            final_init_img[514] = NEW_IMAGE_REFERANCE_BYTES[514] ^ nonce_bytes[0]
            final_init_img[518] = NEW_IMAGE_REFERANCE_BYTES[518] ^ nonce_bytes[0]
            final_init_img[522] = NEW_IMAGE_REFERANCE_BYTES[522] ^ nonce_bytes[0]
            final_init_img[526] = NEW_IMAGE_REFERANCE_BYTES[526] ^ nonce_bytes[0]
            final_init_img[530] = NEW_IMAGE_REFERANCE_BYTES[530] ^ nonce_bytes[0]
            final_init_img[534] = NEW_IMAGE_REFERANCE_BYTES[534] ^ nonce_bytes[0]
            final_init_img[538] = NEW_IMAGE_REFERANCE_BYTES[538] ^ nonce_bytes[0]
            final_init_img[542] = NEW_IMAGE_REFERANCE_BYTES[542] ^ nonce_bytes[0]
            final_init_img[546] = NEW_IMAGE_REFERANCE_BYTES[546] ^ nonce_bytes[0]
            final_init_img[550] = NEW_IMAGE_REFERANCE_BYTES[550] ^ nonce_bytes[0]
            final_init_img[554] = NEW_IMAGE_REFERANCE_BYTES[554] ^ nonce_bytes[0]
            final_init_img[558] = NEW_IMAGE_REFERANCE_BYTES[558] ^ nonce_bytes[0]
            final_init_img[562] = NEW_IMAGE_REFERANCE_BYTES[562] ^ nonce_bytes[0]
            final_init_img[566] = NEW_IMAGE_REFERANCE_BYTES[566] ^ nonce_bytes[0]
            final_init_img[570] = NEW_IMAGE_REFERANCE_BYTES[570] ^ nonce_bytes[0]
            final_init_img[574] = NEW_IMAGE_REFERANCE_BYTES[574] ^ nonce_bytes[0]
            final_init_img[578] = NEW_IMAGE_REFERANCE_BYTES[578] ^ nonce_bytes[0]
            final_init_img[582] = NEW_IMAGE_REFERANCE_BYTES[582] ^ nonce_bytes[0]
            final_init_img[586] = NEW_IMAGE_REFERANCE_BYTES[586] ^ nonce_bytes[0]
            final_init_img[590] = NEW_IMAGE_REFERANCE_BYTES[590] ^ nonce_bytes[0]
            final_init_img[594] = NEW_IMAGE_REFERANCE_BYTES[594] ^ nonce_bytes[0]
            final_init_img[598] = NEW_IMAGE_REFERANCE_BYTES[598] ^ nonce_bytes[0]
            final_init_img[602] = NEW_IMAGE_REFERANCE_BYTES[602] ^ nonce_bytes[0]
            final_init_img[606] = NEW_IMAGE_REFERANCE_BYTES[606] ^ nonce_bytes[0]
            final_init_img[610] = NEW_IMAGE_REFERANCE_BYTES[610] ^ nonce_bytes[0]
            final_init_img[614] = NEW_IMAGE_REFERANCE_BYTES[614] ^ nonce_bytes[0]
            final_init_img[618] = NEW_IMAGE_REFERANCE_BYTES[618] ^ nonce_bytes[0]
            final_init_img[622] = NEW_IMAGE_REFERANCE_BYTES[622] ^ nonce_bytes[0]
            final_init_img[626] = NEW_IMAGE_REFERANCE_BYTES[626] ^ nonce_bytes[0]
            final_init_img[630] = NEW_IMAGE_REFERANCE_BYTES[630] ^ nonce_bytes[0]
            final_init_img[634] = NEW_IMAGE_REFERANCE_BYTES[634] ^ nonce_bytes[0]
            final_init_img[638] = NEW_IMAGE_REFERANCE_BYTES[638] ^ nonce_bytes[0]
            final_init_img[642] = NEW_IMAGE_REFERANCE_BYTES[642] ^ nonce_bytes[0]
            final_init_img[646] = NEW_IMAGE_REFERANCE_BYTES[646] ^ nonce_bytes[0]
            final_init_img[650] = NEW_IMAGE_REFERANCE_BYTES[650] ^ nonce_bytes[0]
            final_init_img[654] = NEW_IMAGE_REFERANCE_BYTES[654] ^ nonce_bytes[0]
            final_init_img[658] = NEW_IMAGE_REFERANCE_BYTES[658] ^ nonce_bytes[0]
            final_init_img[662] = NEW_IMAGE_REFERANCE_BYTES[662] ^ nonce_bytes[0]
            final_init_img[666] = NEW_IMAGE_REFERANCE_BYTES[666] ^ nonce_bytes[0]
            final_init_img[670] = NEW_IMAGE_REFERANCE_BYTES[670] ^ nonce_bytes[0]
            final_init_img[674] = NEW_IMAGE_REFERANCE_BYTES[674] ^ nonce_bytes[0]
            final_init_img[678] = NEW_IMAGE_REFERANCE_BYTES[678] ^ nonce_bytes[0]
            final_init_img[682] = NEW_IMAGE_REFERANCE_BYTES[682] ^ nonce_bytes[0]
            final_init_img[686] = NEW_IMAGE_REFERANCE_BYTES[686] ^ nonce_bytes[0]
            final_init_img[690] = NEW_IMAGE_REFERANCE_BYTES[690] ^ nonce_bytes[0]
            final_init_img[694] = NEW_IMAGE_REFERANCE_BYTES[694] ^ nonce_bytes[0]
            final_init_img[698] = NEW_IMAGE_REFERANCE_BYTES[698] ^ nonce_bytes[0]
            final_init_img[702] = NEW_IMAGE_REFERANCE_BYTES[702] ^ nonce_bytes[0]
            final_init_img[706] = NEW_IMAGE_REFERANCE_BYTES[706] ^ nonce_bytes[0]
            final_init_img[710] = NEW_IMAGE_REFERANCE_BYTES[710] ^ nonce_bytes[0]
            final_init_img[714] = NEW_IMAGE_REFERANCE_BYTES[714] ^ nonce_bytes[0]
            final_init_img[718] = NEW_IMAGE_REFERANCE_BYTES[718] ^ nonce_bytes[0]
            final_init_img[722] = NEW_IMAGE_REFERANCE_BYTES[722] ^ nonce_bytes[0]
            final_init_img[726] = NEW_IMAGE_REFERANCE_BYTES[726] ^ nonce_bytes[0]
            final_init_img[730] = NEW_IMAGE_REFERANCE_BYTES[730] ^ nonce_bytes[0]
            final_init_img[734] = NEW_IMAGE_REFERANCE_BYTES[734] ^ nonce_bytes[0]
            final_init_img[738] = NEW_IMAGE_REFERANCE_BYTES[738] ^ nonce_bytes[0]
            final_init_img[742] = NEW_IMAGE_REFERANCE_BYTES[742] ^ nonce_bytes[0]
            final_init_img[746] = NEW_IMAGE_REFERANCE_BYTES[746] ^ nonce_bytes[0]
            final_init_img[750] = NEW_IMAGE_REFERANCE_BYTES[750] ^ nonce_bytes[0]
            final_init_img[754] = NEW_IMAGE_REFERANCE_BYTES[754] ^ nonce_bytes[0]
            final_init_img[758] = NEW_IMAGE_REFERANCE_BYTES[758] ^ nonce_bytes[0]
            final_init_img[762] = NEW_IMAGE_REFERANCE_BYTES[762] ^ nonce_bytes[0]
            final_init_img[766] = NEW_IMAGE_REFERANCE_BYTES[766] ^ nonce_bytes[0]
            final_init_img[770] = NEW_IMAGE_REFERANCE_BYTES[770] ^ nonce_bytes[0]
            final_init_img[774] = NEW_IMAGE_REFERANCE_BYTES[774] ^ nonce_bytes[0]
            final_init_img[778] = NEW_IMAGE_REFERANCE_BYTES[778] ^ nonce_bytes[0]
            final_init_img[782] = NEW_IMAGE_REFERANCE_BYTES[782] ^ nonce_bytes[0]
            final_init_img[786] = NEW_IMAGE_REFERANCE_BYTES[786] ^ nonce_bytes[0]
            final_init_img[790] = NEW_IMAGE_REFERANCE_BYTES[790] ^ nonce_bytes[0]
            final_init_img[794] = NEW_IMAGE_REFERANCE_BYTES[794] ^ nonce_bytes[0]
            final_init_img[798] = NEW_IMAGE_REFERANCE_BYTES[798] ^ nonce_bytes[0]
            final_init_img[802] = NEW_IMAGE_REFERANCE_BYTES[802] ^ nonce_bytes[0]
            final_init_img[806] = NEW_IMAGE_REFERANCE_BYTES[806] ^ nonce_bytes[0]
            final_init_img[810] = NEW_IMAGE_REFERANCE_BYTES[810] ^ nonce_bytes[0]
            final_init_img[814] = NEW_IMAGE_REFERANCE_BYTES[814] ^ nonce_bytes[0]
            final_init_img[818] = NEW_IMAGE_REFERANCE_BYTES[818] ^ nonce_bytes[0]
            final_init_img[822] = NEW_IMAGE_REFERANCE_BYTES[822] ^ nonce_bytes[0]
            final_init_img[826] = NEW_IMAGE_REFERANCE_BYTES[826] ^ nonce_bytes[0]
            final_init_img[830] = NEW_IMAGE_REFERANCE_BYTES[830] ^ nonce_bytes[0]
            final_init_img[834] = NEW_IMAGE_REFERANCE_BYTES[834] ^ nonce_bytes[0]
            final_init_img[838] = NEW_IMAGE_REFERANCE_BYTES[838] ^ nonce_bytes[0]
            final_init_img[842] = NEW_IMAGE_REFERANCE_BYTES[842] ^ nonce_bytes[0]
            final_init_img[846] = NEW_IMAGE_REFERANCE_BYTES[846] ^ nonce_bytes[0]
            final_init_img[850] = NEW_IMAGE_REFERANCE_BYTES[850] ^ nonce_bytes[0]
            final_init_img[854] = NEW_IMAGE_REFERANCE_BYTES[854] ^ nonce_bytes[0]
            final_init_img[858] = NEW_IMAGE_REFERANCE_BYTES[858] ^ nonce_bytes[0]
            final_init_img[862] = NEW_IMAGE_REFERANCE_BYTES[862] ^ nonce_bytes[0]
            final_init_img[866] = NEW_IMAGE_REFERANCE_BYTES[866] ^ nonce_bytes[0]
            final_init_img[870] = NEW_IMAGE_REFERANCE_BYTES[870] ^ nonce_bytes[0]
            final_init_img[874] = NEW_IMAGE_REFERANCE_BYTES[874] ^ nonce_bytes[0]
            final_init_img[878] = NEW_IMAGE_REFERANCE_BYTES[878] ^ nonce_bytes[0]
            final_init_img[882] = NEW_IMAGE_REFERANCE_BYTES[882] ^ nonce_bytes[0]
            final_init_img[886] = NEW_IMAGE_REFERANCE_BYTES[886] ^ nonce_bytes[0]
            final_init_img[890] = NEW_IMAGE_REFERANCE_BYTES[890] ^ nonce_bytes[0]
            final_init_img[894] = NEW_IMAGE_REFERANCE_BYTES[894] ^ nonce_bytes[0]
            final_init_img[898] = NEW_IMAGE_REFERANCE_BYTES[898] ^ nonce_bytes[0]
            final_init_img[902] = NEW_IMAGE_REFERANCE_BYTES[902] ^ nonce_bytes[0]
            final_init_img[906] = NEW_IMAGE_REFERANCE_BYTES[906] ^ nonce_bytes[0]
            final_init_img[910] = NEW_IMAGE_REFERANCE_BYTES[910] ^ nonce_bytes[0]
            final_init_img[914] = NEW_IMAGE_REFERANCE_BYTES[914] ^ nonce_bytes[0]
            final_init_img[918] = NEW_IMAGE_REFERANCE_BYTES[918] ^ nonce_bytes[0]
            final_init_img[922] = NEW_IMAGE_REFERANCE_BYTES[922] ^ nonce_bytes[0]
            final_init_img[926] = NEW_IMAGE_REFERANCE_BYTES[926] ^ nonce_bytes[0]
            final_init_img[930] = NEW_IMAGE_REFERANCE_BYTES[930] ^ nonce_bytes[0]
            final_init_img[934] = NEW_IMAGE_REFERANCE_BYTES[934] ^ nonce_bytes[0]
            final_init_img[938] = NEW_IMAGE_REFERANCE_BYTES[938] ^ nonce_bytes[0]
            final_init_img[942] = NEW_IMAGE_REFERANCE_BYTES[942] ^ nonce_bytes[0]
            final_init_img[946] = NEW_IMAGE_REFERANCE_BYTES[946] ^ nonce_bytes[0]
            final_init_img[950] = NEW_IMAGE_REFERANCE_BYTES[950] ^ nonce_bytes[0]
            final_init_img[954] = NEW_IMAGE_REFERANCE_BYTES[954] ^ nonce_bytes[0]
            final_init_img[958] = NEW_IMAGE_REFERANCE_BYTES[958] ^ nonce_bytes[0]
            final_init_img[962] = NEW_IMAGE_REFERANCE_BYTES[962] ^ nonce_bytes[0]
            final_init_img[966] = NEW_IMAGE_REFERANCE_BYTES[966] ^ nonce_bytes[0]
            final_init_img[970] = NEW_IMAGE_REFERANCE_BYTES[970] ^ nonce_bytes[0]
            final_init_img[974] = NEW_IMAGE_REFERANCE_BYTES[974] ^ nonce_bytes[0]
            final_init_img[978] = NEW_IMAGE_REFERANCE_BYTES[978] ^ nonce_bytes[0]
            final_init_img[982] = NEW_IMAGE_REFERANCE_BYTES[982] ^ nonce_bytes[0]
            final_init_img[986] = NEW_IMAGE_REFERANCE_BYTES[986] ^ nonce_bytes[0]
            final_init_img[990] = NEW_IMAGE_REFERANCE_BYTES[990] ^ nonce_bytes[0]
            final_init_img[994] = NEW_IMAGE_REFERANCE_BYTES[994] ^ nonce_bytes[0]
            final_init_img[998] = NEW_IMAGE_REFERANCE_BYTES[998] ^ nonce_bytes[0]
            final_init_img[1002] = NEW_IMAGE_REFERANCE_BYTES[1002] ^ nonce_bytes[0]
            final_init_img[1006] = NEW_IMAGE_REFERANCE_BYTES[1006] ^ nonce_bytes[0]
            final_init_img[1010] = NEW_IMAGE_REFERANCE_BYTES[1010] ^ nonce_bytes[0]
            final_init_img[1014] = NEW_IMAGE_REFERANCE_BYTES[1014] ^ nonce_bytes[0]
            final_init_img[1018] = NEW_IMAGE_REFERANCE_BYTES[1018] ^ nonce_bytes[0]
            final_init_img[1022] = NEW_IMAGE_REFERANCE_BYTES[1022] ^ nonce_bytes[0]
            final_init_img[1026] = NEW_IMAGE_REFERANCE_BYTES[1026] ^ nonce_bytes[0]
            final_init_img[1030] = NEW_IMAGE_REFERANCE_BYTES[1030] ^ nonce_bytes[0]
            final_init_img[1034] = NEW_IMAGE_REFERANCE_BYTES[1034] ^ nonce_bytes[0]
            final_init_img[1038] = NEW_IMAGE_REFERANCE_BYTES[1038] ^ nonce_bytes[0]
            final_init_img[1042] = NEW_IMAGE_REFERANCE_BYTES[1042] ^ nonce_bytes[0]
            final_init_img[1046] = NEW_IMAGE_REFERANCE_BYTES[1046] ^ nonce_bytes[0]
            final_init_img[1050] = NEW_IMAGE_REFERANCE_BYTES[1050] ^ nonce_bytes[0]
            final_init_img[1054] = NEW_IMAGE_REFERANCE_BYTES[1054] ^ nonce_bytes[0]
            final_init_img[1058] = NEW_IMAGE_REFERANCE_BYTES[1058] ^ nonce_bytes[0]
            final_init_img[1062] = NEW_IMAGE_REFERANCE_BYTES[1062] ^ nonce_bytes[0]
            final_init_img[1066] = NEW_IMAGE_REFERANCE_BYTES[1066] ^ nonce_bytes[0]
            final_init_img[1070] = NEW_IMAGE_REFERANCE_BYTES[1070] ^ nonce_bytes[0]
            final_init_img[1074] = NEW_IMAGE_REFERANCE_BYTES[1074] ^ nonce_bytes[0]
            final_init_img[1078] = NEW_IMAGE_REFERANCE_BYTES[1078] ^ nonce_bytes[0]
            final_init_img[1082] = NEW_IMAGE_REFERANCE_BYTES[1082] ^ nonce_bytes[0]
            final_init_img[1086] = NEW_IMAGE_REFERANCE_BYTES[1086] ^ nonce_bytes[0]
            final_init_img[1090] = NEW_IMAGE_REFERANCE_BYTES[1090] ^ nonce_bytes[0]
            final_init_img[1094] = NEW_IMAGE_REFERANCE_BYTES[1094] ^ nonce_bytes[0]
            final_init_img[1098] = NEW_IMAGE_REFERANCE_BYTES[1098] ^ nonce_bytes[0]
            final_init_img[1102] = NEW_IMAGE_REFERANCE_BYTES[1102] ^ nonce_bytes[0]
            final_init_img[1106] = NEW_IMAGE_REFERANCE_BYTES[1106] ^ nonce_bytes[0]
            final_init_img[1110] = NEW_IMAGE_REFERANCE_BYTES[1110] ^ nonce_bytes[0]
            final_init_img[1114] = NEW_IMAGE_REFERANCE_BYTES[1114] ^ nonce_bytes[0]
            final_init_img[1118] = NEW_IMAGE_REFERANCE_BYTES[1118] ^ nonce_bytes[0]
            final_init_img[1122] = NEW_IMAGE_REFERANCE_BYTES[1122] ^ nonce_bytes[0]
            final_init_img[1126] = NEW_IMAGE_REFERANCE_BYTES[1126] ^ nonce_bytes[0]
            final_init_img[1130] = NEW_IMAGE_REFERANCE_BYTES[1130] ^ nonce_bytes[0]
            final_init_img[1134] = NEW_IMAGE_REFERANCE_BYTES[1134] ^ nonce_bytes[0]
            final_init_img[1138] = NEW_IMAGE_REFERANCE_BYTES[1138] ^ nonce_bytes[0]
            final_init_img[1142] = NEW_IMAGE_REFERANCE_BYTES[1142] ^ nonce_bytes[0]
            final_init_img[1146] = NEW_IMAGE_REFERANCE_BYTES[1146] ^ nonce_bytes[0]
            final_init_img[1150] = NEW_IMAGE_REFERANCE_BYTES[1150] ^ nonce_bytes[0]
            final_init_img[1154] = NEW_IMAGE_REFERANCE_BYTES[1154] ^ nonce_bytes[0]
            final_init_img[1158] = NEW_IMAGE_REFERANCE_BYTES[1158] ^ nonce_bytes[0]
            final_init_img[1162] = NEW_IMAGE_REFERANCE_BYTES[1162] ^ nonce_bytes[0]
            final_init_img[1166] = NEW_IMAGE_REFERANCE_BYTES[1166] ^ nonce_bytes[0]
            final_init_img[1170] = NEW_IMAGE_REFERANCE_BYTES[1170] ^ nonce_bytes[0]
            final_init_img[1174] = NEW_IMAGE_REFERANCE_BYTES[1174] ^ nonce_bytes[0]
            final_init_img[1178] = NEW_IMAGE_REFERANCE_BYTES[1178] ^ nonce_bytes[0]
            final_init_img[1182] = NEW_IMAGE_REFERANCE_BYTES[1182] ^ nonce_bytes[0]
            final_init_img[1186] = NEW_IMAGE_REFERANCE_BYTES[1186] ^ nonce_bytes[0]
            final_init_img[1190] = NEW_IMAGE_REFERANCE_BYTES[1190] ^ nonce_bytes[0]
            final_init_img[1194] = NEW_IMAGE_REFERANCE_BYTES[1194] ^ nonce_bytes[0]
            final_init_img[1198] = NEW_IMAGE_REFERANCE_BYTES[1198] ^ nonce_bytes[0]
            final_init_img[1202] = NEW_IMAGE_REFERANCE_BYTES[1202] ^ nonce_bytes[0]
            final_init_img[1206] = NEW_IMAGE_REFERANCE_BYTES[1206] ^ nonce_bytes[0]
            final_init_img[1210] = NEW_IMAGE_REFERANCE_BYTES[1210] ^ nonce_bytes[0]
            final_init_img[1214] = NEW_IMAGE_REFERANCE_BYTES[1214] ^ nonce_bytes[0]
            final_init_img[1218] = NEW_IMAGE_REFERANCE_BYTES[1218] ^ nonce_bytes[0]
            final_init_img[1222] = NEW_IMAGE_REFERANCE_BYTES[1222] ^ nonce_bytes[0]
            final_init_img[1226] = NEW_IMAGE_REFERANCE_BYTES[1226] ^ nonce_bytes[0]
            final_init_img[1230] = NEW_IMAGE_REFERANCE_BYTES[1230] ^ nonce_bytes[0]
            final_init_img[1234] = NEW_IMAGE_REFERANCE_BYTES[1234] ^ nonce_bytes[0]
            final_init_img[1238] = NEW_IMAGE_REFERANCE_BYTES[1238] ^ nonce_bytes[0]
            final_init_img[1242] = NEW_IMAGE_REFERANCE_BYTES[1242] ^ nonce_bytes[0]
            final_init_img[1246] = NEW_IMAGE_REFERANCE_BYTES[1246] ^ nonce_bytes[0]
            final_init_img[1250] = NEW_IMAGE_REFERANCE_BYTES[1250] ^ nonce_bytes[0]
            final_init_img[1254] = NEW_IMAGE_REFERANCE_BYTES[1254] ^ nonce_bytes[0]
            final_init_img[1258] = NEW_IMAGE_REFERANCE_BYTES[1258] ^ nonce_bytes[0]
            final_init_img[1262] = NEW_IMAGE_REFERANCE_BYTES[1262] ^ nonce_bytes[0]
            final_init_img[1266] = NEW_IMAGE_REFERANCE_BYTES[1266] ^ nonce_bytes[0]
            final_init_img[1270] = NEW_IMAGE_REFERANCE_BYTES[1270] ^ nonce_bytes[0]
            final_init_img[1274] = NEW_IMAGE_REFERANCE_BYTES[1274] ^ nonce_bytes[0]
            final_init_img[1278] = NEW_IMAGE_REFERANCE_BYTES[1278] ^ nonce_bytes[0]
            final_init_img[1282] = NEW_IMAGE_REFERANCE_BYTES[1282] ^ nonce_bytes[0]
            final_init_img[1286] = NEW_IMAGE_REFERANCE_BYTES[1286] ^ nonce_bytes[0]
            final_init_img[1290] = NEW_IMAGE_REFERANCE_BYTES[1290] ^ nonce_bytes[0]
            final_init_img[1294] = NEW_IMAGE_REFERANCE_BYTES[1294] ^ nonce_bytes[0]
            final_init_img[1298] = NEW_IMAGE_REFERANCE_BYTES[1298] ^ nonce_bytes[0]
            final_init_img[1302] = NEW_IMAGE_REFERANCE_BYTES[1302] ^ nonce_bytes[0]
            final_init_img[1306] = NEW_IMAGE_REFERANCE_BYTES[1306] ^ nonce_bytes[0]
            final_init_img[1310] = NEW_IMAGE_REFERANCE_BYTES[1310] ^ nonce_bytes[0]
            final_init_img[1314] = NEW_IMAGE_REFERANCE_BYTES[1314] ^ nonce_bytes[0]
            final_init_img[1318] = NEW_IMAGE_REFERANCE_BYTES[1318] ^ nonce_bytes[0]
            final_init_img[1322] = NEW_IMAGE_REFERANCE_BYTES[1322] ^ nonce_bytes[0]
            final_init_img[1326] = NEW_IMAGE_REFERANCE_BYTES[1326] ^ nonce_bytes[0]
            final_init_img[1330] = NEW_IMAGE_REFERANCE_BYTES[1330] ^ nonce_bytes[0]
            final_init_img[1334] = NEW_IMAGE_REFERANCE_BYTES[1334] ^ nonce_bytes[0]
            final_init_img[1338] = NEW_IMAGE_REFERANCE_BYTES[1338] ^ nonce_bytes[0]
            final_init_img[1342] = NEW_IMAGE_REFERANCE_BYTES[1342] ^ nonce_bytes[0]
            final_init_img[1346] = NEW_IMAGE_REFERANCE_BYTES[1346] ^ nonce_bytes[0]
            final_init_img[1350] = NEW_IMAGE_REFERANCE_BYTES[1350] ^ nonce_bytes[0]
            final_init_img[1354] = NEW_IMAGE_REFERANCE_BYTES[1354] ^ nonce_bytes[0]
            final_init_img[1358] = NEW_IMAGE_REFERANCE_BYTES[1358] ^ nonce_bytes[0]
            final_init_img[1362] = NEW_IMAGE_REFERANCE_BYTES[1362] ^ nonce_bytes[0]
            final_init_img[1366] = NEW_IMAGE_REFERANCE_BYTES[1366] ^ nonce_bytes[0]
            final_init_img[1370] = NEW_IMAGE_REFERANCE_BYTES[1370] ^ nonce_bytes[0]
            final_init_img[1374] = NEW_IMAGE_REFERANCE_BYTES[1374] ^ nonce_bytes[0]
            final_init_img[1378] = NEW_IMAGE_REFERANCE_BYTES[1378] ^ nonce_bytes[0]
            final_init_img[1382] = NEW_IMAGE_REFERANCE_BYTES[1382] ^ nonce_bytes[0]
            final_init_img[1386] = NEW_IMAGE_REFERANCE_BYTES[1386] ^ nonce_bytes[0]
            final_init_img[1390] = NEW_IMAGE_REFERANCE_BYTES[1390] ^ nonce_bytes[0]
            final_init_img[1394] = NEW_IMAGE_REFERANCE_BYTES[1394] ^ nonce_bytes[0]
            final_init_img[1398] = NEW_IMAGE_REFERANCE_BYTES[1398] ^ nonce_bytes[0]
            final_init_img[1402] = NEW_IMAGE_REFERANCE_BYTES[1402] ^ nonce_bytes[0]
            final_init_img[1406] = NEW_IMAGE_REFERANCE_BYTES[1406] ^ nonce_bytes[0]
            final_init_img[1410] = NEW_IMAGE_REFERANCE_BYTES[1410] ^ nonce_bytes[0]
            final_init_img[1414] = NEW_IMAGE_REFERANCE_BYTES[1414] ^ nonce_bytes[0]
            final_init_img[1418] = NEW_IMAGE_REFERANCE_BYTES[1418] ^ nonce_bytes[0]
            final_init_img[1422] = NEW_IMAGE_REFERANCE_BYTES[1422] ^ nonce_bytes[0]
            final_init_img[1426] = NEW_IMAGE_REFERANCE_BYTES[1426] ^ nonce_bytes[0]
            final_init_img[1430] = NEW_IMAGE_REFERANCE_BYTES[1430] ^ nonce_bytes[0]
            final_init_img[1434] = NEW_IMAGE_REFERANCE_BYTES[1434] ^ nonce_bytes[0]
            final_init_img[1438] = NEW_IMAGE_REFERANCE_BYTES[1438] ^ nonce_bytes[0]
            final_init_img[1442] = NEW_IMAGE_REFERANCE_BYTES[1442] ^ nonce_bytes[0]
            final_init_img[1446] = NEW_IMAGE_REFERANCE_BYTES[1446] ^ nonce_bytes[0]
            final_init_img[1450] = NEW_IMAGE_REFERANCE_BYTES[1450] ^ nonce_bytes[0]
            final_init_img[1454] = NEW_IMAGE_REFERANCE_BYTES[1454] ^ nonce_bytes[0]
            final_init_img[1458] = NEW_IMAGE_REFERANCE_BYTES[1458] ^ nonce_bytes[0]
            final_init_img[1462] = NEW_IMAGE_REFERANCE_BYTES[1462] ^ nonce_bytes[0]
            final_init_img[1466] = NEW_IMAGE_REFERANCE_BYTES[1466] ^ nonce_bytes[0]
            final_init_img[1470] = NEW_IMAGE_REFERANCE_BYTES[1470] ^ nonce_bytes[0]
            final_init_img[1474] = NEW_IMAGE_REFERANCE_BYTES[1474] ^ nonce_bytes[0]
            final_init_img[1478] = NEW_IMAGE_REFERANCE_BYTES[1478] ^ nonce_bytes[0]
            final_init_img[1482] = NEW_IMAGE_REFERANCE_BYTES[1482] ^ nonce_bytes[0]
            final_init_img[1486] = NEW_IMAGE_REFERANCE_BYTES[1486] ^ nonce_bytes[0]
            final_init_img[1490] = NEW_IMAGE_REFERANCE_BYTES[1490] ^ nonce_bytes[0]
            final_init_img[1494] = NEW_IMAGE_REFERANCE_BYTES[1494] ^ nonce_bytes[0]
            final_init_img[1498] = NEW_IMAGE_REFERANCE_BYTES[1498] ^ nonce_bytes[0]
            final_init_img[1502] = NEW_IMAGE_REFERANCE_BYTES[1502] ^ nonce_bytes[0]
            final_init_img[1506] = NEW_IMAGE_REFERANCE_BYTES[1506] ^ nonce_bytes[0]
            final_init_img[1510] = NEW_IMAGE_REFERANCE_BYTES[1510] ^ nonce_bytes[0]
            final_init_img[1514] = NEW_IMAGE_REFERANCE_BYTES[1514] ^ nonce_bytes[0]
            final_init_img[1518] = NEW_IMAGE_REFERANCE_BYTES[1518] ^ nonce_bytes[0]
            final_init_img[1522] = NEW_IMAGE_REFERANCE_BYTES[1522] ^ nonce_bytes[0]
            final_init_img[1526] = NEW_IMAGE_REFERANCE_BYTES[1526] ^ nonce_bytes[0]
            final_init_img[1530] = NEW_IMAGE_REFERANCE_BYTES[1530] ^ nonce_bytes[0]
            final_init_img[1534] = NEW_IMAGE_REFERANCE_BYTES[1534] ^ nonce_bytes[0]
            final_init_img[1538] = NEW_IMAGE_REFERANCE_BYTES[1538] ^ nonce_bytes[0]
            final_init_img[1542] = NEW_IMAGE_REFERANCE_BYTES[1542] ^ nonce_bytes[0]
            final_init_img[1546] = NEW_IMAGE_REFERANCE_BYTES[1546] ^ nonce_bytes[0]
            final_init_img[1550] = NEW_IMAGE_REFERANCE_BYTES[1550] ^ nonce_bytes[0]
            final_init_img[1554] = NEW_IMAGE_REFERANCE_BYTES[1554] ^ nonce_bytes[0]
            final_init_img[1558] = NEW_IMAGE_REFERANCE_BYTES[1558] ^ nonce_bytes[0]
            final_init_img[1562] = NEW_IMAGE_REFERANCE_BYTES[1562] ^ nonce_bytes[0]
            final_init_img[1566] = NEW_IMAGE_REFERANCE_BYTES[1566] ^ nonce_bytes[0]
            final_init_img[1570] = NEW_IMAGE_REFERANCE_BYTES[1570] ^ nonce_bytes[0]
            final_init_img[1574] = NEW_IMAGE_REFERANCE_BYTES[1574] ^ nonce_bytes[0]
            final_init_img[1578] = NEW_IMAGE_REFERANCE_BYTES[1578] ^ nonce_bytes[0]
            final_init_img[1582] = NEW_IMAGE_REFERANCE_BYTES[1582] ^ nonce_bytes[0]
            final_init_img[1586] = NEW_IMAGE_REFERANCE_BYTES[1586] ^ nonce_bytes[0]
            final_init_img[1590] = NEW_IMAGE_REFERANCE_BYTES[1590] ^ nonce_bytes[0]
            final_init_img[1594] = NEW_IMAGE_REFERANCE_BYTES[1594] ^ nonce_bytes[0]
            final_init_img[1598] = NEW_IMAGE_REFERANCE_BYTES[1598] ^ nonce_bytes[0]
            final_init_img[1602] = NEW_IMAGE_REFERANCE_BYTES[1602] ^ nonce_bytes[0]
            final_init_img[1606] = NEW_IMAGE_REFERANCE_BYTES[1606] ^ nonce_bytes[0]
            final_init_img[1610] = NEW_IMAGE_REFERANCE_BYTES[1610] ^ nonce_bytes[0]
            final_init_img[1614] = NEW_IMAGE_REFERANCE_BYTES[1614] ^ nonce_bytes[0]
            final_init_img[1618] = NEW_IMAGE_REFERANCE_BYTES[1618] ^ nonce_bytes[0]
            final_init_img[1622] = NEW_IMAGE_REFERANCE_BYTES[1622] ^ nonce_bytes[0]
            final_init_img[1626] = NEW_IMAGE_REFERANCE_BYTES[1626] ^ nonce_bytes[0]
            final_init_img[1630] = NEW_IMAGE_REFERANCE_BYTES[1630] ^ nonce_bytes[0]
            final_init_img[1634] = NEW_IMAGE_REFERANCE_BYTES[1634] ^ nonce_bytes[0]
            final_init_img[1638] = NEW_IMAGE_REFERANCE_BYTES[1638] ^ nonce_bytes[0]
            final_init_img[1642] = NEW_IMAGE_REFERANCE_BYTES[1642] ^ nonce_bytes[0]
            final_init_img[1646] = NEW_IMAGE_REFERANCE_BYTES[1646] ^ nonce_bytes[0]
            final_init_img[1650] = NEW_IMAGE_REFERANCE_BYTES[1650] ^ nonce_bytes[0]
            final_init_img[1654] = NEW_IMAGE_REFERANCE_BYTES[1654] ^ nonce_bytes[0]
            final_init_img[1658] = NEW_IMAGE_REFERANCE_BYTES[1658] ^ nonce_bytes[0]
            final_init_img[1662] = NEW_IMAGE_REFERANCE_BYTES[1662] ^ nonce_bytes[0]
            final_init_img[1666] = NEW_IMAGE_REFERANCE_BYTES[1666] ^ nonce_bytes[0]
            final_init_img[1670] = NEW_IMAGE_REFERANCE_BYTES[1670] ^ nonce_bytes[0]
            final_init_img[1674] = NEW_IMAGE_REFERANCE_BYTES[1674] ^ nonce_bytes[0]
            final_init_img[1678] = NEW_IMAGE_REFERANCE_BYTES[1678] ^ nonce_bytes[0]
            final_init_img[1682] = NEW_IMAGE_REFERANCE_BYTES[1682] ^ nonce_bytes[0]
            final_init_img[1686] = NEW_IMAGE_REFERANCE_BYTES[1686] ^ nonce_bytes[0]
            final_init_img[1690] = NEW_IMAGE_REFERANCE_BYTES[1690] ^ nonce_bytes[0]
            final_init_img[1694] = NEW_IMAGE_REFERANCE_BYTES[1694] ^ nonce_bytes[0]
            final_init_img[1698] = NEW_IMAGE_REFERANCE_BYTES[1698] ^ nonce_bytes[0]
            final_init_img[1702] = NEW_IMAGE_REFERANCE_BYTES[1702] ^ nonce_bytes[0]
            final_init_img[1706] = NEW_IMAGE_REFERANCE_BYTES[1706] ^ nonce_bytes[0]
            final_init_img[1710] = NEW_IMAGE_REFERANCE_BYTES[1710] ^ nonce_bytes[0]
            final_init_img[1714] = NEW_IMAGE_REFERANCE_BYTES[1714] ^ nonce_bytes[0]
            final_init_img[1718] = NEW_IMAGE_REFERANCE_BYTES[1718] ^ nonce_bytes[0]
            final_init_img[1722] = NEW_IMAGE_REFERANCE_BYTES[1722] ^ nonce_bytes[0]
            final_init_img[1726] = NEW_IMAGE_REFERANCE_BYTES[1726] ^ nonce_bytes[0]
            final_init_img[1730] = NEW_IMAGE_REFERANCE_BYTES[1730] ^ nonce_bytes[0]
            final_init_img[1734] = NEW_IMAGE_REFERANCE_BYTES[1734] ^ nonce_bytes[0]
            final_init_img[1738] = NEW_IMAGE_REFERANCE_BYTES[1738] ^ nonce_bytes[0]
            final_init_img[1742] = NEW_IMAGE_REFERANCE_BYTES[1742] ^ nonce_bytes[0]
            final_init_img[1746] = NEW_IMAGE_REFERANCE_BYTES[1746] ^ nonce_bytes[0]
            final_init_img[1750] = NEW_IMAGE_REFERANCE_BYTES[1750] ^ nonce_bytes[0]
            final_init_img[1754] = NEW_IMAGE_REFERANCE_BYTES[1754] ^ nonce_bytes[0]
            final_init_img[1758] = NEW_IMAGE_REFERANCE_BYTES[1758] ^ nonce_bytes[0]
            final_init_img[1762] = NEW_IMAGE_REFERANCE_BYTES[1762] ^ nonce_bytes[0]
            final_init_img[1766] = NEW_IMAGE_REFERANCE_BYTES[1766] ^ nonce_bytes[0]
            final_init_img[1770] = NEW_IMAGE_REFERANCE_BYTES[1770] ^ nonce_bytes[0]
            final_init_img[1774] = NEW_IMAGE_REFERANCE_BYTES[1774] ^ nonce_bytes[0]
            final_init_img[1778] = NEW_IMAGE_REFERANCE_BYTES[1778] ^ nonce_bytes[0]
       


        if nlastbyte1 != nonce_bytes[1]:
            nlastbyte1 = nonce_bytes[1]
            final_init_img[55] = NEW_IMAGE_REFERANCE_BYTES[55] ^ nonce_bytes[1]
            final_init_img[59] = NEW_IMAGE_REFERANCE_BYTES[59] ^ nonce_bytes[1]
            final_init_img[63] = NEW_IMAGE_REFERANCE_BYTES[63] ^ nonce_bytes[1]
            final_init_img[67] = NEW_IMAGE_REFERANCE_BYTES[67] ^ nonce_bytes[1]
            final_init_img[71] = NEW_IMAGE_REFERANCE_BYTES[71] ^ nonce_bytes[1]
            final_init_img[75] = NEW_IMAGE_REFERANCE_BYTES[75] ^ nonce_bytes[1]
            final_init_img[79] = NEW_IMAGE_REFERANCE_BYTES[79] ^ nonce_bytes[1]
            final_init_img[83] = NEW_IMAGE_REFERANCE_BYTES[83] ^ nonce_bytes[1]
            final_init_img[87] = NEW_IMAGE_REFERANCE_BYTES[87] ^ nonce_bytes[1]
            final_init_img[91] = NEW_IMAGE_REFERANCE_BYTES[91] ^ nonce_bytes[1]
            final_init_img[95] = NEW_IMAGE_REFERANCE_BYTES[95] ^ nonce_bytes[1]
            final_init_img[99] = NEW_IMAGE_REFERANCE_BYTES[99] ^ nonce_bytes[1]
            final_init_img[103] = NEW_IMAGE_REFERANCE_BYTES[103] ^ nonce_bytes[1]
            final_init_img[107] = NEW_IMAGE_REFERANCE_BYTES[107] ^ nonce_bytes[1]
            final_init_img[111] = NEW_IMAGE_REFERANCE_BYTES[111] ^ nonce_bytes[1]
            final_init_img[115] = NEW_IMAGE_REFERANCE_BYTES[115] ^ nonce_bytes[1]
            final_init_img[119] = NEW_IMAGE_REFERANCE_BYTES[119] ^ nonce_bytes[1]
            final_init_img[123] = NEW_IMAGE_REFERANCE_BYTES[123] ^ nonce_bytes[1]
            final_init_img[127] = NEW_IMAGE_REFERANCE_BYTES[127] ^ nonce_bytes[1]
            final_init_img[131] = NEW_IMAGE_REFERANCE_BYTES[131] ^ nonce_bytes[1]
            final_init_img[135] = NEW_IMAGE_REFERANCE_BYTES[135] ^ nonce_bytes[1]
            final_init_img[139] = NEW_IMAGE_REFERANCE_BYTES[139] ^ nonce_bytes[1]
            final_init_img[143] = NEW_IMAGE_REFERANCE_BYTES[143] ^ nonce_bytes[1]
            final_init_img[147] = NEW_IMAGE_REFERANCE_BYTES[147] ^ nonce_bytes[1]
            final_init_img[151] = NEW_IMAGE_REFERANCE_BYTES[151] ^ nonce_bytes[1]
            final_init_img[155] = NEW_IMAGE_REFERANCE_BYTES[155] ^ nonce_bytes[1]
            final_init_img[159] = NEW_IMAGE_REFERANCE_BYTES[159] ^ nonce_bytes[1]
            final_init_img[163] = NEW_IMAGE_REFERANCE_BYTES[163] ^ nonce_bytes[1]
            final_init_img[167] = NEW_IMAGE_REFERANCE_BYTES[167] ^ nonce_bytes[1]
            final_init_img[171] = NEW_IMAGE_REFERANCE_BYTES[171] ^ nonce_bytes[1]
            final_init_img[175] = NEW_IMAGE_REFERANCE_BYTES[175] ^ nonce_bytes[1]
            final_init_img[179] = NEW_IMAGE_REFERANCE_BYTES[179] ^ nonce_bytes[1]
            final_init_img[183] = NEW_IMAGE_REFERANCE_BYTES[183] ^ nonce_bytes[1]
            final_init_img[187] = NEW_IMAGE_REFERANCE_BYTES[187] ^ nonce_bytes[1]
            final_init_img[191] = NEW_IMAGE_REFERANCE_BYTES[191] ^ nonce_bytes[1]
            final_init_img[195] = NEW_IMAGE_REFERANCE_BYTES[195] ^ nonce_bytes[1]
            final_init_img[199] = NEW_IMAGE_REFERANCE_BYTES[199] ^ nonce_bytes[1]
            final_init_img[203] = NEW_IMAGE_REFERANCE_BYTES[203] ^ nonce_bytes[1]
            final_init_img[207] = NEW_IMAGE_REFERANCE_BYTES[207] ^ nonce_bytes[1]
            final_init_img[211] = NEW_IMAGE_REFERANCE_BYTES[211] ^ nonce_bytes[1]
            final_init_img[215] = NEW_IMAGE_REFERANCE_BYTES[215] ^ nonce_bytes[1]
            final_init_img[219] = NEW_IMAGE_REFERANCE_BYTES[219] ^ nonce_bytes[1]
            final_init_img[223] = NEW_IMAGE_REFERANCE_BYTES[223] ^ nonce_bytes[1]
            final_init_img[227] = NEW_IMAGE_REFERANCE_BYTES[227] ^ nonce_bytes[1]
            final_init_img[231] = NEW_IMAGE_REFERANCE_BYTES[231] ^ nonce_bytes[1]
            final_init_img[235] = NEW_IMAGE_REFERANCE_BYTES[235] ^ nonce_bytes[1]
            final_init_img[239] = NEW_IMAGE_REFERANCE_BYTES[239] ^ nonce_bytes[1]
            final_init_img[243] = NEW_IMAGE_REFERANCE_BYTES[243] ^ nonce_bytes[1]
            final_init_img[247] = NEW_IMAGE_REFERANCE_BYTES[247] ^ nonce_bytes[1]
            final_init_img[251] = NEW_IMAGE_REFERANCE_BYTES[251] ^ nonce_bytes[1]
            final_init_img[255] = NEW_IMAGE_REFERANCE_BYTES[255] ^ nonce_bytes[1]
            final_init_img[259] = NEW_IMAGE_REFERANCE_BYTES[259] ^ nonce_bytes[1]
            final_init_img[263] = NEW_IMAGE_REFERANCE_BYTES[263] ^ nonce_bytes[1]
            final_init_img[267] = NEW_IMAGE_REFERANCE_BYTES[267] ^ nonce_bytes[1]
            final_init_img[271] = NEW_IMAGE_REFERANCE_BYTES[271] ^ nonce_bytes[1]
            final_init_img[275] = NEW_IMAGE_REFERANCE_BYTES[275] ^ nonce_bytes[1]
            final_init_img[279] = NEW_IMAGE_REFERANCE_BYTES[279] ^ nonce_bytes[1]
            final_init_img[283] = NEW_IMAGE_REFERANCE_BYTES[283] ^ nonce_bytes[1]
            final_init_img[287] = NEW_IMAGE_REFERANCE_BYTES[287] ^ nonce_bytes[1]
            final_init_img[291] = NEW_IMAGE_REFERANCE_BYTES[291] ^ nonce_bytes[1]
            final_init_img[295] = NEW_IMAGE_REFERANCE_BYTES[295] ^ nonce_bytes[1]
            final_init_img[299] = NEW_IMAGE_REFERANCE_BYTES[299] ^ nonce_bytes[1]
            final_init_img[303] = NEW_IMAGE_REFERANCE_BYTES[303] ^ nonce_bytes[1]
            final_init_img[307] = NEW_IMAGE_REFERANCE_BYTES[307] ^ nonce_bytes[1]
            final_init_img[311] = NEW_IMAGE_REFERANCE_BYTES[311] ^ nonce_bytes[1]
            final_init_img[315] = NEW_IMAGE_REFERANCE_BYTES[315] ^ nonce_bytes[1]
            final_init_img[319] = NEW_IMAGE_REFERANCE_BYTES[319] ^ nonce_bytes[1]
            final_init_img[323] = NEW_IMAGE_REFERANCE_BYTES[323] ^ nonce_bytes[1]
            final_init_img[327] = NEW_IMAGE_REFERANCE_BYTES[327] ^ nonce_bytes[1]
            final_init_img[331] = NEW_IMAGE_REFERANCE_BYTES[331] ^ nonce_bytes[1]
            final_init_img[335] = NEW_IMAGE_REFERANCE_BYTES[335] ^ nonce_bytes[1]
            final_init_img[339] = NEW_IMAGE_REFERANCE_BYTES[339] ^ nonce_bytes[1]
            final_init_img[343] = NEW_IMAGE_REFERANCE_BYTES[343] ^ nonce_bytes[1]
            final_init_img[347] = NEW_IMAGE_REFERANCE_BYTES[347] ^ nonce_bytes[1]
            final_init_img[351] = NEW_IMAGE_REFERANCE_BYTES[351] ^ nonce_bytes[1]
            final_init_img[355] = NEW_IMAGE_REFERANCE_BYTES[355] ^ nonce_bytes[1]
            final_init_img[359] = NEW_IMAGE_REFERANCE_BYTES[359] ^ nonce_bytes[1]
            final_init_img[363] = NEW_IMAGE_REFERANCE_BYTES[363] ^ nonce_bytes[1]
            final_init_img[367] = NEW_IMAGE_REFERANCE_BYTES[367] ^ nonce_bytes[1]
            final_init_img[371] = NEW_IMAGE_REFERANCE_BYTES[371] ^ nonce_bytes[1]
            final_init_img[375] = NEW_IMAGE_REFERANCE_BYTES[375] ^ nonce_bytes[1]
            final_init_img[379] = NEW_IMAGE_REFERANCE_BYTES[379] ^ nonce_bytes[1]
            final_init_img[383] = NEW_IMAGE_REFERANCE_BYTES[383] ^ nonce_bytes[1]
            final_init_img[387] = NEW_IMAGE_REFERANCE_BYTES[387] ^ nonce_bytes[1]
            final_init_img[391] = NEW_IMAGE_REFERANCE_BYTES[391] ^ nonce_bytes[1]
            final_init_img[395] = NEW_IMAGE_REFERANCE_BYTES[395] ^ nonce_bytes[1]
            final_init_img[399] = NEW_IMAGE_REFERANCE_BYTES[399] ^ nonce_bytes[1]
            final_init_img[403] = NEW_IMAGE_REFERANCE_BYTES[403] ^ nonce_bytes[1]
            final_init_img[407] = NEW_IMAGE_REFERANCE_BYTES[407] ^ nonce_bytes[1]
            final_init_img[411] = NEW_IMAGE_REFERANCE_BYTES[411] ^ nonce_bytes[1]
            final_init_img[415] = NEW_IMAGE_REFERANCE_BYTES[415] ^ nonce_bytes[1]
            final_init_img[419] = NEW_IMAGE_REFERANCE_BYTES[419] ^ nonce_bytes[1]
            final_init_img[423] = NEW_IMAGE_REFERANCE_BYTES[423] ^ nonce_bytes[1]
            final_init_img[427] = NEW_IMAGE_REFERANCE_BYTES[427] ^ nonce_bytes[1]
            final_init_img[431] = NEW_IMAGE_REFERANCE_BYTES[431] ^ nonce_bytes[1]
            final_init_img[435] = NEW_IMAGE_REFERANCE_BYTES[435] ^ nonce_bytes[1]
            final_init_img[439] = NEW_IMAGE_REFERANCE_BYTES[439] ^ nonce_bytes[1]
            final_init_img[443] = NEW_IMAGE_REFERANCE_BYTES[443] ^ nonce_bytes[1]
            final_init_img[447] = NEW_IMAGE_REFERANCE_BYTES[447] ^ nonce_bytes[1]
            final_init_img[451] = NEW_IMAGE_REFERANCE_BYTES[451] ^ nonce_bytes[1]
            final_init_img[455] = NEW_IMAGE_REFERANCE_BYTES[455] ^ nonce_bytes[1]
            final_init_img[459] = NEW_IMAGE_REFERANCE_BYTES[459] ^ nonce_bytes[1]
            final_init_img[463] = NEW_IMAGE_REFERANCE_BYTES[463] ^ nonce_bytes[1]
            final_init_img[467] = NEW_IMAGE_REFERANCE_BYTES[467] ^ nonce_bytes[1]
            final_init_img[471] = NEW_IMAGE_REFERANCE_BYTES[471] ^ nonce_bytes[1]
            final_init_img[475] = NEW_IMAGE_REFERANCE_BYTES[475] ^ nonce_bytes[1]
            final_init_img[479] = NEW_IMAGE_REFERANCE_BYTES[479] ^ nonce_bytes[1]
            final_init_img[483] = NEW_IMAGE_REFERANCE_BYTES[483] ^ nonce_bytes[1]
            final_init_img[487] = NEW_IMAGE_REFERANCE_BYTES[487] ^ nonce_bytes[1]
            final_init_img[491] = NEW_IMAGE_REFERANCE_BYTES[491] ^ nonce_bytes[1]
            final_init_img[495] = NEW_IMAGE_REFERANCE_BYTES[495] ^ nonce_bytes[1]
            final_init_img[499] = NEW_IMAGE_REFERANCE_BYTES[499] ^ nonce_bytes[1]
            final_init_img[503] = NEW_IMAGE_REFERANCE_BYTES[503] ^ nonce_bytes[1]
            final_init_img[507] = NEW_IMAGE_REFERANCE_BYTES[507] ^ nonce_bytes[1]
            final_init_img[511] = NEW_IMAGE_REFERANCE_BYTES[511] ^ nonce_bytes[1]
            final_init_img[515] = NEW_IMAGE_REFERANCE_BYTES[515] ^ nonce_bytes[1]
            final_init_img[519] = NEW_IMAGE_REFERANCE_BYTES[519] ^ nonce_bytes[1]
            final_init_img[523] = NEW_IMAGE_REFERANCE_BYTES[523] ^ nonce_bytes[1]
            final_init_img[527] = NEW_IMAGE_REFERANCE_BYTES[527] ^ nonce_bytes[1]
            final_init_img[531] = NEW_IMAGE_REFERANCE_BYTES[531] ^ nonce_bytes[1]
            final_init_img[535] = NEW_IMAGE_REFERANCE_BYTES[535] ^ nonce_bytes[1]
            final_init_img[539] = NEW_IMAGE_REFERANCE_BYTES[539] ^ nonce_bytes[1]
            final_init_img[543] = NEW_IMAGE_REFERANCE_BYTES[543] ^ nonce_bytes[1]
            final_init_img[547] = NEW_IMAGE_REFERANCE_BYTES[547] ^ nonce_bytes[1]
            final_init_img[551] = NEW_IMAGE_REFERANCE_BYTES[551] ^ nonce_bytes[1]
            final_init_img[555] = NEW_IMAGE_REFERANCE_BYTES[555] ^ nonce_bytes[1]
            final_init_img[559] = NEW_IMAGE_REFERANCE_BYTES[559] ^ nonce_bytes[1]
            final_init_img[563] = NEW_IMAGE_REFERANCE_BYTES[563] ^ nonce_bytes[1]
            final_init_img[567] = NEW_IMAGE_REFERANCE_BYTES[567] ^ nonce_bytes[1]
            final_init_img[571] = NEW_IMAGE_REFERANCE_BYTES[571] ^ nonce_bytes[1]
            final_init_img[575] = NEW_IMAGE_REFERANCE_BYTES[575] ^ nonce_bytes[1]
            final_init_img[579] = NEW_IMAGE_REFERANCE_BYTES[579] ^ nonce_bytes[1]
            final_init_img[583] = NEW_IMAGE_REFERANCE_BYTES[583] ^ nonce_bytes[1]
            final_init_img[587] = NEW_IMAGE_REFERANCE_BYTES[587] ^ nonce_bytes[1]
            final_init_img[591] = NEW_IMAGE_REFERANCE_BYTES[591] ^ nonce_bytes[1]
            final_init_img[595] = NEW_IMAGE_REFERANCE_BYTES[595] ^ nonce_bytes[1]
            final_init_img[599] = NEW_IMAGE_REFERANCE_BYTES[599] ^ nonce_bytes[1]
            final_init_img[603] = NEW_IMAGE_REFERANCE_BYTES[603] ^ nonce_bytes[1]
            final_init_img[607] = NEW_IMAGE_REFERANCE_BYTES[607] ^ nonce_bytes[1]
            final_init_img[611] = NEW_IMAGE_REFERANCE_BYTES[611] ^ nonce_bytes[1]
            final_init_img[615] = NEW_IMAGE_REFERANCE_BYTES[615] ^ nonce_bytes[1]
            final_init_img[619] = NEW_IMAGE_REFERANCE_BYTES[619] ^ nonce_bytes[1]
            final_init_img[623] = NEW_IMAGE_REFERANCE_BYTES[623] ^ nonce_bytes[1]
            final_init_img[627] = NEW_IMAGE_REFERANCE_BYTES[627] ^ nonce_bytes[1]
            final_init_img[631] = NEW_IMAGE_REFERANCE_BYTES[631] ^ nonce_bytes[1]
            final_init_img[635] = NEW_IMAGE_REFERANCE_BYTES[635] ^ nonce_bytes[1]
            final_init_img[639] = NEW_IMAGE_REFERANCE_BYTES[639] ^ nonce_bytes[1]
            final_init_img[643] = NEW_IMAGE_REFERANCE_BYTES[643] ^ nonce_bytes[1]
            final_init_img[647] = NEW_IMAGE_REFERANCE_BYTES[647] ^ nonce_bytes[1]
            final_init_img[651] = NEW_IMAGE_REFERANCE_BYTES[651] ^ nonce_bytes[1]
            final_init_img[655] = NEW_IMAGE_REFERANCE_BYTES[655] ^ nonce_bytes[1]
            final_init_img[659] = NEW_IMAGE_REFERANCE_BYTES[659] ^ nonce_bytes[1]
            final_init_img[663] = NEW_IMAGE_REFERANCE_BYTES[663] ^ nonce_bytes[1]
            final_init_img[667] = NEW_IMAGE_REFERANCE_BYTES[667] ^ nonce_bytes[1]
            final_init_img[671] = NEW_IMAGE_REFERANCE_BYTES[671] ^ nonce_bytes[1]
            final_init_img[675] = NEW_IMAGE_REFERANCE_BYTES[675] ^ nonce_bytes[1]
            final_init_img[679] = NEW_IMAGE_REFERANCE_BYTES[679] ^ nonce_bytes[1]
            final_init_img[683] = NEW_IMAGE_REFERANCE_BYTES[683] ^ nonce_bytes[1]
            final_init_img[687] = NEW_IMAGE_REFERANCE_BYTES[687] ^ nonce_bytes[1]
            final_init_img[691] = NEW_IMAGE_REFERANCE_BYTES[691] ^ nonce_bytes[1]
            final_init_img[695] = NEW_IMAGE_REFERANCE_BYTES[695] ^ nonce_bytes[1]
            final_init_img[699] = NEW_IMAGE_REFERANCE_BYTES[699] ^ nonce_bytes[1]
            final_init_img[703] = NEW_IMAGE_REFERANCE_BYTES[703] ^ nonce_bytes[1]
            final_init_img[707] = NEW_IMAGE_REFERANCE_BYTES[707] ^ nonce_bytes[1]
            final_init_img[711] = NEW_IMAGE_REFERANCE_BYTES[711] ^ nonce_bytes[1]
            final_init_img[715] = NEW_IMAGE_REFERANCE_BYTES[715] ^ nonce_bytes[1]
            final_init_img[719] = NEW_IMAGE_REFERANCE_BYTES[719] ^ nonce_bytes[1]
            final_init_img[723] = NEW_IMAGE_REFERANCE_BYTES[723] ^ nonce_bytes[1]
            final_init_img[727] = NEW_IMAGE_REFERANCE_BYTES[727] ^ nonce_bytes[1]
            final_init_img[731] = NEW_IMAGE_REFERANCE_BYTES[731] ^ nonce_bytes[1]
            final_init_img[735] = NEW_IMAGE_REFERANCE_BYTES[735] ^ nonce_bytes[1]
            final_init_img[739] = NEW_IMAGE_REFERANCE_BYTES[739] ^ nonce_bytes[1]
            final_init_img[743] = NEW_IMAGE_REFERANCE_BYTES[743] ^ nonce_bytes[1]
            final_init_img[747] = NEW_IMAGE_REFERANCE_BYTES[747] ^ nonce_bytes[1]
            final_init_img[751] = NEW_IMAGE_REFERANCE_BYTES[751] ^ nonce_bytes[1]
            final_init_img[755] = NEW_IMAGE_REFERANCE_BYTES[755] ^ nonce_bytes[1]
            final_init_img[759] = NEW_IMAGE_REFERANCE_BYTES[759] ^ nonce_bytes[1]
            final_init_img[763] = NEW_IMAGE_REFERANCE_BYTES[763] ^ nonce_bytes[1]
            final_init_img[767] = NEW_IMAGE_REFERANCE_BYTES[767] ^ nonce_bytes[1]
            final_init_img[771] = NEW_IMAGE_REFERANCE_BYTES[771] ^ nonce_bytes[1]
            final_init_img[775] = NEW_IMAGE_REFERANCE_BYTES[775] ^ nonce_bytes[1]
            final_init_img[779] = NEW_IMAGE_REFERANCE_BYTES[779] ^ nonce_bytes[1]
            final_init_img[783] = NEW_IMAGE_REFERANCE_BYTES[783] ^ nonce_bytes[1]
            final_init_img[787] = NEW_IMAGE_REFERANCE_BYTES[787] ^ nonce_bytes[1]
            final_init_img[791] = NEW_IMAGE_REFERANCE_BYTES[791] ^ nonce_bytes[1]
            final_init_img[795] = NEW_IMAGE_REFERANCE_BYTES[795] ^ nonce_bytes[1]
            final_init_img[799] = NEW_IMAGE_REFERANCE_BYTES[799] ^ nonce_bytes[1]
            final_init_img[803] = NEW_IMAGE_REFERANCE_BYTES[803] ^ nonce_bytes[1]
            final_init_img[807] = NEW_IMAGE_REFERANCE_BYTES[807] ^ nonce_bytes[1]
            final_init_img[811] = NEW_IMAGE_REFERANCE_BYTES[811] ^ nonce_bytes[1]
            final_init_img[815] = NEW_IMAGE_REFERANCE_BYTES[815] ^ nonce_bytes[1]
            final_init_img[819] = NEW_IMAGE_REFERANCE_BYTES[819] ^ nonce_bytes[1]
            final_init_img[823] = NEW_IMAGE_REFERANCE_BYTES[823] ^ nonce_bytes[1]
            final_init_img[827] = NEW_IMAGE_REFERANCE_BYTES[827] ^ nonce_bytes[1]
            final_init_img[831] = NEW_IMAGE_REFERANCE_BYTES[831] ^ nonce_bytes[1]
            final_init_img[835] = NEW_IMAGE_REFERANCE_BYTES[835] ^ nonce_bytes[1]
            final_init_img[839] = NEW_IMAGE_REFERANCE_BYTES[839] ^ nonce_bytes[1]
            final_init_img[843] = NEW_IMAGE_REFERANCE_BYTES[843] ^ nonce_bytes[1]
            final_init_img[847] = NEW_IMAGE_REFERANCE_BYTES[847] ^ nonce_bytes[1]
            final_init_img[851] = NEW_IMAGE_REFERANCE_BYTES[851] ^ nonce_bytes[1]
            final_init_img[855] = NEW_IMAGE_REFERANCE_BYTES[855] ^ nonce_bytes[1]
            final_init_img[859] = NEW_IMAGE_REFERANCE_BYTES[859] ^ nonce_bytes[1]
            final_init_img[863] = NEW_IMAGE_REFERANCE_BYTES[863] ^ nonce_bytes[1]
            final_init_img[867] = NEW_IMAGE_REFERANCE_BYTES[867] ^ nonce_bytes[1]
            final_init_img[871] = NEW_IMAGE_REFERANCE_BYTES[871] ^ nonce_bytes[1]
            final_init_img[875] = NEW_IMAGE_REFERANCE_BYTES[875] ^ nonce_bytes[1]
            final_init_img[879] = NEW_IMAGE_REFERANCE_BYTES[879] ^ nonce_bytes[1]
            final_init_img[883] = NEW_IMAGE_REFERANCE_BYTES[883] ^ nonce_bytes[1]
            final_init_img[887] = NEW_IMAGE_REFERANCE_BYTES[887] ^ nonce_bytes[1]
            final_init_img[891] = NEW_IMAGE_REFERANCE_BYTES[891] ^ nonce_bytes[1]
            final_init_img[895] = NEW_IMAGE_REFERANCE_BYTES[895] ^ nonce_bytes[1]
            final_init_img[899] = NEW_IMAGE_REFERANCE_BYTES[899] ^ nonce_bytes[1]
            final_init_img[903] = NEW_IMAGE_REFERANCE_BYTES[903] ^ nonce_bytes[1]
            final_init_img[907] = NEW_IMAGE_REFERANCE_BYTES[907] ^ nonce_bytes[1]
            final_init_img[911] = NEW_IMAGE_REFERANCE_BYTES[911] ^ nonce_bytes[1]
            final_init_img[915] = NEW_IMAGE_REFERANCE_BYTES[915] ^ nonce_bytes[1]
            final_init_img[919] = NEW_IMAGE_REFERANCE_BYTES[919] ^ nonce_bytes[1]
            final_init_img[923] = NEW_IMAGE_REFERANCE_BYTES[923] ^ nonce_bytes[1]
            final_init_img[927] = NEW_IMAGE_REFERANCE_BYTES[927] ^ nonce_bytes[1]
            final_init_img[931] = NEW_IMAGE_REFERANCE_BYTES[931] ^ nonce_bytes[1]
            final_init_img[935] = NEW_IMAGE_REFERANCE_BYTES[935] ^ nonce_bytes[1]
            final_init_img[939] = NEW_IMAGE_REFERANCE_BYTES[939] ^ nonce_bytes[1]
            final_init_img[943] = NEW_IMAGE_REFERANCE_BYTES[943] ^ nonce_bytes[1]
            final_init_img[947] = NEW_IMAGE_REFERANCE_BYTES[947] ^ nonce_bytes[1]
            final_init_img[951] = NEW_IMAGE_REFERANCE_BYTES[951] ^ nonce_bytes[1]
            final_init_img[955] = NEW_IMAGE_REFERANCE_BYTES[955] ^ nonce_bytes[1]
            final_init_img[959] = NEW_IMAGE_REFERANCE_BYTES[959] ^ nonce_bytes[1]
            final_init_img[963] = NEW_IMAGE_REFERANCE_BYTES[963] ^ nonce_bytes[1]
            final_init_img[967] = NEW_IMAGE_REFERANCE_BYTES[967] ^ nonce_bytes[1]
            final_init_img[971] = NEW_IMAGE_REFERANCE_BYTES[971] ^ nonce_bytes[1]
            final_init_img[975] = NEW_IMAGE_REFERANCE_BYTES[975] ^ nonce_bytes[1]
            final_init_img[979] = NEW_IMAGE_REFERANCE_BYTES[979] ^ nonce_bytes[1]
            final_init_img[983] = NEW_IMAGE_REFERANCE_BYTES[983] ^ nonce_bytes[1]
            final_init_img[987] = NEW_IMAGE_REFERANCE_BYTES[987] ^ nonce_bytes[1]
            final_init_img[991] = NEW_IMAGE_REFERANCE_BYTES[991] ^ nonce_bytes[1]
            final_init_img[995] = NEW_IMAGE_REFERANCE_BYTES[995] ^ nonce_bytes[1]
            final_init_img[999] = NEW_IMAGE_REFERANCE_BYTES[999] ^ nonce_bytes[1]
            final_init_img[1003] = NEW_IMAGE_REFERANCE_BYTES[1003] ^ nonce_bytes[1]
            final_init_img[1007] = NEW_IMAGE_REFERANCE_BYTES[1007] ^ nonce_bytes[1]
            final_init_img[1011] = NEW_IMAGE_REFERANCE_BYTES[1011] ^ nonce_bytes[1]
            final_init_img[1015] = NEW_IMAGE_REFERANCE_BYTES[1015] ^ nonce_bytes[1]
            final_init_img[1019] = NEW_IMAGE_REFERANCE_BYTES[1019] ^ nonce_bytes[1]
            final_init_img[1023] = NEW_IMAGE_REFERANCE_BYTES[1023] ^ nonce_bytes[1]
            final_init_img[1027] = NEW_IMAGE_REFERANCE_BYTES[1027] ^ nonce_bytes[1]
            final_init_img[1031] = NEW_IMAGE_REFERANCE_BYTES[1031] ^ nonce_bytes[1]
            final_init_img[1035] = NEW_IMAGE_REFERANCE_BYTES[1035] ^ nonce_bytes[1]
            final_init_img[1039] = NEW_IMAGE_REFERANCE_BYTES[1039] ^ nonce_bytes[1]
            final_init_img[1043] = NEW_IMAGE_REFERANCE_BYTES[1043] ^ nonce_bytes[1]
            final_init_img[1047] = NEW_IMAGE_REFERANCE_BYTES[1047] ^ nonce_bytes[1]
            final_init_img[1051] = NEW_IMAGE_REFERANCE_BYTES[1051] ^ nonce_bytes[1]
            final_init_img[1055] = NEW_IMAGE_REFERANCE_BYTES[1055] ^ nonce_bytes[1]
            final_init_img[1059] = NEW_IMAGE_REFERANCE_BYTES[1059] ^ nonce_bytes[1]
            final_init_img[1063] = NEW_IMAGE_REFERANCE_BYTES[1063] ^ nonce_bytes[1]
            final_init_img[1067] = NEW_IMAGE_REFERANCE_BYTES[1067] ^ nonce_bytes[1]
            final_init_img[1071] = NEW_IMAGE_REFERANCE_BYTES[1071] ^ nonce_bytes[1]
            final_init_img[1075] = NEW_IMAGE_REFERANCE_BYTES[1075] ^ nonce_bytes[1]
            final_init_img[1079] = NEW_IMAGE_REFERANCE_BYTES[1079] ^ nonce_bytes[1]
            final_init_img[1083] = NEW_IMAGE_REFERANCE_BYTES[1083] ^ nonce_bytes[1]
            final_init_img[1087] = NEW_IMAGE_REFERANCE_BYTES[1087] ^ nonce_bytes[1]
            final_init_img[1091] = NEW_IMAGE_REFERANCE_BYTES[1091] ^ nonce_bytes[1]
            final_init_img[1095] = NEW_IMAGE_REFERANCE_BYTES[1095] ^ nonce_bytes[1]
            final_init_img[1099] = NEW_IMAGE_REFERANCE_BYTES[1099] ^ nonce_bytes[1]
            final_init_img[1103] = NEW_IMAGE_REFERANCE_BYTES[1103] ^ nonce_bytes[1]
            final_init_img[1107] = NEW_IMAGE_REFERANCE_BYTES[1107] ^ nonce_bytes[1]
            final_init_img[1111] = NEW_IMAGE_REFERANCE_BYTES[1111] ^ nonce_bytes[1]
            final_init_img[1115] = NEW_IMAGE_REFERANCE_BYTES[1115] ^ nonce_bytes[1]
            final_init_img[1119] = NEW_IMAGE_REFERANCE_BYTES[1119] ^ nonce_bytes[1]
            final_init_img[1123] = NEW_IMAGE_REFERANCE_BYTES[1123] ^ nonce_bytes[1]
            final_init_img[1127] = NEW_IMAGE_REFERANCE_BYTES[1127] ^ nonce_bytes[1]
            final_init_img[1131] = NEW_IMAGE_REFERANCE_BYTES[1131] ^ nonce_bytes[1]
            final_init_img[1135] = NEW_IMAGE_REFERANCE_BYTES[1135] ^ nonce_bytes[1]
            final_init_img[1139] = NEW_IMAGE_REFERANCE_BYTES[1139] ^ nonce_bytes[1]
            final_init_img[1143] = NEW_IMAGE_REFERANCE_BYTES[1143] ^ nonce_bytes[1]
            final_init_img[1147] = NEW_IMAGE_REFERANCE_BYTES[1147] ^ nonce_bytes[1]
            final_init_img[1151] = NEW_IMAGE_REFERANCE_BYTES[1151] ^ nonce_bytes[1]
            final_init_img[1155] = NEW_IMAGE_REFERANCE_BYTES[1155] ^ nonce_bytes[1]
            final_init_img[1159] = NEW_IMAGE_REFERANCE_BYTES[1159] ^ nonce_bytes[1]
            final_init_img[1163] = NEW_IMAGE_REFERANCE_BYTES[1163] ^ nonce_bytes[1]
            final_init_img[1167] = NEW_IMAGE_REFERANCE_BYTES[1167] ^ nonce_bytes[1]
            final_init_img[1171] = NEW_IMAGE_REFERANCE_BYTES[1171] ^ nonce_bytes[1]
            final_init_img[1175] = NEW_IMAGE_REFERANCE_BYTES[1175] ^ nonce_bytes[1]
            final_init_img[1179] = NEW_IMAGE_REFERANCE_BYTES[1179] ^ nonce_bytes[1]
            final_init_img[1183] = NEW_IMAGE_REFERANCE_BYTES[1183] ^ nonce_bytes[1]
            final_init_img[1187] = NEW_IMAGE_REFERANCE_BYTES[1187] ^ nonce_bytes[1]
            final_init_img[1191] = NEW_IMAGE_REFERANCE_BYTES[1191] ^ nonce_bytes[1]
            final_init_img[1195] = NEW_IMAGE_REFERANCE_BYTES[1195] ^ nonce_bytes[1]
            final_init_img[1199] = NEW_IMAGE_REFERANCE_BYTES[1199] ^ nonce_bytes[1]
            final_init_img[1203] = NEW_IMAGE_REFERANCE_BYTES[1203] ^ nonce_bytes[1]
            final_init_img[1207] = NEW_IMAGE_REFERANCE_BYTES[1207] ^ nonce_bytes[1]
            final_init_img[1211] = NEW_IMAGE_REFERANCE_BYTES[1211] ^ nonce_bytes[1]
            final_init_img[1215] = NEW_IMAGE_REFERANCE_BYTES[1215] ^ nonce_bytes[1]
            final_init_img[1219] = NEW_IMAGE_REFERANCE_BYTES[1219] ^ nonce_bytes[1]
            final_init_img[1223] = NEW_IMAGE_REFERANCE_BYTES[1223] ^ nonce_bytes[1]
            final_init_img[1227] = NEW_IMAGE_REFERANCE_BYTES[1227] ^ nonce_bytes[1]
            final_init_img[1231] = NEW_IMAGE_REFERANCE_BYTES[1231] ^ nonce_bytes[1]
            final_init_img[1235] = NEW_IMAGE_REFERANCE_BYTES[1235] ^ nonce_bytes[1]
            final_init_img[1239] = NEW_IMAGE_REFERANCE_BYTES[1239] ^ nonce_bytes[1]
            final_init_img[1243] = NEW_IMAGE_REFERANCE_BYTES[1243] ^ nonce_bytes[1]
            final_init_img[1247] = NEW_IMAGE_REFERANCE_BYTES[1247] ^ nonce_bytes[1]
            final_init_img[1251] = NEW_IMAGE_REFERANCE_BYTES[1251] ^ nonce_bytes[1]
            final_init_img[1255] = NEW_IMAGE_REFERANCE_BYTES[1255] ^ nonce_bytes[1]
            final_init_img[1259] = NEW_IMAGE_REFERANCE_BYTES[1259] ^ nonce_bytes[1]
            final_init_img[1263] = NEW_IMAGE_REFERANCE_BYTES[1263] ^ nonce_bytes[1]
            final_init_img[1267] = NEW_IMAGE_REFERANCE_BYTES[1267] ^ nonce_bytes[1]
            final_init_img[1271] = NEW_IMAGE_REFERANCE_BYTES[1271] ^ nonce_bytes[1]
            final_init_img[1275] = NEW_IMAGE_REFERANCE_BYTES[1275] ^ nonce_bytes[1]
            final_init_img[1279] = NEW_IMAGE_REFERANCE_BYTES[1279] ^ nonce_bytes[1]
            final_init_img[1283] = NEW_IMAGE_REFERANCE_BYTES[1283] ^ nonce_bytes[1]
            final_init_img[1287] = NEW_IMAGE_REFERANCE_BYTES[1287] ^ nonce_bytes[1]
            final_init_img[1291] = NEW_IMAGE_REFERANCE_BYTES[1291] ^ nonce_bytes[1]
            final_init_img[1295] = NEW_IMAGE_REFERANCE_BYTES[1295] ^ nonce_bytes[1]
            final_init_img[1299] = NEW_IMAGE_REFERANCE_BYTES[1299] ^ nonce_bytes[1]
            final_init_img[1303] = NEW_IMAGE_REFERANCE_BYTES[1303] ^ nonce_bytes[1]
            final_init_img[1307] = NEW_IMAGE_REFERANCE_BYTES[1307] ^ nonce_bytes[1]
            final_init_img[1311] = NEW_IMAGE_REFERANCE_BYTES[1311] ^ nonce_bytes[1]
            final_init_img[1315] = NEW_IMAGE_REFERANCE_BYTES[1315] ^ nonce_bytes[1]
            final_init_img[1319] = NEW_IMAGE_REFERANCE_BYTES[1319] ^ nonce_bytes[1]
            final_init_img[1323] = NEW_IMAGE_REFERANCE_BYTES[1323] ^ nonce_bytes[1]
            final_init_img[1327] = NEW_IMAGE_REFERANCE_BYTES[1327] ^ nonce_bytes[1]
            final_init_img[1331] = NEW_IMAGE_REFERANCE_BYTES[1331] ^ nonce_bytes[1]
            final_init_img[1335] = NEW_IMAGE_REFERANCE_BYTES[1335] ^ nonce_bytes[1]
            final_init_img[1339] = NEW_IMAGE_REFERANCE_BYTES[1339] ^ nonce_bytes[1]
            final_init_img[1343] = NEW_IMAGE_REFERANCE_BYTES[1343] ^ nonce_bytes[1]
            final_init_img[1347] = NEW_IMAGE_REFERANCE_BYTES[1347] ^ nonce_bytes[1]
            final_init_img[1351] = NEW_IMAGE_REFERANCE_BYTES[1351] ^ nonce_bytes[1]
            final_init_img[1355] = NEW_IMAGE_REFERANCE_BYTES[1355] ^ nonce_bytes[1]
            final_init_img[1359] = NEW_IMAGE_REFERANCE_BYTES[1359] ^ nonce_bytes[1]
            final_init_img[1363] = NEW_IMAGE_REFERANCE_BYTES[1363] ^ nonce_bytes[1]
            final_init_img[1367] = NEW_IMAGE_REFERANCE_BYTES[1367] ^ nonce_bytes[1]
            final_init_img[1371] = NEW_IMAGE_REFERANCE_BYTES[1371] ^ nonce_bytes[1]
            final_init_img[1375] = NEW_IMAGE_REFERANCE_BYTES[1375] ^ nonce_bytes[1]
            final_init_img[1379] = NEW_IMAGE_REFERANCE_BYTES[1379] ^ nonce_bytes[1]
            final_init_img[1383] = NEW_IMAGE_REFERANCE_BYTES[1383] ^ nonce_bytes[1]
            final_init_img[1387] = NEW_IMAGE_REFERANCE_BYTES[1387] ^ nonce_bytes[1]
            final_init_img[1391] = NEW_IMAGE_REFERANCE_BYTES[1391] ^ nonce_bytes[1]
            final_init_img[1395] = NEW_IMAGE_REFERANCE_BYTES[1395] ^ nonce_bytes[1]
            final_init_img[1399] = NEW_IMAGE_REFERANCE_BYTES[1399] ^ nonce_bytes[1]
            final_init_img[1403] = NEW_IMAGE_REFERANCE_BYTES[1403] ^ nonce_bytes[1]
            final_init_img[1407] = NEW_IMAGE_REFERANCE_BYTES[1407] ^ nonce_bytes[1]
            final_init_img[1411] = NEW_IMAGE_REFERANCE_BYTES[1411] ^ nonce_bytes[1]
            final_init_img[1415] = NEW_IMAGE_REFERANCE_BYTES[1415] ^ nonce_bytes[1]
            final_init_img[1419] = NEW_IMAGE_REFERANCE_BYTES[1419] ^ nonce_bytes[1]
            final_init_img[1423] = NEW_IMAGE_REFERANCE_BYTES[1423] ^ nonce_bytes[1]
            final_init_img[1427] = NEW_IMAGE_REFERANCE_BYTES[1427] ^ nonce_bytes[1]
            final_init_img[1431] = NEW_IMAGE_REFERANCE_BYTES[1431] ^ nonce_bytes[1]
            final_init_img[1435] = NEW_IMAGE_REFERANCE_BYTES[1435] ^ nonce_bytes[1]
            final_init_img[1439] = NEW_IMAGE_REFERANCE_BYTES[1439] ^ nonce_bytes[1]
            final_init_img[1443] = NEW_IMAGE_REFERANCE_BYTES[1443] ^ nonce_bytes[1]
            final_init_img[1447] = NEW_IMAGE_REFERANCE_BYTES[1447] ^ nonce_bytes[1]
            final_init_img[1451] = NEW_IMAGE_REFERANCE_BYTES[1451] ^ nonce_bytes[1]
            final_init_img[1455] = NEW_IMAGE_REFERANCE_BYTES[1455] ^ nonce_bytes[1]
            final_init_img[1459] = NEW_IMAGE_REFERANCE_BYTES[1459] ^ nonce_bytes[1]
            final_init_img[1463] = NEW_IMAGE_REFERANCE_BYTES[1463] ^ nonce_bytes[1]
            final_init_img[1467] = NEW_IMAGE_REFERANCE_BYTES[1467] ^ nonce_bytes[1]
            final_init_img[1471] = NEW_IMAGE_REFERANCE_BYTES[1471] ^ nonce_bytes[1]
            final_init_img[1475] = NEW_IMAGE_REFERANCE_BYTES[1475] ^ nonce_bytes[1]
            final_init_img[1479] = NEW_IMAGE_REFERANCE_BYTES[1479] ^ nonce_bytes[1]
            final_init_img[1483] = NEW_IMAGE_REFERANCE_BYTES[1483] ^ nonce_bytes[1]
            final_init_img[1487] = NEW_IMAGE_REFERANCE_BYTES[1487] ^ nonce_bytes[1]
            final_init_img[1491] = NEW_IMAGE_REFERANCE_BYTES[1491] ^ nonce_bytes[1]
            final_init_img[1495] = NEW_IMAGE_REFERANCE_BYTES[1495] ^ nonce_bytes[1]
            final_init_img[1499] = NEW_IMAGE_REFERANCE_BYTES[1499] ^ nonce_bytes[1]
            final_init_img[1503] = NEW_IMAGE_REFERANCE_BYTES[1503] ^ nonce_bytes[1]
            final_init_img[1507] = NEW_IMAGE_REFERANCE_BYTES[1507] ^ nonce_bytes[1]
            final_init_img[1511] = NEW_IMAGE_REFERANCE_BYTES[1511] ^ nonce_bytes[1]
            final_init_img[1515] = NEW_IMAGE_REFERANCE_BYTES[1515] ^ nonce_bytes[1]
            final_init_img[1519] = NEW_IMAGE_REFERANCE_BYTES[1519] ^ nonce_bytes[1]
            final_init_img[1523] = NEW_IMAGE_REFERANCE_BYTES[1523] ^ nonce_bytes[1]
            final_init_img[1527] = NEW_IMAGE_REFERANCE_BYTES[1527] ^ nonce_bytes[1]
            final_init_img[1531] = NEW_IMAGE_REFERANCE_BYTES[1531] ^ nonce_bytes[1]
            final_init_img[1535] = NEW_IMAGE_REFERANCE_BYTES[1535] ^ nonce_bytes[1]
            final_init_img[1539] = NEW_IMAGE_REFERANCE_BYTES[1539] ^ nonce_bytes[1]
            final_init_img[1543] = NEW_IMAGE_REFERANCE_BYTES[1543] ^ nonce_bytes[1]
            final_init_img[1547] = NEW_IMAGE_REFERANCE_BYTES[1547] ^ nonce_bytes[1]
            final_init_img[1551] = NEW_IMAGE_REFERANCE_BYTES[1551] ^ nonce_bytes[1]
            final_init_img[1555] = NEW_IMAGE_REFERANCE_BYTES[1555] ^ nonce_bytes[1]
            final_init_img[1559] = NEW_IMAGE_REFERANCE_BYTES[1559] ^ nonce_bytes[1]
            final_init_img[1563] = NEW_IMAGE_REFERANCE_BYTES[1563] ^ nonce_bytes[1]
            final_init_img[1567] = NEW_IMAGE_REFERANCE_BYTES[1567] ^ nonce_bytes[1]
            final_init_img[1571] = NEW_IMAGE_REFERANCE_BYTES[1571] ^ nonce_bytes[1]
            final_init_img[1575] = NEW_IMAGE_REFERANCE_BYTES[1575] ^ nonce_bytes[1]
            final_init_img[1579] = NEW_IMAGE_REFERANCE_BYTES[1579] ^ nonce_bytes[1]
            final_init_img[1583] = NEW_IMAGE_REFERANCE_BYTES[1583] ^ nonce_bytes[1]
            final_init_img[1587] = NEW_IMAGE_REFERANCE_BYTES[1587] ^ nonce_bytes[1]
            final_init_img[1591] = NEW_IMAGE_REFERANCE_BYTES[1591] ^ nonce_bytes[1]
            final_init_img[1595] = NEW_IMAGE_REFERANCE_BYTES[1595] ^ nonce_bytes[1]
            final_init_img[1599] = NEW_IMAGE_REFERANCE_BYTES[1599] ^ nonce_bytes[1]
            final_init_img[1603] = NEW_IMAGE_REFERANCE_BYTES[1603] ^ nonce_bytes[1]
            final_init_img[1607] = NEW_IMAGE_REFERANCE_BYTES[1607] ^ nonce_bytes[1]
            final_init_img[1611] = NEW_IMAGE_REFERANCE_BYTES[1611] ^ nonce_bytes[1]
            final_init_img[1615] = NEW_IMAGE_REFERANCE_BYTES[1615] ^ nonce_bytes[1]
            final_init_img[1619] = NEW_IMAGE_REFERANCE_BYTES[1619] ^ nonce_bytes[1]
            final_init_img[1623] = NEW_IMAGE_REFERANCE_BYTES[1623] ^ nonce_bytes[1]
            final_init_img[1627] = NEW_IMAGE_REFERANCE_BYTES[1627] ^ nonce_bytes[1]
            final_init_img[1631] = NEW_IMAGE_REFERANCE_BYTES[1631] ^ nonce_bytes[1]
            final_init_img[1635] = NEW_IMAGE_REFERANCE_BYTES[1635] ^ nonce_bytes[1]
            final_init_img[1639] = NEW_IMAGE_REFERANCE_BYTES[1639] ^ nonce_bytes[1]
            final_init_img[1643] = NEW_IMAGE_REFERANCE_BYTES[1643] ^ nonce_bytes[1]
            final_init_img[1647] = NEW_IMAGE_REFERANCE_BYTES[1647] ^ nonce_bytes[1]
            final_init_img[1651] = NEW_IMAGE_REFERANCE_BYTES[1651] ^ nonce_bytes[1]
            final_init_img[1655] = NEW_IMAGE_REFERANCE_BYTES[1655] ^ nonce_bytes[1]
            final_init_img[1659] = NEW_IMAGE_REFERANCE_BYTES[1659] ^ nonce_bytes[1]
            final_init_img[1663] = NEW_IMAGE_REFERANCE_BYTES[1663] ^ nonce_bytes[1]
            final_init_img[1667] = NEW_IMAGE_REFERANCE_BYTES[1667] ^ nonce_bytes[1]
            final_init_img[1671] = NEW_IMAGE_REFERANCE_BYTES[1671] ^ nonce_bytes[1]
            final_init_img[1675] = NEW_IMAGE_REFERANCE_BYTES[1675] ^ nonce_bytes[1]
            final_init_img[1679] = NEW_IMAGE_REFERANCE_BYTES[1679] ^ nonce_bytes[1]
            final_init_img[1683] = NEW_IMAGE_REFERANCE_BYTES[1683] ^ nonce_bytes[1]
            final_init_img[1687] = NEW_IMAGE_REFERANCE_BYTES[1687] ^ nonce_bytes[1]
            final_init_img[1691] = NEW_IMAGE_REFERANCE_BYTES[1691] ^ nonce_bytes[1]
            final_init_img[1695] = NEW_IMAGE_REFERANCE_BYTES[1695] ^ nonce_bytes[1]
            final_init_img[1699] = NEW_IMAGE_REFERANCE_BYTES[1699] ^ nonce_bytes[1]
            final_init_img[1703] = NEW_IMAGE_REFERANCE_BYTES[1703] ^ nonce_bytes[1]
            final_init_img[1707] = NEW_IMAGE_REFERANCE_BYTES[1707] ^ nonce_bytes[1]
            final_init_img[1711] = NEW_IMAGE_REFERANCE_BYTES[1711] ^ nonce_bytes[1]
            final_init_img[1715] = NEW_IMAGE_REFERANCE_BYTES[1715] ^ nonce_bytes[1]
            final_init_img[1719] = NEW_IMAGE_REFERANCE_BYTES[1719] ^ nonce_bytes[1]
            final_init_img[1723] = NEW_IMAGE_REFERANCE_BYTES[1723] ^ nonce_bytes[1]
            final_init_img[1727] = NEW_IMAGE_REFERANCE_BYTES[1727] ^ nonce_bytes[1]
            final_init_img[1731] = NEW_IMAGE_REFERANCE_BYTES[1731] ^ nonce_bytes[1]
            final_init_img[1735] = NEW_IMAGE_REFERANCE_BYTES[1735] ^ nonce_bytes[1]
            final_init_img[1739] = NEW_IMAGE_REFERANCE_BYTES[1739] ^ nonce_bytes[1]
            final_init_img[1743] = NEW_IMAGE_REFERANCE_BYTES[1743] ^ nonce_bytes[1]
            final_init_img[1747] = NEW_IMAGE_REFERANCE_BYTES[1747] ^ nonce_bytes[1]
            final_init_img[1751] = NEW_IMAGE_REFERANCE_BYTES[1751] ^ nonce_bytes[1]
            final_init_img[1755] = NEW_IMAGE_REFERANCE_BYTES[1755] ^ nonce_bytes[1]
            final_init_img[1759] = NEW_IMAGE_REFERANCE_BYTES[1759] ^ nonce_bytes[1]
            final_init_img[1763] = NEW_IMAGE_REFERANCE_BYTES[1763] ^ nonce_bytes[1]
            final_init_img[1767] = NEW_IMAGE_REFERANCE_BYTES[1767] ^ nonce_bytes[1]
            final_init_img[1771] = NEW_IMAGE_REFERANCE_BYTES[1771] ^ nonce_bytes[1]
            final_init_img[1775] = NEW_IMAGE_REFERANCE_BYTES[1775] ^ nonce_bytes[1]
            final_init_img[1779] = NEW_IMAGE_REFERANCE_BYTES[1779] ^ nonce_bytes[1]
       


        if nlastbyte2 != nonce_bytes[2]:
            nlastbyte2 = nonce_bytes[2]
            final_init_img[56] = NEW_IMAGE_REFERANCE_BYTES[56] ^ nonce_bytes[2]
            final_init_img[60] = NEW_IMAGE_REFERANCE_BYTES[60] ^ nonce_bytes[2]
            final_init_img[64] = NEW_IMAGE_REFERANCE_BYTES[64] ^ nonce_bytes[2]
            final_init_img[68] = NEW_IMAGE_REFERANCE_BYTES[68] ^ nonce_bytes[2]
            final_init_img[72] = NEW_IMAGE_REFERANCE_BYTES[72] ^ nonce_bytes[2]
            final_init_img[76] = NEW_IMAGE_REFERANCE_BYTES[76] ^ nonce_bytes[2]
            final_init_img[80] = NEW_IMAGE_REFERANCE_BYTES[80] ^ nonce_bytes[2]
            final_init_img[84] = NEW_IMAGE_REFERANCE_BYTES[84] ^ nonce_bytes[2]
            final_init_img[88] = NEW_IMAGE_REFERANCE_BYTES[88] ^ nonce_bytes[2]
            final_init_img[92] = NEW_IMAGE_REFERANCE_BYTES[92] ^ nonce_bytes[2]
            final_init_img[96] = NEW_IMAGE_REFERANCE_BYTES[96] ^ nonce_bytes[2]
            final_init_img[100] = NEW_IMAGE_REFERANCE_BYTES[100] ^ nonce_bytes[2]
            final_init_img[104] = NEW_IMAGE_REFERANCE_BYTES[104] ^ nonce_bytes[2]
            final_init_img[108] = NEW_IMAGE_REFERANCE_BYTES[108] ^ nonce_bytes[2]
            final_init_img[112] = NEW_IMAGE_REFERANCE_BYTES[112] ^ nonce_bytes[2]
            final_init_img[116] = NEW_IMAGE_REFERANCE_BYTES[116] ^ nonce_bytes[2]
            final_init_img[120] = NEW_IMAGE_REFERANCE_BYTES[120] ^ nonce_bytes[2]
            final_init_img[124] = NEW_IMAGE_REFERANCE_BYTES[124] ^ nonce_bytes[2]
            final_init_img[128] = NEW_IMAGE_REFERANCE_BYTES[128] ^ nonce_bytes[2]
            final_init_img[132] = NEW_IMAGE_REFERANCE_BYTES[132] ^ nonce_bytes[2]
            final_init_img[136] = NEW_IMAGE_REFERANCE_BYTES[136] ^ nonce_bytes[2]
            final_init_img[140] = NEW_IMAGE_REFERANCE_BYTES[140] ^ nonce_bytes[2]
            final_init_img[144] = NEW_IMAGE_REFERANCE_BYTES[144] ^ nonce_bytes[2]
            final_init_img[148] = NEW_IMAGE_REFERANCE_BYTES[148] ^ nonce_bytes[2]
            final_init_img[152] = NEW_IMAGE_REFERANCE_BYTES[152] ^ nonce_bytes[2]
            final_init_img[156] = NEW_IMAGE_REFERANCE_BYTES[156] ^ nonce_bytes[2]
            final_init_img[160] = NEW_IMAGE_REFERANCE_BYTES[160] ^ nonce_bytes[2]
            final_init_img[164] = NEW_IMAGE_REFERANCE_BYTES[164] ^ nonce_bytes[2]
            final_init_img[168] = NEW_IMAGE_REFERANCE_BYTES[168] ^ nonce_bytes[2]
            final_init_img[172] = NEW_IMAGE_REFERANCE_BYTES[172] ^ nonce_bytes[2]
            final_init_img[176] = NEW_IMAGE_REFERANCE_BYTES[176] ^ nonce_bytes[2]
            final_init_img[180] = NEW_IMAGE_REFERANCE_BYTES[180] ^ nonce_bytes[2]
            final_init_img[184] = NEW_IMAGE_REFERANCE_BYTES[184] ^ nonce_bytes[2]
            final_init_img[188] = NEW_IMAGE_REFERANCE_BYTES[188] ^ nonce_bytes[2]
            final_init_img[192] = NEW_IMAGE_REFERANCE_BYTES[192] ^ nonce_bytes[2]
            final_init_img[196] = NEW_IMAGE_REFERANCE_BYTES[196] ^ nonce_bytes[2]
            final_init_img[200] = NEW_IMAGE_REFERANCE_BYTES[200] ^ nonce_bytes[2]
            final_init_img[204] = NEW_IMAGE_REFERANCE_BYTES[204] ^ nonce_bytes[2]
            final_init_img[208] = NEW_IMAGE_REFERANCE_BYTES[208] ^ nonce_bytes[2]
            final_init_img[212] = NEW_IMAGE_REFERANCE_BYTES[212] ^ nonce_bytes[2]
            final_init_img[216] = NEW_IMAGE_REFERANCE_BYTES[216] ^ nonce_bytes[2]
            final_init_img[220] = NEW_IMAGE_REFERANCE_BYTES[220] ^ nonce_bytes[2]
            final_init_img[224] = NEW_IMAGE_REFERANCE_BYTES[224] ^ nonce_bytes[2]
            final_init_img[228] = NEW_IMAGE_REFERANCE_BYTES[228] ^ nonce_bytes[2]
            final_init_img[232] = NEW_IMAGE_REFERANCE_BYTES[232] ^ nonce_bytes[2]
            final_init_img[236] = NEW_IMAGE_REFERANCE_BYTES[236] ^ nonce_bytes[2]
            final_init_img[240] = NEW_IMAGE_REFERANCE_BYTES[240] ^ nonce_bytes[2]
            final_init_img[244] = NEW_IMAGE_REFERANCE_BYTES[244] ^ nonce_bytes[2]
            final_init_img[248] = NEW_IMAGE_REFERANCE_BYTES[248] ^ nonce_bytes[2]
            final_init_img[252] = NEW_IMAGE_REFERANCE_BYTES[252] ^ nonce_bytes[2]
            final_init_img[256] = NEW_IMAGE_REFERANCE_BYTES[256] ^ nonce_bytes[2]
            final_init_img[260] = NEW_IMAGE_REFERANCE_BYTES[260] ^ nonce_bytes[2]
            final_init_img[264] = NEW_IMAGE_REFERANCE_BYTES[264] ^ nonce_bytes[2]
            final_init_img[268] = NEW_IMAGE_REFERANCE_BYTES[268] ^ nonce_bytes[2]
            final_init_img[272] = NEW_IMAGE_REFERANCE_BYTES[272] ^ nonce_bytes[2]
            final_init_img[276] = NEW_IMAGE_REFERANCE_BYTES[276] ^ nonce_bytes[2]
            final_init_img[280] = NEW_IMAGE_REFERANCE_BYTES[280] ^ nonce_bytes[2]
            final_init_img[284] = NEW_IMAGE_REFERANCE_BYTES[284] ^ nonce_bytes[2]
            final_init_img[288] = NEW_IMAGE_REFERANCE_BYTES[288] ^ nonce_bytes[2]
            final_init_img[292] = NEW_IMAGE_REFERANCE_BYTES[292] ^ nonce_bytes[2]
            final_init_img[296] = NEW_IMAGE_REFERANCE_BYTES[296] ^ nonce_bytes[2]
            final_init_img[300] = NEW_IMAGE_REFERANCE_BYTES[300] ^ nonce_bytes[2]
            final_init_img[304] = NEW_IMAGE_REFERANCE_BYTES[304] ^ nonce_bytes[2]
            final_init_img[308] = NEW_IMAGE_REFERANCE_BYTES[308] ^ nonce_bytes[2]
            final_init_img[312] = NEW_IMAGE_REFERANCE_BYTES[312] ^ nonce_bytes[2]
            final_init_img[316] = NEW_IMAGE_REFERANCE_BYTES[316] ^ nonce_bytes[2]
            final_init_img[320] = NEW_IMAGE_REFERANCE_BYTES[320] ^ nonce_bytes[2]
            final_init_img[324] = NEW_IMAGE_REFERANCE_BYTES[324] ^ nonce_bytes[2]
            final_init_img[328] = NEW_IMAGE_REFERANCE_BYTES[328] ^ nonce_bytes[2]
            final_init_img[332] = NEW_IMAGE_REFERANCE_BYTES[332] ^ nonce_bytes[2]
            final_init_img[336] = NEW_IMAGE_REFERANCE_BYTES[336] ^ nonce_bytes[2]
            final_init_img[340] = NEW_IMAGE_REFERANCE_BYTES[340] ^ nonce_bytes[2]
            final_init_img[344] = NEW_IMAGE_REFERANCE_BYTES[344] ^ nonce_bytes[2]
            final_init_img[348] = NEW_IMAGE_REFERANCE_BYTES[348] ^ nonce_bytes[2]
            final_init_img[352] = NEW_IMAGE_REFERANCE_BYTES[352] ^ nonce_bytes[2]
            final_init_img[356] = NEW_IMAGE_REFERANCE_BYTES[356] ^ nonce_bytes[2]
            final_init_img[360] = NEW_IMAGE_REFERANCE_BYTES[360] ^ nonce_bytes[2]
            final_init_img[364] = NEW_IMAGE_REFERANCE_BYTES[364] ^ nonce_bytes[2]
            final_init_img[368] = NEW_IMAGE_REFERANCE_BYTES[368] ^ nonce_bytes[2]
            final_init_img[372] = NEW_IMAGE_REFERANCE_BYTES[372] ^ nonce_bytes[2]
            final_init_img[376] = NEW_IMAGE_REFERANCE_BYTES[376] ^ nonce_bytes[2]
            final_init_img[380] = NEW_IMAGE_REFERANCE_BYTES[380] ^ nonce_bytes[2]
            final_init_img[384] = NEW_IMAGE_REFERANCE_BYTES[384] ^ nonce_bytes[2]
            final_init_img[388] = NEW_IMAGE_REFERANCE_BYTES[388] ^ nonce_bytes[2]
            final_init_img[392] = NEW_IMAGE_REFERANCE_BYTES[392] ^ nonce_bytes[2]
            final_init_img[396] = NEW_IMAGE_REFERANCE_BYTES[396] ^ nonce_bytes[2]
            final_init_img[400] = NEW_IMAGE_REFERANCE_BYTES[400] ^ nonce_bytes[2]
            final_init_img[404] = NEW_IMAGE_REFERANCE_BYTES[404] ^ nonce_bytes[2]
            final_init_img[408] = NEW_IMAGE_REFERANCE_BYTES[408] ^ nonce_bytes[2]
            final_init_img[412] = NEW_IMAGE_REFERANCE_BYTES[412] ^ nonce_bytes[2]
            final_init_img[416] = NEW_IMAGE_REFERANCE_BYTES[416] ^ nonce_bytes[2]
            final_init_img[420] = NEW_IMAGE_REFERANCE_BYTES[420] ^ nonce_bytes[2]
            final_init_img[424] = NEW_IMAGE_REFERANCE_BYTES[424] ^ nonce_bytes[2]
            final_init_img[428] = NEW_IMAGE_REFERANCE_BYTES[428] ^ nonce_bytes[2]
            final_init_img[432] = NEW_IMAGE_REFERANCE_BYTES[432] ^ nonce_bytes[2]
            final_init_img[436] = NEW_IMAGE_REFERANCE_BYTES[436] ^ nonce_bytes[2]
            final_init_img[440] = NEW_IMAGE_REFERANCE_BYTES[440] ^ nonce_bytes[2]
            final_init_img[444] = NEW_IMAGE_REFERANCE_BYTES[444] ^ nonce_bytes[2]
            final_init_img[448] = NEW_IMAGE_REFERANCE_BYTES[448] ^ nonce_bytes[2]
            final_init_img[452] = NEW_IMAGE_REFERANCE_BYTES[452] ^ nonce_bytes[2]
            final_init_img[456] = NEW_IMAGE_REFERANCE_BYTES[456] ^ nonce_bytes[2]
            final_init_img[460] = NEW_IMAGE_REFERANCE_BYTES[460] ^ nonce_bytes[2]
            final_init_img[464] = NEW_IMAGE_REFERANCE_BYTES[464] ^ nonce_bytes[2]
            final_init_img[468] = NEW_IMAGE_REFERANCE_BYTES[468] ^ nonce_bytes[2]
            final_init_img[472] = NEW_IMAGE_REFERANCE_BYTES[472] ^ nonce_bytes[2]
            final_init_img[476] = NEW_IMAGE_REFERANCE_BYTES[476] ^ nonce_bytes[2]
            final_init_img[480] = NEW_IMAGE_REFERANCE_BYTES[480] ^ nonce_bytes[2]
            final_init_img[484] = NEW_IMAGE_REFERANCE_BYTES[484] ^ nonce_bytes[2]
            final_init_img[488] = NEW_IMAGE_REFERANCE_BYTES[488] ^ nonce_bytes[2]
            final_init_img[492] = NEW_IMAGE_REFERANCE_BYTES[492] ^ nonce_bytes[2]
            final_init_img[496] = NEW_IMAGE_REFERANCE_BYTES[496] ^ nonce_bytes[2]
            final_init_img[500] = NEW_IMAGE_REFERANCE_BYTES[500] ^ nonce_bytes[2]
            final_init_img[504] = NEW_IMAGE_REFERANCE_BYTES[504] ^ nonce_bytes[2]
            final_init_img[508] = NEW_IMAGE_REFERANCE_BYTES[508] ^ nonce_bytes[2]
            final_init_img[512] = NEW_IMAGE_REFERANCE_BYTES[512] ^ nonce_bytes[2]
            final_init_img[516] = NEW_IMAGE_REFERANCE_BYTES[516] ^ nonce_bytes[2]
            final_init_img[520] = NEW_IMAGE_REFERANCE_BYTES[520] ^ nonce_bytes[2]
            final_init_img[524] = NEW_IMAGE_REFERANCE_BYTES[524] ^ nonce_bytes[2]
            final_init_img[528] = NEW_IMAGE_REFERANCE_BYTES[528] ^ nonce_bytes[2]
            final_init_img[532] = NEW_IMAGE_REFERANCE_BYTES[532] ^ nonce_bytes[2]
            final_init_img[536] = NEW_IMAGE_REFERANCE_BYTES[536] ^ nonce_bytes[2]
            final_init_img[540] = NEW_IMAGE_REFERANCE_BYTES[540] ^ nonce_bytes[2]
            final_init_img[544] = NEW_IMAGE_REFERANCE_BYTES[544] ^ nonce_bytes[2]
            final_init_img[548] = NEW_IMAGE_REFERANCE_BYTES[548] ^ nonce_bytes[2]
            final_init_img[552] = NEW_IMAGE_REFERANCE_BYTES[552] ^ nonce_bytes[2]
            final_init_img[556] = NEW_IMAGE_REFERANCE_BYTES[556] ^ nonce_bytes[2]
            final_init_img[560] = NEW_IMAGE_REFERANCE_BYTES[560] ^ nonce_bytes[2]
            final_init_img[564] = NEW_IMAGE_REFERANCE_BYTES[564] ^ nonce_bytes[2]
            final_init_img[568] = NEW_IMAGE_REFERANCE_BYTES[568] ^ nonce_bytes[2]
            final_init_img[572] = NEW_IMAGE_REFERANCE_BYTES[572] ^ nonce_bytes[2]
            final_init_img[576] = NEW_IMAGE_REFERANCE_BYTES[576] ^ nonce_bytes[2]
            final_init_img[580] = NEW_IMAGE_REFERANCE_BYTES[580] ^ nonce_bytes[2]
            final_init_img[584] = NEW_IMAGE_REFERANCE_BYTES[584] ^ nonce_bytes[2]
            final_init_img[588] = NEW_IMAGE_REFERANCE_BYTES[588] ^ nonce_bytes[2]
            final_init_img[592] = NEW_IMAGE_REFERANCE_BYTES[592] ^ nonce_bytes[2]
            final_init_img[596] = NEW_IMAGE_REFERANCE_BYTES[596] ^ nonce_bytes[2]
            final_init_img[600] = NEW_IMAGE_REFERANCE_BYTES[600] ^ nonce_bytes[2]
            final_init_img[604] = NEW_IMAGE_REFERANCE_BYTES[604] ^ nonce_bytes[2]
            final_init_img[608] = NEW_IMAGE_REFERANCE_BYTES[608] ^ nonce_bytes[2]
            final_init_img[612] = NEW_IMAGE_REFERANCE_BYTES[612] ^ nonce_bytes[2]
            final_init_img[616] = NEW_IMAGE_REFERANCE_BYTES[616] ^ nonce_bytes[2]
            final_init_img[620] = NEW_IMAGE_REFERANCE_BYTES[620] ^ nonce_bytes[2]
            final_init_img[624] = NEW_IMAGE_REFERANCE_BYTES[624] ^ nonce_bytes[2]
            final_init_img[628] = NEW_IMAGE_REFERANCE_BYTES[628] ^ nonce_bytes[2]
            final_init_img[632] = NEW_IMAGE_REFERANCE_BYTES[632] ^ nonce_bytes[2]
            final_init_img[636] = NEW_IMAGE_REFERANCE_BYTES[636] ^ nonce_bytes[2]
            final_init_img[640] = NEW_IMAGE_REFERANCE_BYTES[640] ^ nonce_bytes[2]
            final_init_img[644] = NEW_IMAGE_REFERANCE_BYTES[644] ^ nonce_bytes[2]
            final_init_img[648] = NEW_IMAGE_REFERANCE_BYTES[648] ^ nonce_bytes[2]
            final_init_img[652] = NEW_IMAGE_REFERANCE_BYTES[652] ^ nonce_bytes[2]
            final_init_img[656] = NEW_IMAGE_REFERANCE_BYTES[656] ^ nonce_bytes[2]
            final_init_img[660] = NEW_IMAGE_REFERANCE_BYTES[660] ^ nonce_bytes[2]
            final_init_img[664] = NEW_IMAGE_REFERANCE_BYTES[664] ^ nonce_bytes[2]
            final_init_img[668] = NEW_IMAGE_REFERANCE_BYTES[668] ^ nonce_bytes[2]
            final_init_img[672] = NEW_IMAGE_REFERANCE_BYTES[672] ^ nonce_bytes[2]
            final_init_img[676] = NEW_IMAGE_REFERANCE_BYTES[676] ^ nonce_bytes[2]
            final_init_img[680] = NEW_IMAGE_REFERANCE_BYTES[680] ^ nonce_bytes[2]
            final_init_img[684] = NEW_IMAGE_REFERANCE_BYTES[684] ^ nonce_bytes[2]
            final_init_img[688] = NEW_IMAGE_REFERANCE_BYTES[688] ^ nonce_bytes[2]
            final_init_img[692] = NEW_IMAGE_REFERANCE_BYTES[692] ^ nonce_bytes[2]
            final_init_img[696] = NEW_IMAGE_REFERANCE_BYTES[696] ^ nonce_bytes[2]
            final_init_img[700] = NEW_IMAGE_REFERANCE_BYTES[700] ^ nonce_bytes[2]
            final_init_img[704] = NEW_IMAGE_REFERANCE_BYTES[704] ^ nonce_bytes[2]
            final_init_img[708] = NEW_IMAGE_REFERANCE_BYTES[708] ^ nonce_bytes[2]
            final_init_img[712] = NEW_IMAGE_REFERANCE_BYTES[712] ^ nonce_bytes[2]
            final_init_img[716] = NEW_IMAGE_REFERANCE_BYTES[716] ^ nonce_bytes[2]
            final_init_img[720] = NEW_IMAGE_REFERANCE_BYTES[720] ^ nonce_bytes[2]
            final_init_img[724] = NEW_IMAGE_REFERANCE_BYTES[724] ^ nonce_bytes[2]
            final_init_img[728] = NEW_IMAGE_REFERANCE_BYTES[728] ^ nonce_bytes[2]
            final_init_img[732] = NEW_IMAGE_REFERANCE_BYTES[732] ^ nonce_bytes[2]
            final_init_img[736] = NEW_IMAGE_REFERANCE_BYTES[736] ^ nonce_bytes[2]
            final_init_img[740] = NEW_IMAGE_REFERANCE_BYTES[740] ^ nonce_bytes[2]
            final_init_img[744] = NEW_IMAGE_REFERANCE_BYTES[744] ^ nonce_bytes[2]
            final_init_img[748] = NEW_IMAGE_REFERANCE_BYTES[748] ^ nonce_bytes[2]
            final_init_img[752] = NEW_IMAGE_REFERANCE_BYTES[752] ^ nonce_bytes[2]
            final_init_img[756] = NEW_IMAGE_REFERANCE_BYTES[756] ^ nonce_bytes[2]
            final_init_img[760] = NEW_IMAGE_REFERANCE_BYTES[760] ^ nonce_bytes[2]
            final_init_img[764] = NEW_IMAGE_REFERANCE_BYTES[764] ^ nonce_bytes[2]
            final_init_img[768] = NEW_IMAGE_REFERANCE_BYTES[768] ^ nonce_bytes[2]
            final_init_img[772] = NEW_IMAGE_REFERANCE_BYTES[772] ^ nonce_bytes[2]
            final_init_img[776] = NEW_IMAGE_REFERANCE_BYTES[776] ^ nonce_bytes[2]
            final_init_img[780] = NEW_IMAGE_REFERANCE_BYTES[780] ^ nonce_bytes[2]
            final_init_img[784] = NEW_IMAGE_REFERANCE_BYTES[784] ^ nonce_bytes[2]
            final_init_img[788] = NEW_IMAGE_REFERANCE_BYTES[788] ^ nonce_bytes[2]
            final_init_img[792] = NEW_IMAGE_REFERANCE_BYTES[792] ^ nonce_bytes[2]
            final_init_img[796] = NEW_IMAGE_REFERANCE_BYTES[796] ^ nonce_bytes[2]
            final_init_img[800] = NEW_IMAGE_REFERANCE_BYTES[800] ^ nonce_bytes[2]
            final_init_img[804] = NEW_IMAGE_REFERANCE_BYTES[804] ^ nonce_bytes[2]
            final_init_img[808] = NEW_IMAGE_REFERANCE_BYTES[808] ^ nonce_bytes[2]
            final_init_img[812] = NEW_IMAGE_REFERANCE_BYTES[812] ^ nonce_bytes[2]
            final_init_img[816] = NEW_IMAGE_REFERANCE_BYTES[816] ^ nonce_bytes[2]
            final_init_img[820] = NEW_IMAGE_REFERANCE_BYTES[820] ^ nonce_bytes[2]
            final_init_img[824] = NEW_IMAGE_REFERANCE_BYTES[824] ^ nonce_bytes[2]
            final_init_img[828] = NEW_IMAGE_REFERANCE_BYTES[828] ^ nonce_bytes[2]
            final_init_img[832] = NEW_IMAGE_REFERANCE_BYTES[832] ^ nonce_bytes[2]
            final_init_img[836] = NEW_IMAGE_REFERANCE_BYTES[836] ^ nonce_bytes[2]
            final_init_img[840] = NEW_IMAGE_REFERANCE_BYTES[840] ^ nonce_bytes[2]
            final_init_img[844] = NEW_IMAGE_REFERANCE_BYTES[844] ^ nonce_bytes[2]
            final_init_img[848] = NEW_IMAGE_REFERANCE_BYTES[848] ^ nonce_bytes[2]
            final_init_img[852] = NEW_IMAGE_REFERANCE_BYTES[852] ^ nonce_bytes[2]
            final_init_img[856] = NEW_IMAGE_REFERANCE_BYTES[856] ^ nonce_bytes[2]
            final_init_img[860] = NEW_IMAGE_REFERANCE_BYTES[860] ^ nonce_bytes[2]
            final_init_img[864] = NEW_IMAGE_REFERANCE_BYTES[864] ^ nonce_bytes[2]
            final_init_img[868] = NEW_IMAGE_REFERANCE_BYTES[868] ^ nonce_bytes[2]
            final_init_img[872] = NEW_IMAGE_REFERANCE_BYTES[872] ^ nonce_bytes[2]
            final_init_img[876] = NEW_IMAGE_REFERANCE_BYTES[876] ^ nonce_bytes[2]
            final_init_img[880] = NEW_IMAGE_REFERANCE_BYTES[880] ^ nonce_bytes[2]
            final_init_img[884] = NEW_IMAGE_REFERANCE_BYTES[884] ^ nonce_bytes[2]
            final_init_img[888] = NEW_IMAGE_REFERANCE_BYTES[888] ^ nonce_bytes[2]
            final_init_img[892] = NEW_IMAGE_REFERANCE_BYTES[892] ^ nonce_bytes[2]
            final_init_img[896] = NEW_IMAGE_REFERANCE_BYTES[896] ^ nonce_bytes[2]
            final_init_img[900] = NEW_IMAGE_REFERANCE_BYTES[900] ^ nonce_bytes[2]
            final_init_img[904] = NEW_IMAGE_REFERANCE_BYTES[904] ^ nonce_bytes[2]
            final_init_img[908] = NEW_IMAGE_REFERANCE_BYTES[908] ^ nonce_bytes[2]
            final_init_img[912] = NEW_IMAGE_REFERANCE_BYTES[912] ^ nonce_bytes[2]
            final_init_img[916] = NEW_IMAGE_REFERANCE_BYTES[916] ^ nonce_bytes[2]
            final_init_img[920] = NEW_IMAGE_REFERANCE_BYTES[920] ^ nonce_bytes[2]
            final_init_img[924] = NEW_IMAGE_REFERANCE_BYTES[924] ^ nonce_bytes[2]
            final_init_img[928] = NEW_IMAGE_REFERANCE_BYTES[928] ^ nonce_bytes[2]
            final_init_img[932] = NEW_IMAGE_REFERANCE_BYTES[932] ^ nonce_bytes[2]
            final_init_img[936] = NEW_IMAGE_REFERANCE_BYTES[936] ^ nonce_bytes[2]
            final_init_img[940] = NEW_IMAGE_REFERANCE_BYTES[940] ^ nonce_bytes[2]
            final_init_img[944] = NEW_IMAGE_REFERANCE_BYTES[944] ^ nonce_bytes[2]
            final_init_img[948] = NEW_IMAGE_REFERANCE_BYTES[948] ^ nonce_bytes[2]
            final_init_img[952] = NEW_IMAGE_REFERANCE_BYTES[952] ^ nonce_bytes[2]
            final_init_img[956] = NEW_IMAGE_REFERANCE_BYTES[956] ^ nonce_bytes[2]
            final_init_img[960] = NEW_IMAGE_REFERANCE_BYTES[960] ^ nonce_bytes[2]
            final_init_img[964] = NEW_IMAGE_REFERANCE_BYTES[964] ^ nonce_bytes[2]
            final_init_img[968] = NEW_IMAGE_REFERANCE_BYTES[968] ^ nonce_bytes[2]
            final_init_img[972] = NEW_IMAGE_REFERANCE_BYTES[972] ^ nonce_bytes[2]
            final_init_img[976] = NEW_IMAGE_REFERANCE_BYTES[976] ^ nonce_bytes[2]
            final_init_img[980] = NEW_IMAGE_REFERANCE_BYTES[980] ^ nonce_bytes[2]
            final_init_img[984] = NEW_IMAGE_REFERANCE_BYTES[984] ^ nonce_bytes[2]
            final_init_img[988] = NEW_IMAGE_REFERANCE_BYTES[988] ^ nonce_bytes[2]
            final_init_img[992] = NEW_IMAGE_REFERANCE_BYTES[992] ^ nonce_bytes[2]
            final_init_img[996] = NEW_IMAGE_REFERANCE_BYTES[996] ^ nonce_bytes[2]
            final_init_img[1000] = NEW_IMAGE_REFERANCE_BYTES[1000] ^ nonce_bytes[2]
            final_init_img[1004] = NEW_IMAGE_REFERANCE_BYTES[1004] ^ nonce_bytes[2]
            final_init_img[1008] = NEW_IMAGE_REFERANCE_BYTES[1008] ^ nonce_bytes[2]
            final_init_img[1012] = NEW_IMAGE_REFERANCE_BYTES[1012] ^ nonce_bytes[2]
            final_init_img[1016] = NEW_IMAGE_REFERANCE_BYTES[1016] ^ nonce_bytes[2]
            final_init_img[1020] = NEW_IMAGE_REFERANCE_BYTES[1020] ^ nonce_bytes[2]
            final_init_img[1024] = NEW_IMAGE_REFERANCE_BYTES[1024] ^ nonce_bytes[2]
            final_init_img[1028] = NEW_IMAGE_REFERANCE_BYTES[1028] ^ nonce_bytes[2]
            final_init_img[1032] = NEW_IMAGE_REFERANCE_BYTES[1032] ^ nonce_bytes[2]
            final_init_img[1036] = NEW_IMAGE_REFERANCE_BYTES[1036] ^ nonce_bytes[2]
            final_init_img[1040] = NEW_IMAGE_REFERANCE_BYTES[1040] ^ nonce_bytes[2]
            final_init_img[1044] = NEW_IMAGE_REFERANCE_BYTES[1044] ^ nonce_bytes[2]
            final_init_img[1048] = NEW_IMAGE_REFERANCE_BYTES[1048] ^ nonce_bytes[2]
            final_init_img[1052] = NEW_IMAGE_REFERANCE_BYTES[1052] ^ nonce_bytes[2]
            final_init_img[1056] = NEW_IMAGE_REFERANCE_BYTES[1056] ^ nonce_bytes[2]
            final_init_img[1060] = NEW_IMAGE_REFERANCE_BYTES[1060] ^ nonce_bytes[2]
            final_init_img[1064] = NEW_IMAGE_REFERANCE_BYTES[1064] ^ nonce_bytes[2]
            final_init_img[1068] = NEW_IMAGE_REFERANCE_BYTES[1068] ^ nonce_bytes[2]
            final_init_img[1072] = NEW_IMAGE_REFERANCE_BYTES[1072] ^ nonce_bytes[2]
            final_init_img[1076] = NEW_IMAGE_REFERANCE_BYTES[1076] ^ nonce_bytes[2]
            final_init_img[1080] = NEW_IMAGE_REFERANCE_BYTES[1080] ^ nonce_bytes[2]
            final_init_img[1084] = NEW_IMAGE_REFERANCE_BYTES[1084] ^ nonce_bytes[2]
            final_init_img[1088] = NEW_IMAGE_REFERANCE_BYTES[1088] ^ nonce_bytes[2]
            final_init_img[1092] = NEW_IMAGE_REFERANCE_BYTES[1092] ^ nonce_bytes[2]
            final_init_img[1096] = NEW_IMAGE_REFERANCE_BYTES[1096] ^ nonce_bytes[2]
            final_init_img[1100] = NEW_IMAGE_REFERANCE_BYTES[1100] ^ nonce_bytes[2]
            final_init_img[1104] = NEW_IMAGE_REFERANCE_BYTES[1104] ^ nonce_bytes[2]
            final_init_img[1108] = NEW_IMAGE_REFERANCE_BYTES[1108] ^ nonce_bytes[2]
            final_init_img[1112] = NEW_IMAGE_REFERANCE_BYTES[1112] ^ nonce_bytes[2]
            final_init_img[1116] = NEW_IMAGE_REFERANCE_BYTES[1116] ^ nonce_bytes[2]
            final_init_img[1120] = NEW_IMAGE_REFERANCE_BYTES[1120] ^ nonce_bytes[2]
            final_init_img[1124] = NEW_IMAGE_REFERANCE_BYTES[1124] ^ nonce_bytes[2]
            final_init_img[1128] = NEW_IMAGE_REFERANCE_BYTES[1128] ^ nonce_bytes[2]
            final_init_img[1132] = NEW_IMAGE_REFERANCE_BYTES[1132] ^ nonce_bytes[2]
            final_init_img[1136] = NEW_IMAGE_REFERANCE_BYTES[1136] ^ nonce_bytes[2]
            final_init_img[1140] = NEW_IMAGE_REFERANCE_BYTES[1140] ^ nonce_bytes[2]
            final_init_img[1144] = NEW_IMAGE_REFERANCE_BYTES[1144] ^ nonce_bytes[2]
            final_init_img[1148] = NEW_IMAGE_REFERANCE_BYTES[1148] ^ nonce_bytes[2]
            final_init_img[1152] = NEW_IMAGE_REFERANCE_BYTES[1152] ^ nonce_bytes[2]
            final_init_img[1156] = NEW_IMAGE_REFERANCE_BYTES[1156] ^ nonce_bytes[2]
            final_init_img[1160] = NEW_IMAGE_REFERANCE_BYTES[1160] ^ nonce_bytes[2]
            final_init_img[1164] = NEW_IMAGE_REFERANCE_BYTES[1164] ^ nonce_bytes[2]
            final_init_img[1168] = NEW_IMAGE_REFERANCE_BYTES[1168] ^ nonce_bytes[2]
            final_init_img[1172] = NEW_IMAGE_REFERANCE_BYTES[1172] ^ nonce_bytes[2]
            final_init_img[1176] = NEW_IMAGE_REFERANCE_BYTES[1176] ^ nonce_bytes[2]
            final_init_img[1180] = NEW_IMAGE_REFERANCE_BYTES[1180] ^ nonce_bytes[2]
            final_init_img[1184] = NEW_IMAGE_REFERANCE_BYTES[1184] ^ nonce_bytes[2]
            final_init_img[1188] = NEW_IMAGE_REFERANCE_BYTES[1188] ^ nonce_bytes[2]
            final_init_img[1192] = NEW_IMAGE_REFERANCE_BYTES[1192] ^ nonce_bytes[2]
            final_init_img[1196] = NEW_IMAGE_REFERANCE_BYTES[1196] ^ nonce_bytes[2]
            final_init_img[1200] = NEW_IMAGE_REFERANCE_BYTES[1200] ^ nonce_bytes[2]
            final_init_img[1204] = NEW_IMAGE_REFERANCE_BYTES[1204] ^ nonce_bytes[2]
            final_init_img[1208] = NEW_IMAGE_REFERANCE_BYTES[1208] ^ nonce_bytes[2]
            final_init_img[1212] = NEW_IMAGE_REFERANCE_BYTES[1212] ^ nonce_bytes[2]
            final_init_img[1216] = NEW_IMAGE_REFERANCE_BYTES[1216] ^ nonce_bytes[2]
            final_init_img[1220] = NEW_IMAGE_REFERANCE_BYTES[1220] ^ nonce_bytes[2]
            final_init_img[1224] = NEW_IMAGE_REFERANCE_BYTES[1224] ^ nonce_bytes[2]
            final_init_img[1228] = NEW_IMAGE_REFERANCE_BYTES[1228] ^ nonce_bytes[2]
            final_init_img[1232] = NEW_IMAGE_REFERANCE_BYTES[1232] ^ nonce_bytes[2]
            final_init_img[1236] = NEW_IMAGE_REFERANCE_BYTES[1236] ^ nonce_bytes[2]
            final_init_img[1240] = NEW_IMAGE_REFERANCE_BYTES[1240] ^ nonce_bytes[2]
            final_init_img[1244] = NEW_IMAGE_REFERANCE_BYTES[1244] ^ nonce_bytes[2]
            final_init_img[1248] = NEW_IMAGE_REFERANCE_BYTES[1248] ^ nonce_bytes[2]
            final_init_img[1252] = NEW_IMAGE_REFERANCE_BYTES[1252] ^ nonce_bytes[2]
            final_init_img[1256] = NEW_IMAGE_REFERANCE_BYTES[1256] ^ nonce_bytes[2]
            final_init_img[1260] = NEW_IMAGE_REFERANCE_BYTES[1260] ^ nonce_bytes[2]
            final_init_img[1264] = NEW_IMAGE_REFERANCE_BYTES[1264] ^ nonce_bytes[2]
            final_init_img[1268] = NEW_IMAGE_REFERANCE_BYTES[1268] ^ nonce_bytes[2]
            final_init_img[1272] = NEW_IMAGE_REFERANCE_BYTES[1272] ^ nonce_bytes[2]
            final_init_img[1276] = NEW_IMAGE_REFERANCE_BYTES[1276] ^ nonce_bytes[2]
            final_init_img[1280] = NEW_IMAGE_REFERANCE_BYTES[1280] ^ nonce_bytes[2]
            final_init_img[1284] = NEW_IMAGE_REFERANCE_BYTES[1284] ^ nonce_bytes[2]
            final_init_img[1288] = NEW_IMAGE_REFERANCE_BYTES[1288] ^ nonce_bytes[2]
            final_init_img[1292] = NEW_IMAGE_REFERANCE_BYTES[1292] ^ nonce_bytes[2]
            final_init_img[1296] = NEW_IMAGE_REFERANCE_BYTES[1296] ^ nonce_bytes[2]
            final_init_img[1300] = NEW_IMAGE_REFERANCE_BYTES[1300] ^ nonce_bytes[2]
            final_init_img[1304] = NEW_IMAGE_REFERANCE_BYTES[1304] ^ nonce_bytes[2]
            final_init_img[1308] = NEW_IMAGE_REFERANCE_BYTES[1308] ^ nonce_bytes[2]
            final_init_img[1312] = NEW_IMAGE_REFERANCE_BYTES[1312] ^ nonce_bytes[2]
            final_init_img[1316] = NEW_IMAGE_REFERANCE_BYTES[1316] ^ nonce_bytes[2]
            final_init_img[1320] = NEW_IMAGE_REFERANCE_BYTES[1320] ^ nonce_bytes[2]
            final_init_img[1324] = NEW_IMAGE_REFERANCE_BYTES[1324] ^ nonce_bytes[2]
            final_init_img[1328] = NEW_IMAGE_REFERANCE_BYTES[1328] ^ nonce_bytes[2]
            final_init_img[1332] = NEW_IMAGE_REFERANCE_BYTES[1332] ^ nonce_bytes[2]
            final_init_img[1336] = NEW_IMAGE_REFERANCE_BYTES[1336] ^ nonce_bytes[2]
            final_init_img[1340] = NEW_IMAGE_REFERANCE_BYTES[1340] ^ nonce_bytes[2]
            final_init_img[1344] = NEW_IMAGE_REFERANCE_BYTES[1344] ^ nonce_bytes[2]
            final_init_img[1348] = NEW_IMAGE_REFERANCE_BYTES[1348] ^ nonce_bytes[2]
            final_init_img[1352] = NEW_IMAGE_REFERANCE_BYTES[1352] ^ nonce_bytes[2]
            final_init_img[1356] = NEW_IMAGE_REFERANCE_BYTES[1356] ^ nonce_bytes[2]
            final_init_img[1360] = NEW_IMAGE_REFERANCE_BYTES[1360] ^ nonce_bytes[2]
            final_init_img[1364] = NEW_IMAGE_REFERANCE_BYTES[1364] ^ nonce_bytes[2]
            final_init_img[1368] = NEW_IMAGE_REFERANCE_BYTES[1368] ^ nonce_bytes[2]
            final_init_img[1372] = NEW_IMAGE_REFERANCE_BYTES[1372] ^ nonce_bytes[2]
            final_init_img[1376] = NEW_IMAGE_REFERANCE_BYTES[1376] ^ nonce_bytes[2]
            final_init_img[1380] = NEW_IMAGE_REFERANCE_BYTES[1380] ^ nonce_bytes[2]
            final_init_img[1384] = NEW_IMAGE_REFERANCE_BYTES[1384] ^ nonce_bytes[2]
            final_init_img[1388] = NEW_IMAGE_REFERANCE_BYTES[1388] ^ nonce_bytes[2]
            final_init_img[1392] = NEW_IMAGE_REFERANCE_BYTES[1392] ^ nonce_bytes[2]
            final_init_img[1396] = NEW_IMAGE_REFERANCE_BYTES[1396] ^ nonce_bytes[2]
            final_init_img[1400] = NEW_IMAGE_REFERANCE_BYTES[1400] ^ nonce_bytes[2]
            final_init_img[1404] = NEW_IMAGE_REFERANCE_BYTES[1404] ^ nonce_bytes[2]
            final_init_img[1408] = NEW_IMAGE_REFERANCE_BYTES[1408] ^ nonce_bytes[2]
            final_init_img[1412] = NEW_IMAGE_REFERANCE_BYTES[1412] ^ nonce_bytes[2]
            final_init_img[1416] = NEW_IMAGE_REFERANCE_BYTES[1416] ^ nonce_bytes[2]
            final_init_img[1420] = NEW_IMAGE_REFERANCE_BYTES[1420] ^ nonce_bytes[2]
            final_init_img[1424] = NEW_IMAGE_REFERANCE_BYTES[1424] ^ nonce_bytes[2]
            final_init_img[1428] = NEW_IMAGE_REFERANCE_BYTES[1428] ^ nonce_bytes[2]
            final_init_img[1432] = NEW_IMAGE_REFERANCE_BYTES[1432] ^ nonce_bytes[2]
            final_init_img[1436] = NEW_IMAGE_REFERANCE_BYTES[1436] ^ nonce_bytes[2]
            final_init_img[1440] = NEW_IMAGE_REFERANCE_BYTES[1440] ^ nonce_bytes[2]
            final_init_img[1444] = NEW_IMAGE_REFERANCE_BYTES[1444] ^ nonce_bytes[2]
            final_init_img[1448] = NEW_IMAGE_REFERANCE_BYTES[1448] ^ nonce_bytes[2]
            final_init_img[1452] = NEW_IMAGE_REFERANCE_BYTES[1452] ^ nonce_bytes[2]
            final_init_img[1456] = NEW_IMAGE_REFERANCE_BYTES[1456] ^ nonce_bytes[2]
            final_init_img[1460] = NEW_IMAGE_REFERANCE_BYTES[1460] ^ nonce_bytes[2]
            final_init_img[1464] = NEW_IMAGE_REFERANCE_BYTES[1464] ^ nonce_bytes[2]
            final_init_img[1468] = NEW_IMAGE_REFERANCE_BYTES[1468] ^ nonce_bytes[2]
            final_init_img[1472] = NEW_IMAGE_REFERANCE_BYTES[1472] ^ nonce_bytes[2]
            final_init_img[1476] = NEW_IMAGE_REFERANCE_BYTES[1476] ^ nonce_bytes[2]
            final_init_img[1480] = NEW_IMAGE_REFERANCE_BYTES[1480] ^ nonce_bytes[2]
            final_init_img[1484] = NEW_IMAGE_REFERANCE_BYTES[1484] ^ nonce_bytes[2]
            final_init_img[1488] = NEW_IMAGE_REFERANCE_BYTES[1488] ^ nonce_bytes[2]
            final_init_img[1492] = NEW_IMAGE_REFERANCE_BYTES[1492] ^ nonce_bytes[2]
            final_init_img[1496] = NEW_IMAGE_REFERANCE_BYTES[1496] ^ nonce_bytes[2]
            final_init_img[1500] = NEW_IMAGE_REFERANCE_BYTES[1500] ^ nonce_bytes[2]
            final_init_img[1504] = NEW_IMAGE_REFERANCE_BYTES[1504] ^ nonce_bytes[2]
            final_init_img[1508] = NEW_IMAGE_REFERANCE_BYTES[1508] ^ nonce_bytes[2]
            final_init_img[1512] = NEW_IMAGE_REFERANCE_BYTES[1512] ^ nonce_bytes[2]
            final_init_img[1516] = NEW_IMAGE_REFERANCE_BYTES[1516] ^ nonce_bytes[2]
            final_init_img[1520] = NEW_IMAGE_REFERANCE_BYTES[1520] ^ nonce_bytes[2]
            final_init_img[1524] = NEW_IMAGE_REFERANCE_BYTES[1524] ^ nonce_bytes[2]
            final_init_img[1528] = NEW_IMAGE_REFERANCE_BYTES[1528] ^ nonce_bytes[2]
            final_init_img[1532] = NEW_IMAGE_REFERANCE_BYTES[1532] ^ nonce_bytes[2]
            final_init_img[1536] = NEW_IMAGE_REFERANCE_BYTES[1536] ^ nonce_bytes[2]
            final_init_img[1540] = NEW_IMAGE_REFERANCE_BYTES[1540] ^ nonce_bytes[2]
            final_init_img[1544] = NEW_IMAGE_REFERANCE_BYTES[1544] ^ nonce_bytes[2]
            final_init_img[1548] = NEW_IMAGE_REFERANCE_BYTES[1548] ^ nonce_bytes[2]
            final_init_img[1552] = NEW_IMAGE_REFERANCE_BYTES[1552] ^ nonce_bytes[2]
            final_init_img[1556] = NEW_IMAGE_REFERANCE_BYTES[1556] ^ nonce_bytes[2]
            final_init_img[1560] = NEW_IMAGE_REFERANCE_BYTES[1560] ^ nonce_bytes[2]
            final_init_img[1564] = NEW_IMAGE_REFERANCE_BYTES[1564] ^ nonce_bytes[2]
            final_init_img[1568] = NEW_IMAGE_REFERANCE_BYTES[1568] ^ nonce_bytes[2]
            final_init_img[1572] = NEW_IMAGE_REFERANCE_BYTES[1572] ^ nonce_bytes[2]
            final_init_img[1576] = NEW_IMAGE_REFERANCE_BYTES[1576] ^ nonce_bytes[2]
            final_init_img[1580] = NEW_IMAGE_REFERANCE_BYTES[1580] ^ nonce_bytes[2]
            final_init_img[1584] = NEW_IMAGE_REFERANCE_BYTES[1584] ^ nonce_bytes[2]
            final_init_img[1588] = NEW_IMAGE_REFERANCE_BYTES[1588] ^ nonce_bytes[2]
            final_init_img[1592] = NEW_IMAGE_REFERANCE_BYTES[1592] ^ nonce_bytes[2]
            final_init_img[1596] = NEW_IMAGE_REFERANCE_BYTES[1596] ^ nonce_bytes[2]
            final_init_img[1600] = NEW_IMAGE_REFERANCE_BYTES[1600] ^ nonce_bytes[2]
            final_init_img[1604] = NEW_IMAGE_REFERANCE_BYTES[1604] ^ nonce_bytes[2]
            final_init_img[1608] = NEW_IMAGE_REFERANCE_BYTES[1608] ^ nonce_bytes[2]
            final_init_img[1612] = NEW_IMAGE_REFERANCE_BYTES[1612] ^ nonce_bytes[2]
            final_init_img[1616] = NEW_IMAGE_REFERANCE_BYTES[1616] ^ nonce_bytes[2]
            final_init_img[1620] = NEW_IMAGE_REFERANCE_BYTES[1620] ^ nonce_bytes[2]
            final_init_img[1624] = NEW_IMAGE_REFERANCE_BYTES[1624] ^ nonce_bytes[2]
            final_init_img[1628] = NEW_IMAGE_REFERANCE_BYTES[1628] ^ nonce_bytes[2]
            final_init_img[1632] = NEW_IMAGE_REFERANCE_BYTES[1632] ^ nonce_bytes[2]
            final_init_img[1636] = NEW_IMAGE_REFERANCE_BYTES[1636] ^ nonce_bytes[2]
            final_init_img[1640] = NEW_IMAGE_REFERANCE_BYTES[1640] ^ nonce_bytes[2]
            final_init_img[1644] = NEW_IMAGE_REFERANCE_BYTES[1644] ^ nonce_bytes[2]
            final_init_img[1648] = NEW_IMAGE_REFERANCE_BYTES[1648] ^ nonce_bytes[2]
            final_init_img[1652] = NEW_IMAGE_REFERANCE_BYTES[1652] ^ nonce_bytes[2]
            final_init_img[1656] = NEW_IMAGE_REFERANCE_BYTES[1656] ^ nonce_bytes[2]
            final_init_img[1660] = NEW_IMAGE_REFERANCE_BYTES[1660] ^ nonce_bytes[2]
            final_init_img[1664] = NEW_IMAGE_REFERANCE_BYTES[1664] ^ nonce_bytes[2]
            final_init_img[1668] = NEW_IMAGE_REFERANCE_BYTES[1668] ^ nonce_bytes[2]
            final_init_img[1672] = NEW_IMAGE_REFERANCE_BYTES[1672] ^ nonce_bytes[2]
            final_init_img[1676] = NEW_IMAGE_REFERANCE_BYTES[1676] ^ nonce_bytes[2]
            final_init_img[1680] = NEW_IMAGE_REFERANCE_BYTES[1680] ^ nonce_bytes[2]
            final_init_img[1684] = NEW_IMAGE_REFERANCE_BYTES[1684] ^ nonce_bytes[2]
            final_init_img[1688] = NEW_IMAGE_REFERANCE_BYTES[1688] ^ nonce_bytes[2]
            final_init_img[1692] = NEW_IMAGE_REFERANCE_BYTES[1692] ^ nonce_bytes[2]
            final_init_img[1696] = NEW_IMAGE_REFERANCE_BYTES[1696] ^ nonce_bytes[2]
            final_init_img[1700] = NEW_IMAGE_REFERANCE_BYTES[1700] ^ nonce_bytes[2]
            final_init_img[1704] = NEW_IMAGE_REFERANCE_BYTES[1704] ^ nonce_bytes[2]
            final_init_img[1708] = NEW_IMAGE_REFERANCE_BYTES[1708] ^ nonce_bytes[2]
            final_init_img[1712] = NEW_IMAGE_REFERANCE_BYTES[1712] ^ nonce_bytes[2]
            final_init_img[1716] = NEW_IMAGE_REFERANCE_BYTES[1716] ^ nonce_bytes[2]
            final_init_img[1720] = NEW_IMAGE_REFERANCE_BYTES[1720] ^ nonce_bytes[2]
            final_init_img[1724] = NEW_IMAGE_REFERANCE_BYTES[1724] ^ nonce_bytes[2]
            final_init_img[1728] = NEW_IMAGE_REFERANCE_BYTES[1728] ^ nonce_bytes[2]
            final_init_img[1732] = NEW_IMAGE_REFERANCE_BYTES[1732] ^ nonce_bytes[2]
            final_init_img[1736] = NEW_IMAGE_REFERANCE_BYTES[1736] ^ nonce_bytes[2]
            final_init_img[1740] = NEW_IMAGE_REFERANCE_BYTES[1740] ^ nonce_bytes[2]
            final_init_img[1744] = NEW_IMAGE_REFERANCE_BYTES[1744] ^ nonce_bytes[2]
            final_init_img[1748] = NEW_IMAGE_REFERANCE_BYTES[1748] ^ nonce_bytes[2]
            final_init_img[1752] = NEW_IMAGE_REFERANCE_BYTES[1752] ^ nonce_bytes[2]
            final_init_img[1756] = NEW_IMAGE_REFERANCE_BYTES[1756] ^ nonce_bytes[2]
            final_init_img[1760] = NEW_IMAGE_REFERANCE_BYTES[1760] ^ nonce_bytes[2]
            final_init_img[1764] = NEW_IMAGE_REFERANCE_BYTES[1764] ^ nonce_bytes[2]
            final_init_img[1768] = NEW_IMAGE_REFERANCE_BYTES[1768] ^ nonce_bytes[2]
            final_init_img[1772] = NEW_IMAGE_REFERANCE_BYTES[1772] ^ nonce_bytes[2]
            final_init_img[1776] = NEW_IMAGE_REFERANCE_BYTES[1776] ^ nonce_bytes[2]
            final_init_img[1780] = NEW_IMAGE_REFERANCE_BYTES[1780] ^ nonce_bytes[2]
      


        if nlastbyte3 != nonce_bytes[3]:
            nlastbyte3 = nonce_bytes[3]
            final_init_img[57] = NEW_IMAGE_REFERANCE_BYTES[57] ^ nonce_bytes[3]
            final_init_img[61] = NEW_IMAGE_REFERANCE_BYTES[61] ^ nonce_bytes[3]
            final_init_img[65] = NEW_IMAGE_REFERANCE_BYTES[65] ^ nonce_bytes[3]
            final_init_img[69] = NEW_IMAGE_REFERANCE_BYTES[69] ^ nonce_bytes[3]
            final_init_img[73] = NEW_IMAGE_REFERANCE_BYTES[73] ^ nonce_bytes[3]
            final_init_img[77] = NEW_IMAGE_REFERANCE_BYTES[77] ^ nonce_bytes[3]
            final_init_img[81] = NEW_IMAGE_REFERANCE_BYTES[81] ^ nonce_bytes[3]
            final_init_img[85] = NEW_IMAGE_REFERANCE_BYTES[85] ^ nonce_bytes[3]
            final_init_img[89] = NEW_IMAGE_REFERANCE_BYTES[89] ^ nonce_bytes[3]
            final_init_img[93] = NEW_IMAGE_REFERANCE_BYTES[93] ^ nonce_bytes[3]
            final_init_img[97] = NEW_IMAGE_REFERANCE_BYTES[97] ^ nonce_bytes[3]
            final_init_img[101] = NEW_IMAGE_REFERANCE_BYTES[101] ^ nonce_bytes[3]
            final_init_img[105] = NEW_IMAGE_REFERANCE_BYTES[105] ^ nonce_bytes[3]
            final_init_img[109] = NEW_IMAGE_REFERANCE_BYTES[109] ^ nonce_bytes[3]
            final_init_img[113] = NEW_IMAGE_REFERANCE_BYTES[113] ^ nonce_bytes[3]
            final_init_img[117] = NEW_IMAGE_REFERANCE_BYTES[117] ^ nonce_bytes[3]
            final_init_img[121] = NEW_IMAGE_REFERANCE_BYTES[121] ^ nonce_bytes[3]
            final_init_img[125] = NEW_IMAGE_REFERANCE_BYTES[125] ^ nonce_bytes[3]
            final_init_img[129] = NEW_IMAGE_REFERANCE_BYTES[129] ^ nonce_bytes[3]
            final_init_img[133] = NEW_IMAGE_REFERANCE_BYTES[133] ^ nonce_bytes[3]
            final_init_img[137] = NEW_IMAGE_REFERANCE_BYTES[137] ^ nonce_bytes[3]
            final_init_img[141] = NEW_IMAGE_REFERANCE_BYTES[141] ^ nonce_bytes[3]
            final_init_img[145] = NEW_IMAGE_REFERANCE_BYTES[145] ^ nonce_bytes[3]
            final_init_img[149] = NEW_IMAGE_REFERANCE_BYTES[149] ^ nonce_bytes[3]
            final_init_img[153] = NEW_IMAGE_REFERANCE_BYTES[153] ^ nonce_bytes[3]
            final_init_img[157] = NEW_IMAGE_REFERANCE_BYTES[157] ^ nonce_bytes[3]
            final_init_img[161] = NEW_IMAGE_REFERANCE_BYTES[161] ^ nonce_bytes[3]
            final_init_img[165] = NEW_IMAGE_REFERANCE_BYTES[165] ^ nonce_bytes[3]
            final_init_img[169] = NEW_IMAGE_REFERANCE_BYTES[169] ^ nonce_bytes[3]
            final_init_img[173] = NEW_IMAGE_REFERANCE_BYTES[173] ^ nonce_bytes[3]
            final_init_img[177] = NEW_IMAGE_REFERANCE_BYTES[177] ^ nonce_bytes[3]
            final_init_img[181] = NEW_IMAGE_REFERANCE_BYTES[181] ^ nonce_bytes[3]
            final_init_img[185] = NEW_IMAGE_REFERANCE_BYTES[185] ^ nonce_bytes[3]
            final_init_img[189] = NEW_IMAGE_REFERANCE_BYTES[189] ^ nonce_bytes[3]
            final_init_img[193] = NEW_IMAGE_REFERANCE_BYTES[193] ^ nonce_bytes[3]
            final_init_img[197] = NEW_IMAGE_REFERANCE_BYTES[197] ^ nonce_bytes[3]
            final_init_img[201] = NEW_IMAGE_REFERANCE_BYTES[201] ^ nonce_bytes[3]
            final_init_img[205] = NEW_IMAGE_REFERANCE_BYTES[205] ^ nonce_bytes[3]
            final_init_img[209] = NEW_IMAGE_REFERANCE_BYTES[209] ^ nonce_bytes[3]
            final_init_img[213] = NEW_IMAGE_REFERANCE_BYTES[213] ^ nonce_bytes[3]
            final_init_img[217] = NEW_IMAGE_REFERANCE_BYTES[217] ^ nonce_bytes[3]
            final_init_img[221] = NEW_IMAGE_REFERANCE_BYTES[221] ^ nonce_bytes[3]
            final_init_img[225] = NEW_IMAGE_REFERANCE_BYTES[225] ^ nonce_bytes[3]
            final_init_img[229] = NEW_IMAGE_REFERANCE_BYTES[229] ^ nonce_bytes[3]
            final_init_img[233] = NEW_IMAGE_REFERANCE_BYTES[233] ^ nonce_bytes[3]
            final_init_img[237] = NEW_IMAGE_REFERANCE_BYTES[237] ^ nonce_bytes[3]
            final_init_img[241] = NEW_IMAGE_REFERANCE_BYTES[241] ^ nonce_bytes[3]
            final_init_img[245] = NEW_IMAGE_REFERANCE_BYTES[245] ^ nonce_bytes[3]
            final_init_img[249] = NEW_IMAGE_REFERANCE_BYTES[249] ^ nonce_bytes[3]
            final_init_img[253] = NEW_IMAGE_REFERANCE_BYTES[253] ^ nonce_bytes[3]
            final_init_img[257] = NEW_IMAGE_REFERANCE_BYTES[257] ^ nonce_bytes[3]
            final_init_img[261] = NEW_IMAGE_REFERANCE_BYTES[261] ^ nonce_bytes[3]
            final_init_img[265] = NEW_IMAGE_REFERANCE_BYTES[265] ^ nonce_bytes[3]
            final_init_img[269] = NEW_IMAGE_REFERANCE_BYTES[269] ^ nonce_bytes[3]
            final_init_img[273] = NEW_IMAGE_REFERANCE_BYTES[273] ^ nonce_bytes[3]
            final_init_img[277] = NEW_IMAGE_REFERANCE_BYTES[277] ^ nonce_bytes[3]
            final_init_img[281] = NEW_IMAGE_REFERANCE_BYTES[281] ^ nonce_bytes[3]
            final_init_img[285] = NEW_IMAGE_REFERANCE_BYTES[285] ^ nonce_bytes[3]
            final_init_img[289] = NEW_IMAGE_REFERANCE_BYTES[289] ^ nonce_bytes[3]
            final_init_img[293] = NEW_IMAGE_REFERANCE_BYTES[293] ^ nonce_bytes[3]
            final_init_img[297] = NEW_IMAGE_REFERANCE_BYTES[297] ^ nonce_bytes[3]
            final_init_img[301] = NEW_IMAGE_REFERANCE_BYTES[301] ^ nonce_bytes[3]
            final_init_img[305] = NEW_IMAGE_REFERANCE_BYTES[305] ^ nonce_bytes[3]
            final_init_img[309] = NEW_IMAGE_REFERANCE_BYTES[309] ^ nonce_bytes[3]
            final_init_img[313] = NEW_IMAGE_REFERANCE_BYTES[313] ^ nonce_bytes[3]
            final_init_img[317] = NEW_IMAGE_REFERANCE_BYTES[317] ^ nonce_bytes[3]
            final_init_img[321] = NEW_IMAGE_REFERANCE_BYTES[321] ^ nonce_bytes[3]
            final_init_img[325] = NEW_IMAGE_REFERANCE_BYTES[325] ^ nonce_bytes[3]
            final_init_img[329] = NEW_IMAGE_REFERANCE_BYTES[329] ^ nonce_bytes[3]
            final_init_img[333] = NEW_IMAGE_REFERANCE_BYTES[333] ^ nonce_bytes[3]
            final_init_img[337] = NEW_IMAGE_REFERANCE_BYTES[337] ^ nonce_bytes[3]
            final_init_img[341] = NEW_IMAGE_REFERANCE_BYTES[341] ^ nonce_bytes[3]
            final_init_img[345] = NEW_IMAGE_REFERANCE_BYTES[345] ^ nonce_bytes[3]
            final_init_img[349] = NEW_IMAGE_REFERANCE_BYTES[349] ^ nonce_bytes[3]
            final_init_img[353] = NEW_IMAGE_REFERANCE_BYTES[353] ^ nonce_bytes[3]
            final_init_img[357] = NEW_IMAGE_REFERANCE_BYTES[357] ^ nonce_bytes[3]
            final_init_img[361] = NEW_IMAGE_REFERANCE_BYTES[361] ^ nonce_bytes[3]
            final_init_img[365] = NEW_IMAGE_REFERANCE_BYTES[365] ^ nonce_bytes[3]
            final_init_img[369] = NEW_IMAGE_REFERANCE_BYTES[369] ^ nonce_bytes[3]
            final_init_img[373] = NEW_IMAGE_REFERANCE_BYTES[373] ^ nonce_bytes[3]
            final_init_img[377] = NEW_IMAGE_REFERANCE_BYTES[377] ^ nonce_bytes[3]
            final_init_img[381] = NEW_IMAGE_REFERANCE_BYTES[381] ^ nonce_bytes[3]
            final_init_img[385] = NEW_IMAGE_REFERANCE_BYTES[385] ^ nonce_bytes[3]
            final_init_img[389] = NEW_IMAGE_REFERANCE_BYTES[389] ^ nonce_bytes[3]
            final_init_img[393] = NEW_IMAGE_REFERANCE_BYTES[393] ^ nonce_bytes[3]
            final_init_img[397] = NEW_IMAGE_REFERANCE_BYTES[397] ^ nonce_bytes[3]
            final_init_img[401] = NEW_IMAGE_REFERANCE_BYTES[401] ^ nonce_bytes[3]
            final_init_img[405] = NEW_IMAGE_REFERANCE_BYTES[405] ^ nonce_bytes[3]
            final_init_img[409] = NEW_IMAGE_REFERANCE_BYTES[409] ^ nonce_bytes[3]
            final_init_img[413] = NEW_IMAGE_REFERANCE_BYTES[413] ^ nonce_bytes[3]
            final_init_img[417] = NEW_IMAGE_REFERANCE_BYTES[417] ^ nonce_bytes[3]
            final_init_img[421] = NEW_IMAGE_REFERANCE_BYTES[421] ^ nonce_bytes[3]
            final_init_img[425] = NEW_IMAGE_REFERANCE_BYTES[425] ^ nonce_bytes[3]
            final_init_img[429] = NEW_IMAGE_REFERANCE_BYTES[429] ^ nonce_bytes[3]
            final_init_img[433] = NEW_IMAGE_REFERANCE_BYTES[433] ^ nonce_bytes[3]
            final_init_img[437] = NEW_IMAGE_REFERANCE_BYTES[437] ^ nonce_bytes[3]
            final_init_img[441] = NEW_IMAGE_REFERANCE_BYTES[441] ^ nonce_bytes[3]
            final_init_img[445] = NEW_IMAGE_REFERANCE_BYTES[445] ^ nonce_bytes[3]
            final_init_img[449] = NEW_IMAGE_REFERANCE_BYTES[449] ^ nonce_bytes[3]
            final_init_img[453] = NEW_IMAGE_REFERANCE_BYTES[453] ^ nonce_bytes[3]
            final_init_img[457] = NEW_IMAGE_REFERANCE_BYTES[457] ^ nonce_bytes[3]
            final_init_img[461] = NEW_IMAGE_REFERANCE_BYTES[461] ^ nonce_bytes[3]
            final_init_img[465] = NEW_IMAGE_REFERANCE_BYTES[465] ^ nonce_bytes[3]
            final_init_img[469] = NEW_IMAGE_REFERANCE_BYTES[469] ^ nonce_bytes[3]
            final_init_img[473] = NEW_IMAGE_REFERANCE_BYTES[473] ^ nonce_bytes[3]
            final_init_img[477] = NEW_IMAGE_REFERANCE_BYTES[477] ^ nonce_bytes[3]
            final_init_img[481] = NEW_IMAGE_REFERANCE_BYTES[481] ^ nonce_bytes[3]
            final_init_img[485] = NEW_IMAGE_REFERANCE_BYTES[485] ^ nonce_bytes[3]
            final_init_img[489] = NEW_IMAGE_REFERANCE_BYTES[489] ^ nonce_bytes[3]
            final_init_img[493] = NEW_IMAGE_REFERANCE_BYTES[493] ^ nonce_bytes[3]
            final_init_img[497] = NEW_IMAGE_REFERANCE_BYTES[497] ^ nonce_bytes[3]
            final_init_img[501] = NEW_IMAGE_REFERANCE_BYTES[501] ^ nonce_bytes[3]
            final_init_img[505] = NEW_IMAGE_REFERANCE_BYTES[505] ^ nonce_bytes[3]
            final_init_img[509] = NEW_IMAGE_REFERANCE_BYTES[509] ^ nonce_bytes[3]
            final_init_img[513] = NEW_IMAGE_REFERANCE_BYTES[513] ^ nonce_bytes[3]
            final_init_img[517] = NEW_IMAGE_REFERANCE_BYTES[517] ^ nonce_bytes[3]
            final_init_img[521] = NEW_IMAGE_REFERANCE_BYTES[521] ^ nonce_bytes[3]
            final_init_img[525] = NEW_IMAGE_REFERANCE_BYTES[525] ^ nonce_bytes[3]
            final_init_img[529] = NEW_IMAGE_REFERANCE_BYTES[529] ^ nonce_bytes[3]
            final_init_img[533] = NEW_IMAGE_REFERANCE_BYTES[533] ^ nonce_bytes[3]
            final_init_img[537] = NEW_IMAGE_REFERANCE_BYTES[537] ^ nonce_bytes[3]
            final_init_img[541] = NEW_IMAGE_REFERANCE_BYTES[541] ^ nonce_bytes[3]
            final_init_img[545] = NEW_IMAGE_REFERANCE_BYTES[545] ^ nonce_bytes[3]
            final_init_img[549] = NEW_IMAGE_REFERANCE_BYTES[549] ^ nonce_bytes[3]
            final_init_img[553] = NEW_IMAGE_REFERANCE_BYTES[553] ^ nonce_bytes[3]
            final_init_img[557] = NEW_IMAGE_REFERANCE_BYTES[557] ^ nonce_bytes[3]
            final_init_img[561] = NEW_IMAGE_REFERANCE_BYTES[561] ^ nonce_bytes[3]
            final_init_img[565] = NEW_IMAGE_REFERANCE_BYTES[565] ^ nonce_bytes[3]
            final_init_img[569] = NEW_IMAGE_REFERANCE_BYTES[569] ^ nonce_bytes[3]
            final_init_img[573] = NEW_IMAGE_REFERANCE_BYTES[573] ^ nonce_bytes[3]
            final_init_img[577] = NEW_IMAGE_REFERANCE_BYTES[577] ^ nonce_bytes[3]
            final_init_img[581] = NEW_IMAGE_REFERANCE_BYTES[581] ^ nonce_bytes[3]
            final_init_img[585] = NEW_IMAGE_REFERANCE_BYTES[585] ^ nonce_bytes[3]
            final_init_img[589] = NEW_IMAGE_REFERANCE_BYTES[589] ^ nonce_bytes[3]
            final_init_img[593] = NEW_IMAGE_REFERANCE_BYTES[593] ^ nonce_bytes[3]
            final_init_img[597] = NEW_IMAGE_REFERANCE_BYTES[597] ^ nonce_bytes[3]
            final_init_img[601] = NEW_IMAGE_REFERANCE_BYTES[601] ^ nonce_bytes[3]
            final_init_img[605] = NEW_IMAGE_REFERANCE_BYTES[605] ^ nonce_bytes[3]
            final_init_img[609] = NEW_IMAGE_REFERANCE_BYTES[609] ^ nonce_bytes[3]
            final_init_img[613] = NEW_IMAGE_REFERANCE_BYTES[613] ^ nonce_bytes[3]
            final_init_img[617] = NEW_IMAGE_REFERANCE_BYTES[617] ^ nonce_bytes[3]
            final_init_img[621] = NEW_IMAGE_REFERANCE_BYTES[621] ^ nonce_bytes[3]
            final_init_img[625] = NEW_IMAGE_REFERANCE_BYTES[625] ^ nonce_bytes[3]
            final_init_img[629] = NEW_IMAGE_REFERANCE_BYTES[629] ^ nonce_bytes[3]
            final_init_img[633] = NEW_IMAGE_REFERANCE_BYTES[633] ^ nonce_bytes[3]
            final_init_img[637] = NEW_IMAGE_REFERANCE_BYTES[637] ^ nonce_bytes[3]
            final_init_img[641] = NEW_IMAGE_REFERANCE_BYTES[641] ^ nonce_bytes[3]
            final_init_img[645] = NEW_IMAGE_REFERANCE_BYTES[645] ^ nonce_bytes[3]
            final_init_img[649] = NEW_IMAGE_REFERANCE_BYTES[649] ^ nonce_bytes[3]
            final_init_img[653] = NEW_IMAGE_REFERANCE_BYTES[653] ^ nonce_bytes[3]
            final_init_img[657] = NEW_IMAGE_REFERANCE_BYTES[657] ^ nonce_bytes[3]
            final_init_img[661] = NEW_IMAGE_REFERANCE_BYTES[661] ^ nonce_bytes[3]
            final_init_img[665] = NEW_IMAGE_REFERANCE_BYTES[665] ^ nonce_bytes[3]
            final_init_img[669] = NEW_IMAGE_REFERANCE_BYTES[669] ^ nonce_bytes[3]
            final_init_img[673] = NEW_IMAGE_REFERANCE_BYTES[673] ^ nonce_bytes[3]
            final_init_img[677] = NEW_IMAGE_REFERANCE_BYTES[677] ^ nonce_bytes[3]
            final_init_img[681] = NEW_IMAGE_REFERANCE_BYTES[681] ^ nonce_bytes[3]
            final_init_img[685] = NEW_IMAGE_REFERANCE_BYTES[685] ^ nonce_bytes[3]
            final_init_img[689] = NEW_IMAGE_REFERANCE_BYTES[689] ^ nonce_bytes[3]
            final_init_img[693] = NEW_IMAGE_REFERANCE_BYTES[693] ^ nonce_bytes[3]
            final_init_img[697] = NEW_IMAGE_REFERANCE_BYTES[697] ^ nonce_bytes[3]
            final_init_img[701] = NEW_IMAGE_REFERANCE_BYTES[701] ^ nonce_bytes[3]
            final_init_img[705] = NEW_IMAGE_REFERANCE_BYTES[705] ^ nonce_bytes[3]
            final_init_img[709] = NEW_IMAGE_REFERANCE_BYTES[709] ^ nonce_bytes[3]
            final_init_img[713] = NEW_IMAGE_REFERANCE_BYTES[713] ^ nonce_bytes[3]
            final_init_img[717] = NEW_IMAGE_REFERANCE_BYTES[717] ^ nonce_bytes[3]
            final_init_img[721] = NEW_IMAGE_REFERANCE_BYTES[721] ^ nonce_bytes[3]
            final_init_img[725] = NEW_IMAGE_REFERANCE_BYTES[725] ^ nonce_bytes[3]
            final_init_img[729] = NEW_IMAGE_REFERANCE_BYTES[729] ^ nonce_bytes[3]
            final_init_img[733] = NEW_IMAGE_REFERANCE_BYTES[733] ^ nonce_bytes[3]
            final_init_img[737] = NEW_IMAGE_REFERANCE_BYTES[737] ^ nonce_bytes[3]
            final_init_img[741] = NEW_IMAGE_REFERANCE_BYTES[741] ^ nonce_bytes[3]
            final_init_img[745] = NEW_IMAGE_REFERANCE_BYTES[745] ^ nonce_bytes[3]
            final_init_img[749] = NEW_IMAGE_REFERANCE_BYTES[749] ^ nonce_bytes[3]
            final_init_img[753] = NEW_IMAGE_REFERANCE_BYTES[753] ^ nonce_bytes[3]
            final_init_img[757] = NEW_IMAGE_REFERANCE_BYTES[757] ^ nonce_bytes[3]
            final_init_img[761] = NEW_IMAGE_REFERANCE_BYTES[761] ^ nonce_bytes[3]
            final_init_img[765] = NEW_IMAGE_REFERANCE_BYTES[765] ^ nonce_bytes[3]
            final_init_img[769] = NEW_IMAGE_REFERANCE_BYTES[769] ^ nonce_bytes[3]
            final_init_img[773] = NEW_IMAGE_REFERANCE_BYTES[773] ^ nonce_bytes[3]
            final_init_img[777] = NEW_IMAGE_REFERANCE_BYTES[777] ^ nonce_bytes[3]
            final_init_img[781] = NEW_IMAGE_REFERANCE_BYTES[781] ^ nonce_bytes[3]
            final_init_img[785] = NEW_IMAGE_REFERANCE_BYTES[785] ^ nonce_bytes[3]
            final_init_img[789] = NEW_IMAGE_REFERANCE_BYTES[789] ^ nonce_bytes[3]
            final_init_img[793] = NEW_IMAGE_REFERANCE_BYTES[793] ^ nonce_bytes[3]
            final_init_img[797] = NEW_IMAGE_REFERANCE_BYTES[797] ^ nonce_bytes[3]
            final_init_img[801] = NEW_IMAGE_REFERANCE_BYTES[801] ^ nonce_bytes[3]
            final_init_img[805] = NEW_IMAGE_REFERANCE_BYTES[805] ^ nonce_bytes[3]
            final_init_img[809] = NEW_IMAGE_REFERANCE_BYTES[809] ^ nonce_bytes[3]
            final_init_img[813] = NEW_IMAGE_REFERANCE_BYTES[813] ^ nonce_bytes[3]
            final_init_img[817] = NEW_IMAGE_REFERANCE_BYTES[817] ^ nonce_bytes[3]
            final_init_img[821] = NEW_IMAGE_REFERANCE_BYTES[821] ^ nonce_bytes[3]
            final_init_img[825] = NEW_IMAGE_REFERANCE_BYTES[825] ^ nonce_bytes[3]
            final_init_img[829] = NEW_IMAGE_REFERANCE_BYTES[829] ^ nonce_bytes[3]
            final_init_img[833] = NEW_IMAGE_REFERANCE_BYTES[833] ^ nonce_bytes[3]
            final_init_img[837] = NEW_IMAGE_REFERANCE_BYTES[837] ^ nonce_bytes[3]
            final_init_img[841] = NEW_IMAGE_REFERANCE_BYTES[841] ^ nonce_bytes[3]
            final_init_img[845] = NEW_IMAGE_REFERANCE_BYTES[845] ^ nonce_bytes[3]
            final_init_img[849] = NEW_IMAGE_REFERANCE_BYTES[849] ^ nonce_bytes[3]
            final_init_img[853] = NEW_IMAGE_REFERANCE_BYTES[853] ^ nonce_bytes[3]
            final_init_img[857] = NEW_IMAGE_REFERANCE_BYTES[857] ^ nonce_bytes[3]
            final_init_img[861] = NEW_IMAGE_REFERANCE_BYTES[861] ^ nonce_bytes[3]
            final_init_img[865] = NEW_IMAGE_REFERANCE_BYTES[865] ^ nonce_bytes[3]
            final_init_img[869] = NEW_IMAGE_REFERANCE_BYTES[869] ^ nonce_bytes[3]
            final_init_img[873] = NEW_IMAGE_REFERANCE_BYTES[873] ^ nonce_bytes[3]
            final_init_img[877] = NEW_IMAGE_REFERANCE_BYTES[877] ^ nonce_bytes[3]
            final_init_img[881] = NEW_IMAGE_REFERANCE_BYTES[881] ^ nonce_bytes[3]
            final_init_img[885] = NEW_IMAGE_REFERANCE_BYTES[885] ^ nonce_bytes[3]
            final_init_img[889] = NEW_IMAGE_REFERANCE_BYTES[889] ^ nonce_bytes[3]
            final_init_img[893] = NEW_IMAGE_REFERANCE_BYTES[893] ^ nonce_bytes[3]
            final_init_img[897] = NEW_IMAGE_REFERANCE_BYTES[897] ^ nonce_bytes[3]
            final_init_img[901] = NEW_IMAGE_REFERANCE_BYTES[901] ^ nonce_bytes[3]
            final_init_img[905] = NEW_IMAGE_REFERANCE_BYTES[905] ^ nonce_bytes[3]
            final_init_img[909] = NEW_IMAGE_REFERANCE_BYTES[909] ^ nonce_bytes[3]
            final_init_img[913] = NEW_IMAGE_REFERANCE_BYTES[913] ^ nonce_bytes[3]
            final_init_img[917] = NEW_IMAGE_REFERANCE_BYTES[917] ^ nonce_bytes[3]
            final_init_img[921] = NEW_IMAGE_REFERANCE_BYTES[921] ^ nonce_bytes[3]
            final_init_img[925] = NEW_IMAGE_REFERANCE_BYTES[925] ^ nonce_bytes[3]
            final_init_img[929] = NEW_IMAGE_REFERANCE_BYTES[929] ^ nonce_bytes[3]
            final_init_img[933] = NEW_IMAGE_REFERANCE_BYTES[933] ^ nonce_bytes[3]
            final_init_img[937] = NEW_IMAGE_REFERANCE_BYTES[937] ^ nonce_bytes[3]
            final_init_img[941] = NEW_IMAGE_REFERANCE_BYTES[941] ^ nonce_bytes[3]
            final_init_img[945] = NEW_IMAGE_REFERANCE_BYTES[945] ^ nonce_bytes[3]
            final_init_img[949] = NEW_IMAGE_REFERANCE_BYTES[949] ^ nonce_bytes[3]
            final_init_img[953] = NEW_IMAGE_REFERANCE_BYTES[953] ^ nonce_bytes[3]
            final_init_img[957] = NEW_IMAGE_REFERANCE_BYTES[957] ^ nonce_bytes[3]
            final_init_img[961] = NEW_IMAGE_REFERANCE_BYTES[961] ^ nonce_bytes[3]
            final_init_img[965] = NEW_IMAGE_REFERANCE_BYTES[965] ^ nonce_bytes[3]
            final_init_img[969] = NEW_IMAGE_REFERANCE_BYTES[969] ^ nonce_bytes[3]
            final_init_img[973] = NEW_IMAGE_REFERANCE_BYTES[973] ^ nonce_bytes[3]
            final_init_img[977] = NEW_IMAGE_REFERANCE_BYTES[977] ^ nonce_bytes[3]
            final_init_img[981] = NEW_IMAGE_REFERANCE_BYTES[981] ^ nonce_bytes[3]
            final_init_img[985] = NEW_IMAGE_REFERANCE_BYTES[985] ^ nonce_bytes[3]
            final_init_img[989] = NEW_IMAGE_REFERANCE_BYTES[989] ^ nonce_bytes[3]
            final_init_img[993] = NEW_IMAGE_REFERANCE_BYTES[993] ^ nonce_bytes[3]
            final_init_img[997] = NEW_IMAGE_REFERANCE_BYTES[997] ^ nonce_bytes[3]
            final_init_img[1001] = NEW_IMAGE_REFERANCE_BYTES[1001] ^ nonce_bytes[3]
            final_init_img[1005] = NEW_IMAGE_REFERANCE_BYTES[1005] ^ nonce_bytes[3]
            final_init_img[1009] = NEW_IMAGE_REFERANCE_BYTES[1009] ^ nonce_bytes[3]
            final_init_img[1013] = NEW_IMAGE_REFERANCE_BYTES[1013] ^ nonce_bytes[3]
            final_init_img[1017] = NEW_IMAGE_REFERANCE_BYTES[1017] ^ nonce_bytes[3]
            final_init_img[1021] = NEW_IMAGE_REFERANCE_BYTES[1021] ^ nonce_bytes[3]
            final_init_img[1025] = NEW_IMAGE_REFERANCE_BYTES[1025] ^ nonce_bytes[3]
            final_init_img[1029] = NEW_IMAGE_REFERANCE_BYTES[1029] ^ nonce_bytes[3]
            final_init_img[1033] = NEW_IMAGE_REFERANCE_BYTES[1033] ^ nonce_bytes[3]
            final_init_img[1037] = NEW_IMAGE_REFERANCE_BYTES[1037] ^ nonce_bytes[3]
            final_init_img[1041] = NEW_IMAGE_REFERANCE_BYTES[1041] ^ nonce_bytes[3]
            final_init_img[1045] = NEW_IMAGE_REFERANCE_BYTES[1045] ^ nonce_bytes[3]
            final_init_img[1049] = NEW_IMAGE_REFERANCE_BYTES[1049] ^ nonce_bytes[3]
            final_init_img[1053] = NEW_IMAGE_REFERANCE_BYTES[1053] ^ nonce_bytes[3]
            final_init_img[1057] = NEW_IMAGE_REFERANCE_BYTES[1057] ^ nonce_bytes[3]
            final_init_img[1061] = NEW_IMAGE_REFERANCE_BYTES[1061] ^ nonce_bytes[3]
            final_init_img[1065] = NEW_IMAGE_REFERANCE_BYTES[1065] ^ nonce_bytes[3]
            final_init_img[1069] = NEW_IMAGE_REFERANCE_BYTES[1069] ^ nonce_bytes[3]
            final_init_img[1073] = NEW_IMAGE_REFERANCE_BYTES[1073] ^ nonce_bytes[3]
            final_init_img[1077] = NEW_IMAGE_REFERANCE_BYTES[1077] ^ nonce_bytes[3]
            final_init_img[1081] = NEW_IMAGE_REFERANCE_BYTES[1081] ^ nonce_bytes[3]
            final_init_img[1085] = NEW_IMAGE_REFERANCE_BYTES[1085] ^ nonce_bytes[3]
            final_init_img[1089] = NEW_IMAGE_REFERANCE_BYTES[1089] ^ nonce_bytes[3]
            final_init_img[1093] = NEW_IMAGE_REFERANCE_BYTES[1093] ^ nonce_bytes[3]
            final_init_img[1097] = NEW_IMAGE_REFERANCE_BYTES[1097] ^ nonce_bytes[3]
            final_init_img[1101] = NEW_IMAGE_REFERANCE_BYTES[1101] ^ nonce_bytes[3]
            final_init_img[1105] = NEW_IMAGE_REFERANCE_BYTES[1105] ^ nonce_bytes[3]
            final_init_img[1109] = NEW_IMAGE_REFERANCE_BYTES[1109] ^ nonce_bytes[3]
            final_init_img[1113] = NEW_IMAGE_REFERANCE_BYTES[1113] ^ nonce_bytes[3]
            final_init_img[1117] = NEW_IMAGE_REFERANCE_BYTES[1117] ^ nonce_bytes[3]
            final_init_img[1121] = NEW_IMAGE_REFERANCE_BYTES[1121] ^ nonce_bytes[3]
            final_init_img[1125] = NEW_IMAGE_REFERANCE_BYTES[1125] ^ nonce_bytes[3]
            final_init_img[1129] = NEW_IMAGE_REFERANCE_BYTES[1129] ^ nonce_bytes[3]
            final_init_img[1133] = NEW_IMAGE_REFERANCE_BYTES[1133] ^ nonce_bytes[3]
            final_init_img[1137] = NEW_IMAGE_REFERANCE_BYTES[1137] ^ nonce_bytes[3]
            final_init_img[1141] = NEW_IMAGE_REFERANCE_BYTES[1141] ^ nonce_bytes[3]
            final_init_img[1145] = NEW_IMAGE_REFERANCE_BYTES[1145] ^ nonce_bytes[3]
            final_init_img[1149] = NEW_IMAGE_REFERANCE_BYTES[1149] ^ nonce_bytes[3]
            final_init_img[1153] = NEW_IMAGE_REFERANCE_BYTES[1153] ^ nonce_bytes[3]
            final_init_img[1157] = NEW_IMAGE_REFERANCE_BYTES[1157] ^ nonce_bytes[3]
            final_init_img[1161] = NEW_IMAGE_REFERANCE_BYTES[1161] ^ nonce_bytes[3]
            final_init_img[1165] = NEW_IMAGE_REFERANCE_BYTES[1165] ^ nonce_bytes[3]
            final_init_img[1169] = NEW_IMAGE_REFERANCE_BYTES[1169] ^ nonce_bytes[3]
            final_init_img[1173] = NEW_IMAGE_REFERANCE_BYTES[1173] ^ nonce_bytes[3]
            final_init_img[1177] = NEW_IMAGE_REFERANCE_BYTES[1177] ^ nonce_bytes[3]
            final_init_img[1181] = NEW_IMAGE_REFERANCE_BYTES[1181] ^ nonce_bytes[3]
            final_init_img[1185] = NEW_IMAGE_REFERANCE_BYTES[1185] ^ nonce_bytes[3]
            final_init_img[1189] = NEW_IMAGE_REFERANCE_BYTES[1189] ^ nonce_bytes[3]
            final_init_img[1193] = NEW_IMAGE_REFERANCE_BYTES[1193] ^ nonce_bytes[3]
            final_init_img[1197] = NEW_IMAGE_REFERANCE_BYTES[1197] ^ nonce_bytes[3]
            final_init_img[1201] = NEW_IMAGE_REFERANCE_BYTES[1201] ^ nonce_bytes[3]
            final_init_img[1205] = NEW_IMAGE_REFERANCE_BYTES[1205] ^ nonce_bytes[3]
            final_init_img[1209] = NEW_IMAGE_REFERANCE_BYTES[1209] ^ nonce_bytes[3]
            final_init_img[1213] = NEW_IMAGE_REFERANCE_BYTES[1213] ^ nonce_bytes[3]
            final_init_img[1217] = NEW_IMAGE_REFERANCE_BYTES[1217] ^ nonce_bytes[3]
            final_init_img[1221] = NEW_IMAGE_REFERANCE_BYTES[1221] ^ nonce_bytes[3]
            final_init_img[1225] = NEW_IMAGE_REFERANCE_BYTES[1225] ^ nonce_bytes[3]
            final_init_img[1229] = NEW_IMAGE_REFERANCE_BYTES[1229] ^ nonce_bytes[3]
            final_init_img[1233] = NEW_IMAGE_REFERANCE_BYTES[1233] ^ nonce_bytes[3]
            final_init_img[1237] = NEW_IMAGE_REFERANCE_BYTES[1237] ^ nonce_bytes[3]
            final_init_img[1241] = NEW_IMAGE_REFERANCE_BYTES[1241] ^ nonce_bytes[3]
            final_init_img[1245] = NEW_IMAGE_REFERANCE_BYTES[1245] ^ nonce_bytes[3]
            final_init_img[1249] = NEW_IMAGE_REFERANCE_BYTES[1249] ^ nonce_bytes[3]
            final_init_img[1253] = NEW_IMAGE_REFERANCE_BYTES[1253] ^ nonce_bytes[3]
            final_init_img[1257] = NEW_IMAGE_REFERANCE_BYTES[1257] ^ nonce_bytes[3]
            final_init_img[1261] = NEW_IMAGE_REFERANCE_BYTES[1261] ^ nonce_bytes[3]
            final_init_img[1265] = NEW_IMAGE_REFERANCE_BYTES[1265] ^ nonce_bytes[3]
            final_init_img[1269] = NEW_IMAGE_REFERANCE_BYTES[1269] ^ nonce_bytes[3]
            final_init_img[1273] = NEW_IMAGE_REFERANCE_BYTES[1273] ^ nonce_bytes[3]
            final_init_img[1277] = NEW_IMAGE_REFERANCE_BYTES[1277] ^ nonce_bytes[3]
            final_init_img[1281] = NEW_IMAGE_REFERANCE_BYTES[1281] ^ nonce_bytes[3]
            final_init_img[1285] = NEW_IMAGE_REFERANCE_BYTES[1285] ^ nonce_bytes[3]
            final_init_img[1289] = NEW_IMAGE_REFERANCE_BYTES[1289] ^ nonce_bytes[3]
            final_init_img[1293] = NEW_IMAGE_REFERANCE_BYTES[1293] ^ nonce_bytes[3]
            final_init_img[1297] = NEW_IMAGE_REFERANCE_BYTES[1297] ^ nonce_bytes[3]
            final_init_img[1301] = NEW_IMAGE_REFERANCE_BYTES[1301] ^ nonce_bytes[3]
            final_init_img[1305] = NEW_IMAGE_REFERANCE_BYTES[1305] ^ nonce_bytes[3]
            final_init_img[1309] = NEW_IMAGE_REFERANCE_BYTES[1309] ^ nonce_bytes[3]
            final_init_img[1313] = NEW_IMAGE_REFERANCE_BYTES[1313] ^ nonce_bytes[3]
            final_init_img[1317] = NEW_IMAGE_REFERANCE_BYTES[1317] ^ nonce_bytes[3]
            final_init_img[1321] = NEW_IMAGE_REFERANCE_BYTES[1321] ^ nonce_bytes[3]
            final_init_img[1325] = NEW_IMAGE_REFERANCE_BYTES[1325] ^ nonce_bytes[3]
            final_init_img[1329] = NEW_IMAGE_REFERANCE_BYTES[1329] ^ nonce_bytes[3]
            final_init_img[1333] = NEW_IMAGE_REFERANCE_BYTES[1333] ^ nonce_bytes[3]
            final_init_img[1337] = NEW_IMAGE_REFERANCE_BYTES[1337] ^ nonce_bytes[3]
            final_init_img[1341] = NEW_IMAGE_REFERANCE_BYTES[1341] ^ nonce_bytes[3]
            final_init_img[1345] = NEW_IMAGE_REFERANCE_BYTES[1345] ^ nonce_bytes[3]
            final_init_img[1349] = NEW_IMAGE_REFERANCE_BYTES[1349] ^ nonce_bytes[3]
            final_init_img[1353] = NEW_IMAGE_REFERANCE_BYTES[1353] ^ nonce_bytes[3]
            final_init_img[1357] = NEW_IMAGE_REFERANCE_BYTES[1357] ^ nonce_bytes[3]
            final_init_img[1361] = NEW_IMAGE_REFERANCE_BYTES[1361] ^ nonce_bytes[3]
            final_init_img[1365] = NEW_IMAGE_REFERANCE_BYTES[1365] ^ nonce_bytes[3]
            final_init_img[1369] = NEW_IMAGE_REFERANCE_BYTES[1369] ^ nonce_bytes[3]
            final_init_img[1373] = NEW_IMAGE_REFERANCE_BYTES[1373] ^ nonce_bytes[3]
            final_init_img[1377] = NEW_IMAGE_REFERANCE_BYTES[1377] ^ nonce_bytes[3]
            final_init_img[1381] = NEW_IMAGE_REFERANCE_BYTES[1381] ^ nonce_bytes[3]
            final_init_img[1385] = NEW_IMAGE_REFERANCE_BYTES[1385] ^ nonce_bytes[3]
            final_init_img[1389] = NEW_IMAGE_REFERANCE_BYTES[1389] ^ nonce_bytes[3]
            final_init_img[1393] = NEW_IMAGE_REFERANCE_BYTES[1393] ^ nonce_bytes[3]
            final_init_img[1397] = NEW_IMAGE_REFERANCE_BYTES[1397] ^ nonce_bytes[3]
            final_init_img[1401] = NEW_IMAGE_REFERANCE_BYTES[1401] ^ nonce_bytes[3]
            final_init_img[1405] = NEW_IMAGE_REFERANCE_BYTES[1405] ^ nonce_bytes[3]
            final_init_img[1409] = NEW_IMAGE_REFERANCE_BYTES[1409] ^ nonce_bytes[3]
            final_init_img[1413] = NEW_IMAGE_REFERANCE_BYTES[1413] ^ nonce_bytes[3]
            final_init_img[1417] = NEW_IMAGE_REFERANCE_BYTES[1417] ^ nonce_bytes[3]
            final_init_img[1421] = NEW_IMAGE_REFERANCE_BYTES[1421] ^ nonce_bytes[3]
            final_init_img[1425] = NEW_IMAGE_REFERANCE_BYTES[1425] ^ nonce_bytes[3]
            final_init_img[1429] = NEW_IMAGE_REFERANCE_BYTES[1429] ^ nonce_bytes[3]
            final_init_img[1433] = NEW_IMAGE_REFERANCE_BYTES[1433] ^ nonce_bytes[3]
            final_init_img[1437] = NEW_IMAGE_REFERANCE_BYTES[1437] ^ nonce_bytes[3]
            final_init_img[1441] = NEW_IMAGE_REFERANCE_BYTES[1441] ^ nonce_bytes[3]
            final_init_img[1445] = NEW_IMAGE_REFERANCE_BYTES[1445] ^ nonce_bytes[3]
            final_init_img[1449] = NEW_IMAGE_REFERANCE_BYTES[1449] ^ nonce_bytes[3]
            final_init_img[1453] = NEW_IMAGE_REFERANCE_BYTES[1453] ^ nonce_bytes[3]
            final_init_img[1457] = NEW_IMAGE_REFERANCE_BYTES[1457] ^ nonce_bytes[3]
            final_init_img[1461] = NEW_IMAGE_REFERANCE_BYTES[1461] ^ nonce_bytes[3]
            final_init_img[1465] = NEW_IMAGE_REFERANCE_BYTES[1465] ^ nonce_bytes[3]
            final_init_img[1469] = NEW_IMAGE_REFERANCE_BYTES[1469] ^ nonce_bytes[3]
            final_init_img[1473] = NEW_IMAGE_REFERANCE_BYTES[1473] ^ nonce_bytes[3]
            final_init_img[1477] = NEW_IMAGE_REFERANCE_BYTES[1477] ^ nonce_bytes[3]
            final_init_img[1481] = NEW_IMAGE_REFERANCE_BYTES[1481] ^ nonce_bytes[3]
            final_init_img[1485] = NEW_IMAGE_REFERANCE_BYTES[1485] ^ nonce_bytes[3]
            final_init_img[1489] = NEW_IMAGE_REFERANCE_BYTES[1489] ^ nonce_bytes[3]
            final_init_img[1493] = NEW_IMAGE_REFERANCE_BYTES[1493] ^ nonce_bytes[3]
            final_init_img[1497] = NEW_IMAGE_REFERANCE_BYTES[1497] ^ nonce_bytes[3]
            final_init_img[1501] = NEW_IMAGE_REFERANCE_BYTES[1501] ^ nonce_bytes[3]
            final_init_img[1505] = NEW_IMAGE_REFERANCE_BYTES[1505] ^ nonce_bytes[3]
            final_init_img[1509] = NEW_IMAGE_REFERANCE_BYTES[1509] ^ nonce_bytes[3]
            final_init_img[1513] = NEW_IMAGE_REFERANCE_BYTES[1513] ^ nonce_bytes[3]
            final_init_img[1517] = NEW_IMAGE_REFERANCE_BYTES[1517] ^ nonce_bytes[3]
            final_init_img[1521] = NEW_IMAGE_REFERANCE_BYTES[1521] ^ nonce_bytes[3]
            final_init_img[1525] = NEW_IMAGE_REFERANCE_BYTES[1525] ^ nonce_bytes[3]
            final_init_img[1529] = NEW_IMAGE_REFERANCE_BYTES[1529] ^ nonce_bytes[3]
            final_init_img[1533] = NEW_IMAGE_REFERANCE_BYTES[1533] ^ nonce_bytes[3]
            final_init_img[1537] = NEW_IMAGE_REFERANCE_BYTES[1537] ^ nonce_bytes[3]
            final_init_img[1541] = NEW_IMAGE_REFERANCE_BYTES[1541] ^ nonce_bytes[3]
            final_init_img[1545] = NEW_IMAGE_REFERANCE_BYTES[1545] ^ nonce_bytes[3]
            final_init_img[1549] = NEW_IMAGE_REFERANCE_BYTES[1549] ^ nonce_bytes[3]
            final_init_img[1553] = NEW_IMAGE_REFERANCE_BYTES[1553] ^ nonce_bytes[3]
            final_init_img[1557] = NEW_IMAGE_REFERANCE_BYTES[1557] ^ nonce_bytes[3]
            final_init_img[1561] = NEW_IMAGE_REFERANCE_BYTES[1561] ^ nonce_bytes[3]
            final_init_img[1565] = NEW_IMAGE_REFERANCE_BYTES[1565] ^ nonce_bytes[3]
            final_init_img[1569] = NEW_IMAGE_REFERANCE_BYTES[1569] ^ nonce_bytes[3]
            final_init_img[1573] = NEW_IMAGE_REFERANCE_BYTES[1573] ^ nonce_bytes[3]
            final_init_img[1577] = NEW_IMAGE_REFERANCE_BYTES[1577] ^ nonce_bytes[3]
            final_init_img[1581] = NEW_IMAGE_REFERANCE_BYTES[1581] ^ nonce_bytes[3]
            final_init_img[1585] = NEW_IMAGE_REFERANCE_BYTES[1585] ^ nonce_bytes[3]
            final_init_img[1589] = NEW_IMAGE_REFERANCE_BYTES[1589] ^ nonce_bytes[3]
            final_init_img[1593] = NEW_IMAGE_REFERANCE_BYTES[1593] ^ nonce_bytes[3]
            final_init_img[1597] = NEW_IMAGE_REFERANCE_BYTES[1597] ^ nonce_bytes[3]
            final_init_img[1601] = NEW_IMAGE_REFERANCE_BYTES[1601] ^ nonce_bytes[3]
            final_init_img[1605] = NEW_IMAGE_REFERANCE_BYTES[1605] ^ nonce_bytes[3]
            final_init_img[1609] = NEW_IMAGE_REFERANCE_BYTES[1609] ^ nonce_bytes[3]
            final_init_img[1613] = NEW_IMAGE_REFERANCE_BYTES[1613] ^ nonce_bytes[3]
            final_init_img[1617] = NEW_IMAGE_REFERANCE_BYTES[1617] ^ nonce_bytes[3]
            final_init_img[1621] = NEW_IMAGE_REFERANCE_BYTES[1621] ^ nonce_bytes[3]
            final_init_img[1625] = NEW_IMAGE_REFERANCE_BYTES[1625] ^ nonce_bytes[3]
            final_init_img[1629] = NEW_IMAGE_REFERANCE_BYTES[1629] ^ nonce_bytes[3]
            final_init_img[1633] = NEW_IMAGE_REFERANCE_BYTES[1633] ^ nonce_bytes[3]
            final_init_img[1637] = NEW_IMAGE_REFERANCE_BYTES[1637] ^ nonce_bytes[3]
            final_init_img[1641] = NEW_IMAGE_REFERANCE_BYTES[1641] ^ nonce_bytes[3]
            final_init_img[1645] = NEW_IMAGE_REFERANCE_BYTES[1645] ^ nonce_bytes[3]
            final_init_img[1649] = NEW_IMAGE_REFERANCE_BYTES[1649] ^ nonce_bytes[3]
            final_init_img[1653] = NEW_IMAGE_REFERANCE_BYTES[1653] ^ nonce_bytes[3]
            final_init_img[1657] = NEW_IMAGE_REFERANCE_BYTES[1657] ^ nonce_bytes[3]
            final_init_img[1661] = NEW_IMAGE_REFERANCE_BYTES[1661] ^ nonce_bytes[3]
            final_init_img[1665] = NEW_IMAGE_REFERANCE_BYTES[1665] ^ nonce_bytes[3]
            final_init_img[1669] = NEW_IMAGE_REFERANCE_BYTES[1669] ^ nonce_bytes[3]
            final_init_img[1673] = NEW_IMAGE_REFERANCE_BYTES[1673] ^ nonce_bytes[3]
            final_init_img[1677] = NEW_IMAGE_REFERANCE_BYTES[1677] ^ nonce_bytes[3]
            final_init_img[1681] = NEW_IMAGE_REFERANCE_BYTES[1681] ^ nonce_bytes[3]
            final_init_img[1685] = NEW_IMAGE_REFERANCE_BYTES[1685] ^ nonce_bytes[3]
            final_init_img[1689] = NEW_IMAGE_REFERANCE_BYTES[1689] ^ nonce_bytes[3]
            final_init_img[1693] = NEW_IMAGE_REFERANCE_BYTES[1693] ^ nonce_bytes[3]
            final_init_img[1697] = NEW_IMAGE_REFERANCE_BYTES[1697] ^ nonce_bytes[3]
            final_init_img[1701] = NEW_IMAGE_REFERANCE_BYTES[1701] ^ nonce_bytes[3]
            final_init_img[1705] = NEW_IMAGE_REFERANCE_BYTES[1705] ^ nonce_bytes[3]
            final_init_img[1709] = NEW_IMAGE_REFERANCE_BYTES[1709] ^ nonce_bytes[3]
            final_init_img[1713] = NEW_IMAGE_REFERANCE_BYTES[1713] ^ nonce_bytes[3]
            final_init_img[1717] = NEW_IMAGE_REFERANCE_BYTES[1717] ^ nonce_bytes[3]
            final_init_img[1721] = NEW_IMAGE_REFERANCE_BYTES[1721] ^ nonce_bytes[3]
            final_init_img[1725] = NEW_IMAGE_REFERANCE_BYTES[1725] ^ nonce_bytes[3]
            final_init_img[1729] = NEW_IMAGE_REFERANCE_BYTES[1729] ^ nonce_bytes[3]
            final_init_img[1733] = NEW_IMAGE_REFERANCE_BYTES[1733] ^ nonce_bytes[3]
            final_init_img[1737] = NEW_IMAGE_REFERANCE_BYTES[1737] ^ nonce_bytes[3]
            final_init_img[1741] = NEW_IMAGE_REFERANCE_BYTES[1741] ^ nonce_bytes[3]
            final_init_img[1745] = NEW_IMAGE_REFERANCE_BYTES[1745] ^ nonce_bytes[3]
            final_init_img[1749] = NEW_IMAGE_REFERANCE_BYTES[1749] ^ nonce_bytes[3]
            final_init_img[1753] = NEW_IMAGE_REFERANCE_BYTES[1753] ^ nonce_bytes[3]
            final_init_img[1757] = NEW_IMAGE_REFERANCE_BYTES[1757] ^ nonce_bytes[3]
            final_init_img[1761] = NEW_IMAGE_REFERANCE_BYTES[1761] ^ nonce_bytes[3]
            final_init_img[1765] = NEW_IMAGE_REFERANCE_BYTES[1765] ^ nonce_bytes[3]
            final_init_img[1769] = NEW_IMAGE_REFERANCE_BYTES[1769] ^ nonce_bytes[3]
            final_init_img[1773] = NEW_IMAGE_REFERANCE_BYTES[1773] ^ nonce_bytes[3]
            final_init_img[1777] = NEW_IMAGE_REFERANCE_BYTES[1777] ^ nonce_bytes[3]
            final_init_img[1781] = NEW_IMAGE_REFERANCE_BYTES[1781] ^ nonce_bytes[3]
       


            


        # Recompute the block hash
        block_hash = new_hash_block() 

        """
        test_hash = new_hash_block_for_testing(block_header)
        if block_hash == test_hash:
            pass
        else:
            print("wtf?")
        """
        subtarget = share_block_bits2target(block_template["bits"])
        if block_hash < target_hash: 
            submission = (block_header+new_block[80:]).hex()
            print("Found! Submitting: {}\n".format(submission))
            response = rpc_submitblock(submission, address, pool_address, stlx_address, mining_id)
            if response is not None:
                print("Submission: {}".format(response))
                break
        elif block_hash < subtarget:
            submission = (block_header+new_block[80:]).hex()
            print("Share sent to pool!\nSubmitting: {}\n".format(submission))
            response = rpc_submitblock(submission, address, pool_address, stlx_address, mining_id)
            if response is not None:
                print("Submission: {}".format(response))
                break
			
        if event.is_set():
            break
		
        if nonce % 1000 == 0 and nonce > nonce_start:
            current_timestamp = time.time()
            diff = current_timestamp - last_time_stamp
            if diff > 10:
                hash_rate = int((nonce - nonce_start) / diff)
                print("CPU{}: {} hash/s".format(cpu_index, hash_rate))
                nonce_start = nonce + 1
                last_time_stamp = current_timestamp
                
                
            
        nonce += 1

    event.set()

def standalone_miner(address, pool_address, stlx_address, mining_id):
    cpuCount = os.cpu_count()
    
    print("\nNumber of CPU cores in the system: {}".format(cpuCount)) 

    try:
        if len(sys.argv) > 3:
            process_count = int(sys.argv[3])
        else:     
            process_count = int(input("How many of these cores do you want to use?\n"))
    except:    
        process_count = 1
    if process_count > cpuCount:
        process_count = cpuCount
    if process_count < 1:
        process_count = 1
    
    print("\nSelected CPU cores: {}".format(process_count))
    
    address = rpc_registerminer(mining_id)
    print("Mining address received: "+address)
    print("")
    block_template = rpc_getblocktemplate()
    best_blockhash = block_template["previousblockhash"]
    
    re_init_arr = True
    proc_arr = []
    event = multiprocessing.Event()
    while True:
        try:
            if re_init_arr:
                re_init_arr = False
                print("Mining Block: {}".format(block_template["height"]))
                event.clear()
                for i in range(process_count): 
                    proc_arr.insert(i, multiprocessing.Process(target=new_block_mine, args=(block_template, address, pool_address, stlx_address, mining_id, i,cpuCount, event)))
                    proc_arr[i].start()
            time.sleep(0.35)
            best_blockhash = rpc_getbestblockhash()
            if block_template["previousblockhash"] != best_blockhash or event.is_set():
                event.set()
                for i in range(process_count):
                    proc_arr[i].join()
                try_count = 0
                while True:
                    if try_count > 0:
                        print("RETRY {}: Fetching block template...".format(try_count))
                        best_blockhash = rpc_getbestblockhash()
                    else:
                        print("Fetching block template...")
                    block_template = rpc_getblocktemplate()
                    if best_blockhash == block_template["previousblockhash"]:
                        break
                    else:
                        time.sleep(1)
                        try_count += 1
                re_init_arr = True
        except Exception as e:
            print("Exception in standalone_miner loop:")
            print(e) 
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type) 
            print(fname) 
            print(exc_tb.tb_lineno)
            time.sleep(1)

def randomword(length):
	letters = string.ascii_lowercase
	return ''.join(random.choice(letters) for i in range(length))
    
if __name__ == "__main__":

    screen_clear()
    print (
'''
 ██████╗  ██████╗██╗   ██╗ ██████╗ ██████╗ ██╗███╗   ██╗
██╔═══██╗██╔════╝██║   ██║██╔════╝██╔═══██╗██║████╗  ██║
██║   ██║██║     ██║   ██║██║     ██║   ██║██║██╔██╗ ██║
██║   ██║██║     ╚██╗ ██╔╝██║     ██║   ██║██║██║╚██╗██║
╚██████╔╝╚██████╗ ╚████╔╝ ╚██████╗╚██████╔╝██║██║ ╚████║
 ╚═════╝  ╚═════╝  ╚═══╝   ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝
                                                        \n
''')

    addr = ""
    mining_id = randomword(12);
    
    print("\nYou can try wallet.ocvcoin.com to create a wallet and get an address.\n\nIMPORTANT: IF YOU ARE RUNNING ANOTHER COPY OF THIS MINER SCRIPT ON THIS PC OR ANYWHERE, DEFINITELY DO NOT ENTER SAME ADDRESS!")
    if len(sys.argv) > 1:
        paddr = sys.argv[1]
    else:           
        paddr = input("\nEnter your ocvcoin address:\n(you can right click & paste it)\n ")

    if decode_segwit_address("ocv", paddr) == (None, None):
        print("You entered the wrong address. Your address must be of bech32 type.")
        print("(It should start with ocv1)")
        exit()
    if len(sys.argv) > 2:
        stlxaddr = sys.argv[2]
    else:           
        stlxaddr = input("\nEnter your stlx address:\n(you can right click & paste it)\n ")
    if len(stlxaddr) < 178:
        print("You entered the wrong address. Your address must be a STLX address type (STLX....)")
        exit()
    
    sample_data = bytearray(b'\xb7\xd6\x05\xce\xcd\x28\x2d\xf4\x98\xbd\xf5\x1b\x0b\xef\x27\x80\xea\xcd\x4d\x0f\x2e\x63\xf7\xfa\x44\x69\x72\x66\x44\x26\xf2\xd0\xd5\x94\x9e\x86\x38\x07\x38\x3f\xb7\x33\x07\xca\x54\x0b\x40\xd3\xde\xaf\x35\xae\x74\xb7\xd1\x4c\x3a\xe8\xe7\x8f\x44\x42\x7f\xb9\xda\x3f\x9f\xbb\x1b\x7e\x6d\x51\xec\x8d\x3e\x8b\x5d\xfd\xb3\x8c\x64\x95\x70\x53\x21\x45\x56\x17\x0d\xc8\x08\x3f\x88\xd0\x00\x52\x9b\x86\x6b\x5d\x31\x23\x46\x97\x9a\x34\xdc\x85\xd2\x2f\x5c\x1c\x3f\xa7\xb3\x25\x8d\x08\x74\xcf\x53\x22\x27\xfb\xec\x34\x34\x43\xe8\x41\x33\x0f\x4c\x4b\x46\x60\xa3\xe0\x54\x2e\xd4\xb8\xff\x90\x6f\x0a\x36\x7c\x59\xb7\x0f\xf1\x9b\xb7\x2a\x4a\xbd\xc2\x56\xa4\x8d\x32\x7c\x49\xf2\xa5\xe8\x2d\x2c\xfd\xbe\xba\x14\xc1\x8b\x6a\x5a\x4e\xae\xd3\xf9\xa8\xa5\x5a\xff\xd2\x8e\xb2\xa7\x5a\x07\x31\x69\x2a\x25\xf5\xf9\x8a\x3b\xc6\x95\x7a\xb0\x58\xa4\x21\xfc\xa8\xda\x7c\xd0\x72\x13\xca\xb2\x96\xc4\x99\x7f\x94\xb9\x2b\x6d\x22\x26\xb7\x20\x39\xb1\x0c\x73\x57\x8d\x42\x62\xe0\xbc\xcf\x58\x94\xe8\x88\xd9\x4c\x02\xfa\xdc\x56\xf0\xd9\xee\x2a\x85\xc2\xe9\x1e\x49\xe4\x1e\x52\xfd\x2d\xa8\x52\x0d\xa2\x85\x6d\x99\xb1\x79\xa0\xae\x3f\x67\x8e\xa6\x95\x8c\x32\x61\x7a\x4b\xd1\x7b\xec\x32\xab\xba\x16\x16\xc6\x8d\x11\x23\x5b\x38\x8c\x07\xa3\x93\x37\xfe\x91\x86\x78\xba\x43\x69\x42\x22\x6a\x6e\xe3\xde\x8e\xc6\x92\xaa\x3a\x6b\x5d\x66\x4e\x68\x11\x4b\x49\x84\xec\xb0\x7c\x31\xe0\xa9\x72\x6b\xf0\x4d\x1c\xef\x8d\xea\x9a\xe3\x90\x49\x21\xac\x19\xd4\x1c\x62\x8e\x56\xb0\x3b\xdc\x08\x16\xc5\xa8\xfc\x9c\xc4\x21\xbb\xef\xaa\x36\x5c\x48\xaf\x80\x91\x98\x04\xd6\x78\x4a\x83\x8d\x9c\xff\x5c\x9f\xed\xad\xc2\x46\x97\xe3\xc6\x19\xdd\x99\x14\x90\x8d\x9e\x1f\x70\xd1\xaa\x64\x9b\xd5\x2d\xc7\x3f\x92\xac\xaa\x53\x0b\x50\xfb\xdc\x66\x64\x55\x31\x62\xe4\x24\x8b\xe5\xdd\x03\xe3\xec\x64\x74\x77\xf2\x00\xd9\x0d\xd1\x47\xff\xcf\x17\xdd\xcf\xa6\xa6\x75\x7d\x8b\x1b\xc2\xd5\x05\x67\xd8\x81\xdd\xdd\xfc\xa2\x44\x19\xb1\x78\xc6\xf6\x70\x91\xe4\x0a\x28\x36\x62\x04\xdc\x03\x63\x61\x26\x63\x11\xf9\x77\x04\x0b\xe7\x50\x21\x8e\xc3\x83\xff\x8c\xde\x1e\xe4\xa3\x68\x68\x9d\x96\x06\x5a\x18\x73\x5d\x38\x05\xf7\x46\xcb\xc0\xeb\x20\x17\xe3\x0f\xd1\xfb\xe5\x36\x7e\xdd\x7e\xa8\xc5\x88\x4e\x4a\x62\x4b\xe0\x13\x0d\x2d\x89\x69\x6d\x97\xe6\xd5\x0f\x6f\xc4\x19\xd4\x4f\xe5\x9a\x6a\xcc\xd3\x7d\x49\x89\x49\x13\xa5\x3b\x48\xbb\x7f\xd2\xcd\x85\x95\xbf\x42\xf8\x33\x5b\xdb\x6f\x1d\x75\x92\x5b\xd3\xf7\xa7\xb3\xbf\x68\xf0\x1a\xc5\xc0\xcf\x3d\x78\x87\x5e\xf5\x7f\x06\xb4\xb7\x3d\x88\xad\xe1\xb8\xf5\x59\x21\xaf\x4b\xba\x52\xed\x58\x41\x3d\xc3\x25\x3c\x67\x85\xe1\xa8\xf0\xdb\x5b\x33\xd8\x0b\x93\x44\xde\xd3\xb6\xaa\x5a\x71\xa9\xd8\x33\xeb\x40\xd4\x67\x3d\xf5\x99\x43\x16\x3f\x68\xf9\x5d\x82\xbc\xeb\x6d\x9b\x25\x6d\x80\xbf\x5c\xfa\x2f\xad\xe3\xae\x7d\xfb\xba\x99\x6f\xeb\x79\x56\xf5\xe7\xdd\x65\x74\x17\xb0\x7b\xd1\xd4\x86\x2f\x95\x07\xb5\x0a\xad\x41\x31\xc3\x6e\x2b\x22\x20\x84\xc9\x2d\x7c\x59\xee\xff\x48\x23\x8a\xf6\xfe\x18\x1d\xb3\x08\xf4\xdf\x88\xc6\xbb\xfb\xe2\x41\x93\xc7\x0a\x91\x15\x3a\x4e\x6b\x56\x02\x4c\xfc\x23\x2d\x21\x75\x95\x46\x5d\xb6\x4e\x0e\xf5\x0d\xdf\xfb\xd3\x7d\x8b\x56\x90\xfc\x3f\xef\x8a\x37\x0a\x21\x4e\xa4\xd3\x0d\xdf\x56\x3d\x4f\x0d\x87\xc7\x25\x42\xf7\x38\x1c\xba\xde\xe0\xfc\x16\x3c\xc6\xe4\x37\x3a\x41\xbd\x14\x5c\x94\x9c\xa7\xa0\xff\x36\x7b\x2f\x0a\x73\x60\x2d\x9e\xe2\x53\x9d\x7e\xb5\xd6\x27\xe9\xfc\xbf\x15\xa9\x96\xe0\x0e\x0e\xbb\xbf\x44\xde\xb7\x3c\xd7\x81\x15\xe8\x98\x58\x52\x28\xac\xfd\x80\x01\x33\x7a\x95\x42\xd3\xa0\xe0\xd4\xf3\xe9\xff\xb1\x78\x8f\x7a\xf5\x20\x20\x17\x0d\x21\xb7\xb4\x9b\xd8\x4a\x31\xec\x7a\xfb\x75\xb1\x69\xe3\x64\x62\x7c\x9b\xf3\x4c\xda\x1c\xf2\xa5\x20\xbe\x83\x91\x9a\x53\x5c\xa8\x85\x4c\x7c\x8a\x04\x9d\xa5\x62\x42\x9f\xfc\xae\x81\xcf\xe9\x0b\xdf\x61\x81\x6f\x7c\x11\x97\x9d\x30\x22\xca\x8a\x49\xb8\xfe\x02\xea\xb7\x37\xde\x21\xf4\x43\x7a\xf1\x71\x5f\xf1\xf7\x23\x86\x0f\x49\xeb\xe0\xc4\x09\xcf\x18\x51\x77\xd1\x1a\xf6\xcd\x93\xc3\xe4\x83\x91\x74\x61\x3d\x9f\xa0\xb4\x6a\x84\x92\xe1\x96\x67\x14\xe2\x56\xd8\x19\x11\x1d\x50\x50\x6c\x01\x4b\x25\x7c\x2f\xa8\xfb\x61\x9f\xc6\xb4\xde\xb2\x62\x79\x11\x33\x1b\xfa\x23\xd4\x99\xbf\x5c\x22\xbd\x94\xee\x9b\x75\x4f\xd6\x23\xa9\x0a\xdf\x01\x84\x12\xf2\xea\x30\x5f\xb1\xdd\x79\x91')
    

    
    hash_arr = [bytearray(b'\x8dA\x10xp\xe8\x06b\x90*\xcb\x83I\xab\x88ri\xc0$\xcb\x02]\x9f\x80\x8f\x93\r\xa9F\xa4\x88\xc6'), bytearray(b'\x9dp\x9ev\xe3\xc8I\x07\xa8\x90\xfe\x9e\xdc\xb77q\x10)\xd0[\x98M9H\xc8.\x0f\x8e\xabFeH'), bytearray(b'-\xf2\\\xfc\x17\x14\xbe\xed\x01\xcd\xc0\x99{\xa0j8\x8b\xe9\xa0\x9a\xde\xe3\xcd\xbc\x08\xf8\x04\xf6\x0e\x03\x9e\x90'), bytearray(b'\x86g\x0e\x93\x16\xf5\xc9\x08\xb1\x9f\x1a\xa0io\x8e\x13\xc6\xc1\xa7\x97[\xd7c(k!*\x05\xb2m\xa7}'), bytearray(b'\xa6\xa7gJ\xb6\x07\xa1y\xb7\xa2\x13\x084\xa7\xbbu\xc4K\x1cF\xb0\x898\xf1\xb7\xc9\xf0P\x10\xa2A.'), bytearray(b'-*\xed\xaaMb\xef=+!<\x05&\xb7\xecZ\xa6a\xd2\xf5\x84`B\xeb\xb4K\x8dL\xaf\xed\xff9'), bytearray(b'\xee(x\xcc,l\xcf\xd4\xd25\xe6\x9bnP\xa8\xc9)\xad\xc2\xe5F\xd7t\x89\xa0Q\x1a\xdaoG\x14\x0e'), bytearray(b'\x18rA\xfb\xf7a\x9fT\xaa\xb8*\xb5(\xeb\xf4]\xf1\xf2\xcc\xe1H\xa3\x9d\xf1`\xbd\x0e\xbbGO\x16\x8a'), bytearray(b'H\x12\xc0\x1dO\xc3@\xfa\xc0\xf6l;"\x9b\xf2\x8a\xf20\xa7j\xff:0@\xd1\xb56\xd2\xca\xd3\x0f\x05'), bytearray(b'MDL\x19p\x93EW\xf2\x95^\xee\x90\xe5h\xeb\xc9\xd4R\x92<V\xbe\xff\xc0`\x1f\xec\x81A\xaau'), bytearray(b'F\xd4\xa8\xb4;S\xe8\xd5\x98q\xb6\xbeoZ\xa8\x13#\xab\x03\xe0\xd0\x01\xc3Z\xd8\xd9\xc6+>\x14\x96\xc1'), bytearray(b'\xa7&\x0f\xc8`Bc\x06h!=\xb9\x9e\xd0\x0e\x95\x1a\x89\xe92\xa8\xf6\x0c"f\xc6S\xd8[\x99\x9c\r'), bytearray(b'\xf3N\xc1\xf3\x9c.$4]%\xea\x9b\x99\xd2\xaf\x9c\xac\xbd\xe7\xfea\xa1\xa7\xf1\xab\xf5\xea\xbd\xdd]\x8c>'), bytearray(b"\xe0\'\x8ezZ\xa8\x845\xdc\xded\xaf\xa1\xe4\x8d\r\xcb\xa0\xc3\x83L\x1e-h\x84\rJ\x88\xd1_\xb1p"), bytearray(b'\xbf}Au*7\xf3\xac\x0e\x94\x829^\xec\x84<\xfb}\xb4/\x1b\xe0\xd1(<6\xcc\x85\xfd\xd0\xfd\xee'), bytearray(b'\x05L\xe0\xcb\x08DS\xc4\x10\x1c\xdb\x9a\xe32TCQ+\x0b/\xf3\xc8/\xb7`!\x97&\x8c\xe2wB'), bytearray(b'\xc9-\xc7\x06j\xd7\x14\xcc$\x07\xfe\xe9\x05\xf9\xe6\\X\xdc\x9dab\xd5\xb06\xf2[hx\xd1\x01\x90-'), bytearray(b'\x9c{\xfd\x8c\xd5`\x04\xd2\xf5\xcd\xea\xf5\xdc{\xd4g\xa5\xde45\x99\x05-\xaa\xe7{v\x1e:"\xe5\x9d'), bytearray(b"\x1b\xfb\xe6si\xc4\xbc\xe9\xba\xe6\x14NP\xf7N\x8b+a\xa6\x12\x95\'\xfa\xa5\x1aM$\xcd\xca\xf4Y\xa8"), bytearray(b"\x88vz?\xaa|g\x08\x16\xaeV\x1d4W\xbe\x92\xb4\'X\xb8\x121\x8aC\x15\x05\xdb\x9b\xcaQ\xc1|"), bytearray(b'=\xaa\xf4a\x182\xf3\x15g(\xda\xd9\xe7\x98\xd6\xa3i_\xa1\xf6_\xfc\xba\xae2\xf7\xa45\x0b(\x1d\xcb'), bytearray(b'\x1c\xce\x1a\xddR\xb6\xdb\xc3\xa7\x9d\xa2\xb7\x9f\x10@\x92u-PL\x0f?\x84\x8d0[\xf6\xf3$4o3'), bytearray(b'OA\xb0p\t\xf535\xa1u\x0c\xfaWz,\x82IxxX\xbe\xdf\xb9*\x02\x8f!\x8a\x0b\x08\xe8\xef'), bytearray(b'\xdd\x84\xd9L\xf2vg\xb9\x92\xdf\xb5\x01\x1fWR\x16\x11\xcc\xf2.o\xe3\xd5\x12G\xab{\xc2_\x87\x87\x18'), bytearray(b'\xd2\xa9d\xb1\x8a-\x89\xa6J\x06\xda\x87\xb0\xe2,\x8a7h\xb8x\xb0\x04\x04\xd2\x805fM\xa0\xd6\xa9\xfc'), bytearray(b"\x7f\x8e\'B\x8b\x16\xe79\x90\xbb@\x19{J\x8e\xfc!\x9d\x1f\x81\xb0\x97\xefgy\xdb\xc2&\xba9\xf7\xc1"), bytearray(b'\x16\xc5\xfd\xaa\xc9\xb5L7\xb50}<\x1e\xce\xc1\xe8\xc3j\x05\xe0\x8d\x97\xbf\xd9O\xa2\x83\xdfs\xdan\x06'), bytearray(b'\xa3\xd4\xa3\xa9\x18t)\xcf5\xde\xa9S\xa7^uJ\xcf\xac\xe1qo\xd4<r\xeb\xc7\xfe\x1cKDkJ'), bytearray(b'\xde\x9f\xf0\xa4\xc8m\xca|\x0e\x17"\xdb\x7f\x0b`\xf5\x0e\xf9A\x9ah\x7f\xd9\xd1\r\xae\xdf\xd5\xda_<\xef'), bytearray(b'\xad]h\xb3\x83\x98\x04\x8d\xa6\xb3_\x9e\xcb\xaaP\x8bOX\xcd\xb0\xbb\xd8)\xe6\xb8\xb7rl\xf0+\xe9\n'), bytearray(b'\x0f!\xf2#\xd8\xacc\xa9\xdeL\xda\x07\x10\x0c\x81\xe5\xdc\xb0e<4G\xdd6\x89T\x11\x91\xa1y\x106'), bytearray(b'\xda|\n+\x87\x8drFw\x9a\xf2\xd6CH^!\x96\xf1X\x81\xe3\x03\xfbN\xdeH\x1a?\xeb52\xa0'), bytearray(b'(\x9a\x80j\x1d\xc3\xb9\x97\xc0?\x96S!\xec9\xc1\xb7}\xc3j\xa0\x1bH\xcf\xe02e\x00\x81\x85S4'), bytearray(b'K\xb0\xe1\x8bO\x9f@&1\xbaL\xe8\xf6\xb8r\xbd\xad\xc2\x9d\x04\xe5\xc4\xc8K,\xa7e(\x11\x11pI'), bytearray(b'\xfbZ\xd5\xa0\xa0k7\x05\xffOGld\xd7Z\x9d}\x14D\xb5\xc2}\xd1\xf4\xf6G\x83\xae\xd0B\xe9"'), bytearray(b'\xcb\xaf2\xb1W\x11\xba\xae\xb9;\x96\x82\xdeq\xca#N\x9bZ\xc5\x9fb\xc3\xc3wG\xabl\xfa\xf3\xce\xae'), bytearray(b'z\xedP\xeb\xc78k\x9bu\xdd\x02F\x10\x92\xb0\xff\xee\xb8Ve\x13p2\x12\x8a\x98\x86\xc8\x9f\xfc\x0c\xd6'), bytearray(b'\xb6\xd9\x82\xc6\t]dK\xa9\xe3d\x8a\xb1(\x1d\xbbvd\x0b2\xac4F\xc3\xf4\xe7\xa4\xe5\x87,-\xf7'), bytearray(b'\x1b\xa9\x06\xca\xe8\xb2\x90\xd7\xd8\xdf\xac\x0f\x1c!z\xf2\xf6\xad\x1c\xbb\xc1\x82\x91\xf6L\x15\xb3\xa1\r\x0ci\xc1'), bytearray(b'\x05_\x12\x84\xcd\xa7\xbe\xad\xbdo\xb9\xff\x18OK\n\x92\xbdi\xba\xac\x18\xaew\xc3\xc1\xaeVJ\xff+C'), bytearray(b"\xbf$\xbb\xce`\xcf\x0b\x1ar\xa5\x0c\x0fj\x07\xc0&\x96Upka\'R<\xe1\xfaR\x00d\xde\xed\xc6"), bytearray(b'\x93\xa3\x17\xcd|\xc1\xd6Ph\xe1\xf7\x80%\x18\x87\xfb-|\x9fb\xaf\xaa\xbc\x81F=/v\xe3\xee&\xee'), bytearray(b'\xef\xd6HjL0,\xd5e\xcfz\xcd\xdf\x1a/#e\xf3\xdb\xe7Z7\x02\x9f\x9a\x1dL\xf4\xe3\xc4\xbdN'), bytearray(b'\xb3\x1dP\xbf\xe8\x1c7\xf8\x99\xaa\xa6\xcco\x1e\x0f\x0cf3NM{K\x08\xd4H\xe2;\x7f\xf20\xf2f'), bytearray(b'p\xc4\xc5\xb9t\xe9w\x93u\xfe\x81k\xb6\xa0\xe6g\xc0\xd6\x9b\xd2=5\xd2n\xf0M\xad\x15\x96\x07\xe1\xcd'), bytearray(b'\xb0z0D\x0b\x12\xd3\x93\x19\x12eV\xceF\xb0\xf5+\xde2\x14\x07\xd1\x82\x97X\xa4\xd1\x95\x8f\xa2U\xf0'), bytearray(b'ij\x1e\xd0*\xef=\xfe\xef\xce\n\xc4\x00\xba^\xf7:\xca\xd6\xa1\xb1\\\x8a\t\xb0\xd8\x9b\x05I\xc0\x1e\xf7'), bytearray(b'\xe8\xa6q\xc5\x8f\xcd\xb8,\x93\xb0\xb6\x81=t\xe82Cp\x9cP\x00\x1c\tW\x91\xbf\x8d\x8f\xd0c\x1d\xaf'), bytearray(b'K\xb2k\xf8\xfc\xe0\x12L\x87X\x1eM\xe2\xa1\x04P\xba\xcav\xb7\xd7/jg\xf5O.e\xf8\x9f\xfb\x82'), bytearray(b'8`\xd2\x9a\xe9F\xf4\\\x905\x16+\x89b\xd3\x92+\xc0\xec\x89\xee\xa3h\xb4\x8a\xca\xcc\xeb\xa3\xdc\xfc}'), bytearray(b'\x0c\xcf\xce_ \xdc2<\x91p\xeaxh\'h\xa8\x1f^\x8b\xa9\xef"`@\xab,q\xd5\xac\xe5\x90\xbc'), bytearray(b'p\xdb\xec\x1b?\xe5\xdb\xf5\x95\xe0=j\xf0\r\x8a\x16\x90#\x86\xa5{\x17\xa3\xc5\x0cnbs\xc0?\xbd\xa3'), bytearray(b'8X*a\x83\xa3\xafIa\xdbe\xb3\xd0\xd1\x80"\xf1f`\xa3\xed\xb4G\x9a\xd7\x8d\x9d2\x9c\xea)\xec'), bytearray(b'P\xd0i\x16\xa5\xe0\x8a\x0cd\x9c\x01v\xd3v\xb9$\xd7\x88\xe0\xd6%\x1d9\x9a\xd1\xb4/\x18\x86f\xd7\xc9'), bytearray(b'\x91yb\xeb+\xf6\x15?\xcb\x92\xbe\x806\x9e\xca\x0e\x0bt6\xa4\x88\x8ci\xa1\x13\x88hb\xa7\x99)\x8b'), bytearray(b'\xca\x10&\xc0\x80\x9d\xcf\xbb3r\xc8\xcb\xe8\xee\x0f\x88\xaej\xebkR\xde\xbd"p\xf9\xae~\xfbWQ\xe7'), bytearray(b'\x1a\x06\x1al\xc8\x02\xdb-C |WP\x1b"\xce%M9z\x89\x8eP\xcd\x18\xf1\xf0K,x\x94\xba'), bytearray(b'\x88\xae\xc2\xac\xa7N\x95\t\xe8%\xc8l\xc0\x8a\xacMu\xdb\x05\xf1\\\xd0e\x1aH\x89p\xa65/\xe1\x01'), bytearray(b'\xe3w\x9c\xe7\xa0\x15U@\xbd\x9d\xbfp\x1e\xa3\xedO@\n\x02<\x1e\xd8w\xf9\x95S\x18\xa5\xf0\x86i\xfd'), bytearray(b'\x05\x80o\xfc\xdce\x92sE\xd7 \x93g\xde\x17G\x13\xdb\xc0\x8c\xc5\xaf\xff\xccb|\x1f\xbc\r\x99\x97,'), bytearray(b'4\x0b\x94\xc9\xed\xc9\\\x9a\xa2\r\xcb\xc4W\x16\xb1\xc9(\xe4\x9fi\xc4\xca\x9c\x16\xca<Jm\xe2O\x9a\xbd'), bytearray(b"\x96\x948Z\x16\xf1\xf3^\xd3&\xdf`\x1f\x92DC\xd7\x9fy\xe9C{\xa9\'1?\xf3M\xdc\x15\xc9\r"), bytearray(b'\xc2\xc7]h\xdd\xa1\xe7a\x89\x88\x089\x94\x13\xa0\xd9\xc1\xdf\xe62Z\xcc\xa5\x14\x94\xd4\xbb\x08\x82|\xc5\xe3'), bytearray(b'\\\xd2^\x0e\x98\xd1c#\xe17I\x07\x96o\x13\x04\r`\xc8\xb9%\xf5\xa0\xe9\xc7\xf2X#97\xee\xeb'), bytearray(b'\xb7\xee\xe5\xe3\x80\xacR\xca\xe2q\xd5\xb2%\xda\xe0\x8f\x86\x14"\xff\xfc h\x08\xfb\xdd\xb4\x07)Vu\x9d'), bytearray(b'\xdd+u\x1e\x0e\xa6\xb3o\x8f,\xd2\xe8\x1f\xab?\xdc\xf2\x15\xa2\xe8\xb9\x12\xddF\x88J\xbf]\xa9^\xb8\xcb'), bytearray(b'\x9d\xef]\x83\xcd\xaepP\xa4\xb6%\xd2\x13L\x92E\xbb_\x90[\xfe\x93|\x8dG\x89\x8b\x8d/\xe1\x8a\xaf'), bytearray(b'\x0c\xe0\xa0\xb0&\xa2\x85\x95\xec\xcc\xa8\\\xb9\x01F\xb6\xb4\x06\xb1\x90\x1f\xb3K\xfaK\x15\xcb\x8cE\xb79\xef'), bytearray(b'\xec\xab\x1a\xbc\xb2\x90\xf4\xf4\xdf!o>\x1ez\x87SP\xcd\xb3\x95\xdf\xeeDo<\xa7\x19\xd6\x14\x10\xf7x'), bytearray(b'\x17\x87 \xb6\xfd\xda\xe2r!\xd26k\x8c\x0fh\xc4O\x98\x90x\x9f\x13\xba<#\x1b\xef`\xdf\xc3!@'), bytearray(b'\xcaW=\xfc\xb1d\xca\\\x04SVlt\xc2\x9b\xa83\x8d\xa4p\x82i\x03\xdae\xe5\xa1\xf7\x0eHL\xbc'), bytearray(b'%P\x1d_v\x14IUhY\x0cE\x97\x0f\xbe\xd7\tJB\xfd\xbc]*MT1V&c\x17\xef\xf2'), bytearray(b'\xc6\x86C[\xb3\xb4\xcd([\xae\xba\x83\xac1-j\x00kB\xa8W\x9a\x940:p>\xa2\xb3\x9a\x82\xc3'), bytearray(b'rL\xa7\x1f\x0b<[\x82\\\xa9\x04\xa1(\x98\r\x85h\xc2\x19\xf8zj\xf1V\xf8\xd9%\x04z\x887\xd8'), bytearray(b'\xfa\xd0Da\x0c\xc9\x14\x1dg\x98\xfc\xfa\x87\x14j\xc8\x84,)\x9fB\x1a\xfepl\x97\xec\xf4z\xb2\xfb\xad'), bytearray(b"\x0c\xa5D\x9bZ\x81\x08O`\x8e\xe3rrUAE\x8bf\xed-q\xa0:%F5t\xbc\\\x94d\'"), bytearray(b'Y\xa6\x1b\xc2\xaf\x7f\x9a!a\x1d@\xe8\xba\xa1\xf6\xb5\xe8\xf2P\x8a\x89\x1c\xab\x91\x94\xfb\xe1\xadh\x1b\x8d\x0f'), bytearray(b'\xdf6\x1d\t{\xf7]\xda\xb6\xbd\xcd/\x82o\x95{\xd6\xb4\x87\xc3"k\x83\xc6|\x0131\x8e4\x81\x03'), bytearray(b'\x0f&\xc3\x86\x97\x10\xf1\xaf\xab\xcbo\xb7\x98\xb3\xb2\x9e\xb3\xd9\xb3\xa4.\xa2\x01\xbf\xc0\x84\xabh\xa4\xf2_\x9a'), bytearray(b'\r\xe1\xb0\x12\xd5\x9d]Qv\xfc;\xa7V\x957w\xd7&*:N\xe2\xa6,\x90\xec\x03\x10\xce\x17n8'), bytearray(b'\xdd\x9b\x85)\xff\xe8L\xbf\xe5#\x03P\xf8l\x86\x8d,\xee\xec\xd6\x14i\x80\xf7\xd7.\xc1\x1a\xa1\xc4KD'), bytearray(b'\x11Qp\xe6\x8c\xbf\xec\x9b\xe0\x1c]N\xa2t\xfb\xfd\xb3D\xa2\xb4\t\xb4\x9d\xf6I]\xf8\x1eR(-\xaa'), bytearray(b'#\xe1\x9c\xd6%\xab\xfa\x9b\xc9\xd0\xc7\xb9JU\xc6\xc7!\x03\x82r\xe7Qj\xde}\xceb\xfe\xb7\xb8ho'), bytearray(b'\xac_\x06\x98\xc3#\xd3\xe5.B\x93\xd5\xf7\x9f\x99\xf7\xe9_\x01e82\x9c\xb6C\x9f\x96\xba^\xd7\xc1\x9b'), bytearray(b'O[\x9c\xe9\xaa\x86=\xc4\x12\x1az\xf2\x14\xac\xc2gP\xa5{\x88\x9a\xb8\x16\xeb\x0b"\x15\xdbc\xed\xa7T'), bytearray(b'\xebP.\xedY*_\xda\xe7\x92\x0e\xd9\xb1\x926\xd2K\x18\xddH\xa7\xc7"\x81\xc0CD\x858\xe3\xb3\xc9'), bytearray(b'\xb9"\xd9D\xb0P\xef\x80\xf3\xbe\xf8\xec\n\x91\x9c9\xd9\xcc)$\xca\xf9\xf1Op\x8d\x85zm\x9e\xe45'), bytearray(b'\x06\xd4\xe3*iR~\xd5\xf8A\xe428\x0e\xa4\xb9\xf4\xda\xcc\x8dN\xb0!m\x15B0\x04\x83\xca,\xe8'), bytearray(b"\xb5C\x00A\x8b\x0f\n}\x899B\'H\xbb\xc5\xd1Yh\x15\x7f\xee\x01\xcf\xc3n\xddf\x9dHF\xa3#"), bytearray(b'>6/YL8\xe4\xbf\r\xcbR\xbe\x1f\xf7OP\x02\xd7\x03\xd1<7\xa5\x036\xa3\x1d\x90\x9f\xdfL\xfb'), bytearray(b'AT\x14\x02h\x08\x1d\x8bD\xe6N`a\t\xf4Q\x8f\x8c\xc6\x90\x01\xb6\xbc*\xa3zU\x12\xa2\xda\x04\xe9'), bytearray(b'\xeaM\xec\x06\x8f\x07\x0c8{9\xef(h\xe4\x08\xe8\x1c\x95u`\xd7\\\x11*O\xfb\xfe4\x18\xb9\x7fc'), bytearray(b'\xb0\xf6\xca\xe0\xaf\xe3\xa9\x1fA\x14\xaa\xdf\xeb\xca\xe8\x96\x070\xe0BC\xe0[i\x88U\x81\xeb=k\xc4\x9f'), bytearray(b'\xa6:k\x85Y\xeeO\xef\xa9\xdc\xbc\xf2\xf3`#4\xf2n\xaf\xfc}\xd9a_\xa0[\xf7_\x9b\x15\r\xe8'), bytearray(b"\xf8\x10\x8c[\xc5H\x85\xd6\xdc\xa76\xb38\xd4\xc3\xaat\'\xb98\x13\xd2\'\x1am<\xe6\x18\xb0\x82\x01p"), bytearray(b'\\\xdb\x97\xfe\xf1pI\x8fW^\xd9,\xd0\xe68\x8c\xea\x7f{\xcd~l\xf7\xebR\x04\xa3Y\xcc\x9aK\xc4'), bytearray(b'h\x84\xed\x1c\x89\x96\x03\x988\xdd\x83\xa3\xf2\x08\x82\xb4o!t\xc8\x8d\rC\xbetnI\xb4\xd5\xe9\x12\x19'), bytearray(b"|#\x04\xc5\xcaJ8\x12~\x15\x89\x96\x95\xe8VR\xf2s\xfc\x9e\xd5\xf1\x90\x04\xfe\x1e\x18\'\xbd\xb0C\xfd"), bytearray(b"H\x8c^\x980\xf8\xac\xad\xadE\xab\'\x88gv\xc1\x7fh\\\xb4F{\x96\xc2Qm\rs\x84\x14\x9b<"), bytearray(b'K\xab\x9b\x90?\r5>\xc3\xd9I\x94`\tj\x1f\x0b~@b\x1b=*\x92\xea\xe0z\xcb\x95\xe4sp'), bytearray(b'\x84\xfe\xa65*\xe4\xe4\xbc\xcb\xe6Yq\x81(\xfc#xB"g\x97&8\xa5\xbf$\xdcL\xf7\x0e.\xbd'), bytearray(b'\xdd\x8d\x15(\xcf\nT\xf7\xb7\xaf\x001\xbf\xa4R>\xb5\xa2A:\x17\x11!\xafu\xf3\xed1\xafH\xf4\x9e'), bytearray(b"\x03\x8e\xfc ~\xc8\xfb84\t:T\xf2p\xcc\x94\x04\x84\x15\xf7\xdb)\xb7\xa6^B\x8f\xe4\x15\'\xb5\x1c"), bytearray(b'\x87\xee\xc6\x90\xc5\xd1>\xe7\x16&\x8fHv7\xb7\x13\xc1\x85\xba\xb8\xea3aa\xf1\xe5\\\xa7\xa2^\xbf\xc9'), bytearray(b"\x07\xb9#\xdf\xd9\xb6\x88\x0c\xcfu\x8fv\xe1p\xffA\'\xf9\\\xf1\x86dh\x8d\xec\xed\xf7p\x13\xf8[\x08"), bytearray(b'3\xde\xb6nP\xa1e<\x16\xec:\xc2\xe1\rG\xa5{U\xde\xb6)gP\xba\x0b~\xe4g\x1c\x92c\x15'), bytearray(b'\x90Z\xab\xc8\x19\xbf\xa6\xc8\x016\xb1\xd9\x9c\xa1(\xda.5X\x139\x12\x8bVE)\xd98}\xba\xe8\xd4'), bytearray(b'\xf2>Hm\x17@\xcf\x01/\xb4\xdd\xd3\x95Q\xd9\xbfL\x0fC\x16>\xc0/;\x1br\xad\xfe\xb4O\x1a\x19'), bytearray(b'\xd7\xf4\xfc\x9a\xa4\\\xbd\xa9\xc2\xa9\xc5\xd5\x9b\xc7\x11\xcbz\xb4\xba\x7f\x88\xda\xa1j%2_\x8eW\x19\xb9\xfa'), bytearray(b'\xa6M\xc9\xf9\x1a\xdap\xd5a7\xed\xc9\x1d\xdc\x10\xe26\xaa\xb3DgZ\xe7\xec\x0e\xaf\xdcH\xb0\x15F\x8a'), bytearray(b'\xa5\x8b\xe1H\xb1W\xaa\xeeJ\xb1\xbb\xd4<\xe2\x81\x8c\xa9\xbdI\xeb1\x15\xee1=I~\xe6s\xfdv\xe8'), bytearray(b'\x03\xc54\x8ff\xdb\xeb@\xb7\x89w\xc0\xc1\x92\x00\x1b/5\xc2\x96\xd7\xca`\x027y_}#GH\x19'), bytearray(b'\xef\x14\xb5\x17\xa9a$?\xba\xe0\xa9\xc4XT*I\xd0\xfe\x10\xdf\xeeFo0R\xf1\x14\xd7\x01\xc2\xee\xe5'), bytearray(b'%(v\xedt\x7f>;\xb8J\xf8p\xf3\x0bO\xbfYV.\x18\xc7q\xf4\xff\x88e\x86aS\xed\xb9\x99'), bytearray(b">\x97\xc2\xccS\xbfm(T!\x8c\xc4\x821\x9a;\'\xa8S\xc5\xf4W\xddH\xf6\xd3\x1a\xfb\xe0\xcb\x1b\xbb"), bytearray(b'c\x86\xe1\xa1\xb9\xcdf\xca\x8e\xc9\x83\x12\xc1\x05\x9f\x03&YF\x85\xe0\xda\xd2\x0b\x1c}\x85J0\xeb\x9f\x11'), bytearray(b'\xd8\x90\x03\xe1I-\xed\xbcH@ \xef\xca\x8c\xdb\xee\xbc!D\x933\x01\xf8Y\x178\xd9\xe9\xef\xfaC\xb1'), bytearray(b'\x80\x88\x15A\x89\x04\xbd"ui\xdd\xe3\x11\xccP$\xeb\x91\xd6\x89Rv<8\xc2N\x8e\xda\xd0\x89\xa1\xe3'), bytearray(b'\xf23\x0e\x1d\x8dZk\x94\x8a\x9f\x88\x04\xf0\x84\x16=\xad\xf1Rf\x10\xbf2\x07\xd6\x91L\xd7on-\xaa'), bytearray(b'kN\xefg\xb82\x95\xfa\xbc\xd1\xf9\xc7y\xef\xb3\xb3?%\x9d\xb0\x96XXu=\xa2\xd9H\x7f\x03\xfb\xd6'), bytearray(b'Ww\xb8\xf6\xb0\x11-\xd1-\xc8\xe1\x96"\x1d\x9c\x86\xc3\x9a\xb3h\xf8\xa5c\xef\x8e_\xe3\xaeHlcw'), bytearray(b'\x86\x08\x06\xd0\x84\xb3a\r\xb0v\x15\xa1\xfe\xf2u\x94\x95\xd3\xea\xc9\\\xf4\xcc\x94+\x976\x83ojg\t'), bytearray(b'\xed<\xb3\xdc\xe5\x8a1g\xa8qs\xb1b\xdf\xc5\xc8d\xbe7\x02~\x07\x1f@\xa5t\x88\x088\x06IH'), bytearray(b'\xe7\xe3\x1aq\xca&>Fg\xc9\xc9(\x95\xb5\xc8I\x8a\xda\xa8!:\\\xb0\xd2\x0cN\x9b\xb3\xbae\xb6I'), bytearray(b"\xf1uH\x17\xddu\x91\x9dQ\'!\x84\xd9\xcb\xe0w\xc4\xa1\x90\xe7F\xcb\xc1\xff\xebuC\x81\x8d9E\xea"), bytearray(b'\nqn\xb6\x9cf\xca\r0\xf1\x02U\xea\x04\x0e\xf41\t\xa3\xe5\xa7\xfa&\xa1\xcf\x16<\xdb\x9f\xa7\x8bi'), bytearray(b'\xe04\xb5\x9cF\x87\x92\x9b\x97R\xad\xc5n\x83\xc0*|]\x80\xe2\xa1|\xb2\x8e\xec)\xb5\xf1=\xa7\xa8\xb8'), bytearray(b'\xf3\x90\x1a\xc0?2\xdb1]7\x16\x04C\xc1\x7f_:[\x17\xbb\xf3\x9e\xa5u\xe1\xf0\x82\x02\xcf\xd5\xe4\x83'), bytearray(b'\xf4\x9f\xae\xb9\x1e\xa5\x17\x03O\xfa\xc4F\xfft\xe1d\x92\xa5\xc8\x1c\x05\x08\xa1(\xc9\x1a\x92t\x05\x9f\xe8k'), bytearray(b'T?\xb7\xfb\xa4\xf7\xcd\xc9\x8d\xe4w\x1c\xcdDD\x96!0\x12\xf5q\xadU\xcdT\x80j\xd5#\xcdB\x18'), bytearray(b'4H\xbe\xd1\x93APj\x04\xe2H\x84,\xc2\xf8c\xdd+\xc3\xef\xacN^\x1f\xf8<Z\xbfD\x91\x06 '), bytearray(b'\xe3\x18:m\xf6\xf2$\x0e\x9dv\x8a\xfby\x8f\x1fs\xf4\xe1\x19h\xadAba\xb26\xb9\xab\xb4\x11\x93\xbf'), bytearray(b'\\\n\x02\r\xa5\x92D\xed\xae\xea\x16\t\x13\xc2\x078\x1eU+\xa5`\xd9\x884\xa8\xec\xe3U\xe2Y\xc4\xe1'), bytearray(b'\xc72\xbe\xe3\xc2\xeb}\xa7p\xc6\xdc\xf6\xd1\xd1FH\xab\xb7\xa0\x8b\x82\xd7\x87\x0b\x02\x06\x13%{\x00v!'), bytearray(b'\x11^\xdc\xa2\t\xc2t\xfc\x8b\x87\xf6\xcd]\xb9p\xe4\x98Q\x84\xb3\xd5)o\xdc\xbd\xf1\xab\xf2\xc3\xc6\xa7U'), bytearray(b'\xbfIT\xa3\n3s\x97\x8d\x80b\xc2\x82\xe5\xb2\xf31\xdf\xcc\xcf\xb4\x90*+o\xc5sx\xf3\xc0\xa4<'), bytearray(b'\x908\x85\xfc\n\xe0t\x99-\xdcY\x16c\xbd\xb7\xc4\x9e\xe0\xe9\xfc*Y\xbdZ\xd0\x9aW\xd3\x05\x9c/x'), bytearray(b'\xfdT\xb8]Z\xbb\x8ej\xb6!\xa2\xb1\xe8\xfb\xfd\x81\x16\xa3\xd8(\xf01\x8b4P$X\xa4\xc3\x95\x1eK'), bytearray(b'\xe0\xf4\t\xfeW_\x0f\t\x05\xbbv\xce3\x0eJrh\xc8\xb6\x1a\xf9\xb7\xcc\xc9\xeeG\xe2\x800l\x90T'), bytearray(b'\x82\xdc\xf6#\x8d\x1eeQ\xf5=\xca(\xcc\x7f;\xa3\x94"f\xc2\x96\xba\xe6\x14\xa7\x05\x0fw\xaf\xde\xff\xc9'), bytearray(b'3\x89\xe5\xaa\xa7\xd9,\xb7\xf8\xe1+\x02\xfa\xbc\xe1\xc1\xd4\xadZ4f\x17\x9c\xfdfB\x07\x00)\xb0\xe4\xbf'), bytearray(b'\xc8\xfc\xa1\xec\x9ea\xf2\n\xd4\xab\x86\x1e\xf4\xa25\xefwg\xe2\x0b\xefJ\x86\x80k\xfb\x8f\xa7\xb7\xb7\xd5\x1f'), bytearray(b'\xc9\n\x9c\xebj\xb0g\x96{\xd0 $S\xfe\xadk1\xe8\x9a\x9dU5\xe6\xfec\x95qx\x9fs\xb5\xe8'), bytearray(b'\x8d\x8d\xd8\x1bP\x84\xebX@*\x1b5\xff_\x8eRR\x8c\n^\xcb\xd5\x9b0[\xdd\x08=\xd1\x80\xb3:'), bytearray(b'\xd9\x18IKZ>\xa9*\xa6H\x96\xf9\x9d\xf8\xb0\x04\xdf\x9f\xf1\x91\xdf\xf0\xe3D\x05:\xe4\xf4w-\xd2m'), bytearray(b'8\xa5\xe0\xc5\xd3\x88\x91\x86\xf6~%\xcb\x9b\xb0\x8e\xe5\x8fv\x022]4\x18U\xc57\xe2)\x90u>?'), bytearray(b'|}\xf8bfj\x97\xbau\xa9\x1d\xacV\x07{\xfaZ\x9e\xde\xb8\x14\x87c?\x00+\xb0\x80\xba&\x9d\xe1'), bytearray(b'\x8b\x87\xbc_:6\xc88\xc4\xbe_\xb2\xa0X\x998\xa6\xba6S\xe5JZa\x0eH\x9c5\x07SL*'), bytearray(b'`\x01\xc4J\xcd\x92$N\xd5 \xef<p@\x0b)i\xd7\x05 W\xb8h$\xb7\xd4\xd0\xad\x03\xd3\x06\x8a'), bytearray(b'\xa2\xaey\xc0\r\xb1\x08\xd2/\x18\x91\xaf#\x13\xcc\x1f\xe1\tvA\xde\xba\x89\xd9\x99\x9c\x99\x9cJ\xc8\x17\x99'), bytearray(b'\x83<;\xbe\x14\xb2>kj9\x8e\rl\x0b\xde8\x94\xd9\xce=0\x7f\x11\x8a\xe7\x10\x03\xddH\xc5&\xe5'), bytearray(b'\x8a\xe9\x0e]\x0esrJF\xf2\xc6\xe8\xff>|\x16\x89\xdex\xce\xa3|\xf7b\xe1\xdc\xd1ad\xfeR\x04'), bytearray(b'\xbc\xfb\xd2t\xa3\xfeD\x9f2&\r\xac\x15\x1d\xdeTb\xe7\xa60\x10\xfa\x9e\x87\xd0Nn\xbc\x8b\xe1\x084'), bytearray(b'\xcf\x94)d7\xf0I\x14\xd4\xfb\x08_\xde\xde8\xb447p\xf7\xedX\x8d\xfa\xd5d7pj\xb8\xd7\xfe'), bytearray(b'\xba\x9b\xef?\x1ct\x05)\xa9\xf1A\x89eu\xf8\xb6\x93>l(?\xb49\xb2\xc2\xedS\xb7P\xdd\x12\xc5'), bytearray(b'\x88\xa3\xa0\x03\xe1\xd5P\x15\xbfN\xfb\x07\xbe\xe1\xe0\xfb\xa2\xde\xbc\x039\x9f\xbd\xd7sWv[\x97\xb8\x8d\x08'), bytearray(b'E"_|\n\xae\x10mv\xba\xea}1\xe5\xed\x9cZ]\xe2d$ \xf9\xf4C\xef6f\xf2[!\x8a'), bytearray(b':\x1d*\x07n3\xbe\x12\x19\x89p\x05l-z2\xbf\x1e\xcb\x02ah\xbee\x87\x1eV=\xad\xdc\x98\xdd'), bytearray(b'j\xce\xee}\x11\x1dwk5\x16\x8f\xfb\xdf\xf8\x10\x10\x8e\x89\x1b\xbfs\x06F_+.\x9c-\x7f\xaaY\xf8'), bytearray(b'\xd6\xff\xa5\xef\t0\xbfD\xbb\x85|\xe0^pz\x8f4\xfd\xce\xc5\x88\x7flV\t\x1a9\x18\x9c\x94\x03 '), bytearray(b'\xd0\xfb\x01\xb0\x82\x16v\xee\x154wZ\xc3\xbd\xb6e\xcaJ\xb12\xd8\xa9\xe7\xe2!\x1bm\xde\xfa}f\x16'), bytearray(b'\xbb\xcd\xfb\x8c\x99\xd3P\xe1B\xc6\xf3\x08\xca:E\xf63w\x99\xac\xb2;*d\xf9\x00\x13\xa6\xde\x1d>*'), bytearray(b"K*\xc5\xc1X\xb1|>o\x92\x1cF\'\xb5\xa5\x08\xac?\xa6\xb6\xb4\xaa\xe1\x8d\x89\xce\xfb\x90\x11\xb6m\xb9"), bytearray(b'%Ud2m\xa9\x8b\xd5\x1e\x13\xb0\xbfsq\xb4\x1cl\xad\x82\xd7)\x86\xdf\xa9\x1e\xa8\xef\xda\x7f\xc5\x1d\x02'), bytearray(b'\x0b\x18ro\xbbU\xd6Oo\xf6\xcao\xf9r\xa2\xd4UcQ\x82\xc2B\x18\x1a\\\xfe\xcc\ni3N\x9a'), bytearray(b'\\\x9ax\x06(0f\n\x17\xe1Y\xf3v\xb5\xc8\xc1\xf4T\x85@\xbc\xfe>VTWr\r\xcdm\xda\xbf'), bytearray(b'M\x80\xef{\xc4\xb5K\x90\xe9\xe4Hz/1+6W\xcc\xef\xed\xd49\xfd\xfd?\x82\xa2\xae\xb8@5G'), bytearray(b']a\x08\xb7~\xfd\x19*\x14\xe4\x96\x113\x05,\x10\xaa\x94t]\xa4\x01Q\xe7)\xe1\xb4\xc1\xc4\xd0L\x1a'), bytearray(b'F{\xca\xdc\x8f\xb0n\x95\x01\xdb\xa5\x86\xf6P\xc7S\x1d\x85!\xfa\xa1q\xa0\xa5\x1c\xc7\x1e\x97\x06\xe2\x10U'), bytearray(b'S\x17hv\x92\x866\x87\xc2\x03\xf9\x0c)\xe6Q|\xa4\xd2\x8bm\xc0\xf6\xbaz\xb9\xd3\x9a\xad\xee\xcbM\xff'), bytearray(b'\x81\xa6g\x06\xff/\xe5|\x94\x13\x87\xc1Q\xe3\xc5\xd7\xbe\xf9\xe2o\n-\xdb4\x85\xd7\xf9\xc1\xc4\x84\xa5\xfa'), bytearray(b'\xe9\\\xff\x7f\xa2\x86w\xa9\xce\xe7\x80\x98<\xc8\xa2\n\xab\xbeq\x84\xe6/\xc6\xcf=V\xa7\xdd=M\x96\x91'), bytearray(b'\xb0\xb6\xc5*\xf2\xc29\xc8\xb5\x13\xbd~\xa8&\xe3T\xb4\xb3pN\xb2s\x95\xb0\x1a\x95\x0e\x86L\xfb\xc9u'), bytearray(b'\x7fI\xe5{W\x0e\xd3\xde\xbd{\xf4y\x86\xfa\xb96\x08\xdd\xedo\x14\n_\x18\xb0\xe9\xf5g\x14\x0f\x97\x89'), bytearray(b'\x94\xf5\xa1#q\xa4\xa9\x12\x8eS\xad\xd5\x0e\x08\xac\xcf\xe5J\xbc\xc4\x9d\xc0\xbe\x1c\xf7r\xa8\x9a\xe2S6\x84'), bytearray(b',\x16\xdf \x13\xa6\xe6\x10n\x1c3.\xefV\xb8yB\xe7\x80\xd9z\x00\xd2Ay\x93|>Se]\xbc'), bytearray(b'H\x90\x8e\x83S\xc8\x80\x12\xbc\xf5\xd0I\xb9\xfbz\xfbUhGE\xd4q\xc0\xfe*-\xb9\xc2S\x19\x95\x7f'), bytearray(b'{\x1bWS_\xb4\x9a\xed2cN;NS\xd6|\r\xb5c\x0e%N\\\xbc\xb1\x9d\xa5GK\x01\xa9\xdf'), bytearray(b'\xee\x15\xd0H{e\x07\x9f\xd9\xd5Jw\x89\xb4\x8f\xe5M\x0b\xc1Fst\xd1\xc7\x13\x91O&\xa6\xb5\xf7\xc3'), bytearray(b'\xfc\xf4\x13\xa4\x17\xcd\x86\xdbi_\xc7X\x1a\xb2\xf2oUZ\x01\x95\x98\x1f\xce[ rM\x9bA\xec\xc7\xf5'), bytearray(b"&\\,2-\xb8\xe1\xb8\r\xdd\xa7\x08\xdfe\xf7U\xbf\xc2\x1eKY\xb3\xf7\xb455H1\',}G"), bytearray(b'n\xc8\x07\xffz\x16\xbf\xe6\xe2\x10\xa8[D\x82\x0f\x19{\n\x83o\t\xf3\xca?\x87C\x99\xfe\xae\xe6\xe8\xe4'), bytearray(b'0\xbf\xedo\t\x1e\x1biy\xab!\r5)\x04|.\xb1\xc4\x8d\xdf\xaas7\x01\x96\xb6\x11s\xd6\x13\xc0'), bytearray(b'\x1cs\x08\x83\xd3\x10\x04\xa9,(\xe2\x01W\xc3\xb6\x15&\xc2\xbd\x19C5\xcc1\xc4Y\xbe\xfb\xdbG\x08i'), bytearray(b'\x16#\x17\xbb\xab\xf6[d\x06\xef9?\xd3\xd2\xfd\xcd\xe5\xb6`r\xad\xd2\xfc\x89o\xe9\xe3\xfb\x8f\xb5\xf5+'), bytearray(b'Y!\xfbF\xc52\x0c\xaa\xc0\xf9\x9f\xda`\xae}\x9b\xd0\xebC\xe9\xfd\xf5\xee\xf3\x91\xc9i\xd0\xca?\np'), bytearray(b'b\xc8\xb9\xeb\xea\x15p\x9b\xfa\x8c]\xa2=\x84;b\xc3\xa5O\xd2\xe7\x0f^a\x97/\xd8\xc3\xc2\xae\x90\xc6'), bytearray(b'%T\xf8\xaeg\x83\x88BG\xe2\xf0K\x0e\xca\xe7\xed\xb8\x84\x8d\x9c\xe7\x98\x0c\x87C\xe0!)\x9e\xefu\xdd'), bytearray(b'n\xe2\r\x17*\xc4\xaf/Z\xb9\x08\xe8\xc5\xb1\xbd(\xe1bj)\x00\x08_\x8dE\x7f\x8d2\xe3.EW'), bytearray(b'\xcds\x17\xa5\xa2L:\x9a\x14("\xd3\x14\x1c\xaa\xcfL\x9ba\xd496\x80\xe9-L\xe5\x17\xc7\xf1]\x00'), bytearray(b'\xd4\xe3\x16\xb6d\x9e\x8f\xdb|\x9b\xbe\xddi\x9b\xd0\xb4Z\xff\xf1\xeb\xdf\xfd\xf1\xc7\x0b\xf8A\xb6{z(\x8e'), bytearray(b'|\xcf7]7p\x03\x85\x06\xaf\xb7k_\xf2\xbd\xbd L2\t\x88\x99J"\x1c.zn,\xba\x08\x11'), bytearray(b'\xfbt\\\x88\x9bJ\xf6\xd3\x9e\x80\xf0\x13!\x17Z\xbe\r\xc1p\xc4\xb9\xdau\xa5L\x80\x0b"\xf00r\xcc'), bytearray(b'\xf8\xc9\xdd\xfb\xe6\xb3[\x0c\xed\xeb\xfb.Hx\xb7\xc4A:\xde\x82L\xe2\xf9\xb3\xcf\xf0\xfb\xa9\x85\xdd<\xeb'), bytearray(b"\x17\x91\x8c\xa4|\'\xc9\xd7==\x04G\x10\xb6\x89ES\x06t\xae%\xcc\xf2\xc4\xee\x8c>\x9c\x16\x0eL\xcc"), bytearray(b'\xd5\xfb\xcap\xcd\xe9UdYc\x01\xfe\xe4\xfa\x0cAB\xf0\xc6\x02\x1e\x06\xaa\xcd\x06\xc9d\xd1/R\x1e1'), bytearray(b"4\x88U\x9aDC\xe5\'\xe3\x1d\xae\xf8qS?\xf2Q$.%Z\x0e\x92\x88X\xee\xe0J\x99\xf1|\xbd"), bytearray(b'\xda\x8e\xeb\xa8\xc0j/\xff\xf8\xbd\xed\x1eF\x89o\x82\xab>\xf0^\x05\r\x83\xa7D\xf9\x7f#\xee\xab;\n'), bytearray(b'\xd8i\xa26\x84\xf5\x0bZ\xde\xfc\x1e\\"\xd40\xe9\x13\xf0\x9bq\xb5h\xc4m]\xb7#\xd84\x98wB'), bytearray(b'\xebH\x9b\xa93M\x952\xe5j\xd5US\xeb\xc6\xf6\xf6\xef\x15~R\xd6\xa4dd\xc2\xaa\xf8\x16\xc5\x7f\xa9'), bytearray(b'wj\x9abExF\x06/\xd3g\xea7\x7f?<\x96\x82\xf7o\xa1_+\xac\xe32\xb3HR\x9b\xe4\x1f'), bytearray(b'\x05\x02\x84\xe8\x0cm\x19\xd8\xb9(Q\xd6\x07|\x01)K\xad\xf6\xc1\xfcO:\xfb]\xf9\xee\xe0\x9b\xfbD\x1f'), bytearray(b'\xad\x94\xe7%\x08\xa9[bM\xfc\xbf\xf9\xc0\xd9\x12\x7f\x9b\x90\x0cQ<\x88\xcb\xdck\xdaR\x9aG\xa7\x13v'), bytearray(b'44\x184VU\x97_&\xb62\x97B\xfen\x12\xd9\x80o64&\x17\x8d\xb8\x92@f8\x10\x96k'), bytearray(b'\xfb\xaf\xf5y\x0e\x98O\xc9\xed\xcf\x8a\x80\x88h\x9c\xf9\x1e\xf3\xec\xb7\xe4\xcdP\xef\x7fw6z\xd4\x1c\xce`'), bytearray(b'\xa5\x1f[\xda\x90m\xabk?\xfcc\x81CU\xd1<\xc1\x93\xda9k\xa6\x85_c\xac\xcf$\x180\t\x8e'), bytearray(b';\x99ZGRTj\xee\xbd\xa8V\xb12\x14\xfe\xfb\x02q\x8c\xa3\xb2;\xca\x13\xc7\xef\x15\xd5\xf49\x86Y'), bytearray(b'\x00\xe65\xfa\x05\x00\x01\xed\x97\xb3\xf5\xf3\xd0\x16E\x16\xe9MhtA\x9a\xb6"~\x15\xae\x03\xc4\xd0\xc2^'), bytearray(b"\xe3fw\x95\x02\xe0\xf4\xe4\xef-\xc1]\'\xa3\x8f\x1c\x88\xc1\x85\xccc\xaa\xea\xc8\xf6\xee\x94\x84&\xa5\x93,"), bytearray(b"\tu]\xc0\xad6\x91\xfeI\x08\tZ\x97]+\xeb\xcd\xed\x93\'c4\x86\xd7Y\xfao\xfef\xad\xce\xfa"), bytearray(b'(\xc7\x8c\xbe\x16\xaa\xa3\xdf\xc3[g\xd1t\x92\xec\xb2R~\x91\xc2\x99g\xa0\xd8\x85F\xa4d\xd1\xa1\x96\xeb'), bytearray(b'\xd7\x04\xfe2UyIU\x05\xb3\xdaO\xb6\xe1\x7f\x97\xe7\xce\x1c\x16\x1e\xa3\x0bG\x848[Z\xdd?T\xcb'), bytearray(b"\xc1QP\xd1\r\xf9e\xaa\xbc\xdf\x05y=\x05\xc9\xb4\xbah\xad\x07O\xb3T\x12\'\x81\xed}\xc19\xe7D"), bytearray(b'GTO\x852Za\xba-\xf1\xb9B\xf2\xc3\x08\xec\xbdX\xb5\xe7\xc7"\xe0u1xp\xf2\xa7\xaa]`'), bytearray(b'Sz`.\xc0\xea\xa2PF\x98\x1c&\xce\x98x9!\xa1e\xa1\xe6\xe9\xfew\x14v\x01\xee\xe9Y\xfd\xb7'), bytearray(b"\x90\xa2{\x9f\x9f\x9d\xcf\n\'\x0eN\x84&\xb5+\x84\x9a\xff\xc0\xa0\\o\x17\xd3\xc4,f\x92KF\x00\xaf"), bytearray(b'\x93#8\x93\xc7\xb9\xcf\x0f+k\x18-\xe2\x96\x89C\xb9\xe2\xa2\xcd\x96uR\x80M\xf5B\x03M\xebJ|'), bytearray(b'\x01KYH\xbf\x1a\xd8s\xa4\x1aE+4\xc0\xb9b\x8f$\x7f\xec\xb2f\xb7\xfbxb$9\x91Y\xaf0'), bytearray(b'\x85\x89\x8e\xa3\xf2\x96\xe0L\xe9\xed\xba/#9\x04\x8aw\xe1\xdb&e\x1e\x05?XTA\x98c\x9b\x8e\xe8'), bytearray(b'\xaf\x8et\xb7M\xdd\x97l\x9d\x9b!@\xd4\xed\xba\xbe3n\xde\xd1\x94\x88\xa2^\xdd\x7fz=\x8b\x8b\x95l'), bytearray(b'\xb9\x8b\x174\x8b\x9b1\xa6\x03\xdd:\xd1\xac\xf9k\x97\x15\xd6\xb1`+z\x9f\x02\xd9~\x83\xa0Oj\xe8\x8e'), bytearray(b'l\x06V\xa4\xfd\xe2\xb4Y\xbd\xb4:\xd6lX\xf5\xbf\xc7\xa5\xccwwm\xc4\xf4\xea\xad\xf5M\xe7n,\x9b'), bytearray(b',\xdb\xa5\xda\xdfm\xfc6?\x17\xa8]~\xe4o4\x93A\x8f\xf0\x83\xaf\x8f`F\xa6W\xe28lB\xd6'), bytearray(b'\xf9\xaa\xdf\xe3V\xff8L\xf1R\x07h2\x97\xd6\xab\x05\x91\xcc\x85>}\xfa\x9b\xdb\x1a%\xf2\xbe\x8d\xd7\xfa'), bytearray(b"\xff\xb4\x07\xe0Ir\xa4?\xb5\xce<\xbc\xd5\xeb\xf3E\xdf5\x02\x11u\x86 \xccA\x84\x12R\xa6\xf5\'\x8e"), bytearray(b'!\x01\x0b\xcfR\x84\x9e\xa9x\xefPH$\xe4\xbaQ\xa5\xe2\xbc^\xc2\xbfG\xb0\x95\xffK\x85\x00\xb7\xa1\xb4'), bytearray(b'Z\xe8E\x8el\x90\xde%\xd0\xa8\x14\x07\x86b\x9cl\x1e\xbfay,I\xaa1\x85\x0c%\xfc\xbfEX\x8e'), bytearray(b"\x93\x0f\x83~1\xb4\x8f/\xd5\x10\xf7:\xf5\xc6\x1f3\xa9\xc25`\x1e0\xf1\xde\x8azG6)\xad:\'"), bytearray(b'\xf7lc:\xc7\xe5\xcd{\x0ct\xe8\xe4g\x97\xf0\xecTF\xc0\xbf-7\x9f\xb7}\x85\xe1\x050\xe3\xa5\xd7'), bytearray(b'\xe4\xb3:0\xe9\xcd%\xe8\x8d\x82\x9a\xfcc\xb3\x08\x89=+\x94\xa6\xc8\xb3\x1dF\x10\xf3|\xfaz/\xab\xd6'), bytearray(b'\x84ZV\xbe\xe3\x08,\xc8k\x1c\x85\x8f\xbf\x94\x19$\xd6\x1cV}<\x18\xc4\xc3\x95`@\x7fH\xedbX'), bytearray(b'\xa2*py\x05`WH\x04\x8aS\xfc]\x87\xc7\xd9\x81\x7f\xee\x12\xed\xae\x9fl]\xe4c_Y"\x055'), bytearray(b'\x97\x18\xaee\xa0\xb5\xa2\x96\xa6\xe1|\x8d\x8c\x8f\xac\xe6Z@\xd1\xfb\x02\x81W\xba|\x87h\xe2xk\x1f\xcd'), bytearray(b'W\xe6\x01o\xf1Au0+\xf2P%\xd6\x87\x1b\xafq\xe7\x10\x92\x9b\x96\xb2\xe8\\.\x8b\xda}\x12Ja'), bytearray(b'^\xe4\xc3\xf4\xd3G\xa5\xb9b\x80[\x99t\x08Luv\x02\x86\xe5\xf7\x97\x9a@\xdb\xfe\x87\xe1\x13&q\xae'), bytearray(b'\xdc\xfc\xef[\xaeI5\x88?\x82#Vi\xd3\xa3\x83^\xf2\xacV\xc5\xa9\xe2\xc5\xfdw\xb3\x91\xb0\xd3h%'), bytearray(b'\xa8yy\xa3\t\xd0\xdb\xdc\x9f,\x1d4\x12\x7f{\x15\xb0\x99\xa4\xeby\xfb\xa7\xfd\x82\xb39\xc7\xc1l\xdd='), bytearray(b'\xcd\xac\xdd\xbdk\xb2\xd8\x1a^u}!\xffS\xca\x0c7\xf3hC&y\xd4\xa7\xc3\xba,v\xd5\xe4&\xe9'), bytearray(b'Zr\xa9\xc1\x05\xa4`\x82\xa1\xaa4G\x1d\x1e72\r\x89iMd\xe1\xd5\xaa*\x0c\x13\x8e\xb0\xd5%\xe3'), bytearray(b'\xaf\xc0\x90\x15y;\xce\xd26\xa7\x95\xb9}\x05\x99\xc8\x1e<A\x9a\xd1\xdb\xe4t\x0b\x17\xd8`\xbfD\xd8I'), bytearray(b'\x1f\xb0A\xc0T\xf6\x1d\x19\x86\x92\x83\xaay\xda\xec\xa9\xa6\x18L\xcf\xd7\xb8\xfa\xf5\xab\xbb1\xdf*\x81\xe9\x91'), bytearray(b'\x04\x83Xm\x8b(\x89\xaa\xe9\x89\xfe\xf3@\x82\xe4\xae\xdc\x8b\xff\xc5\x08>\r\r+\xf2\xefN\x94\xa9TK'), bytearray(b'\xc5\x07\x80*M\xb7\xe0\xa6/\x19\x12\xbc\xabr\x83\xcb\x86\xae\xd8\xa6c*f\xd2fa\x17\xc5\x04\x07\xc5D'), bytearray(b"v;\x94\xde/\'8\xbfH.M\nO\xe2@d\xc3\x93O\x9b\xfb\xf3d\x9a\xa2d\xa5\x11\x14~N\x8c"), bytearray(b'\x1a\x82\xbf\xa5\x1e\xc7f,\x80a\xd2ze\xc8l,\x81m74\x0cd@2\xd9\xb0\n\x9a\xa0\xb3\x8c\n'), bytearray(b"\xda\xd3\xa1{1\x81\x84\xb5\xd0\xf8\xf4[\xd4\xe1\xf6U@F\x0c&\x9d\x0c\xcd\'\x873dz\x0c\xb1\xfb\xcc"), bytearray(b'PS\xe6B\xc7\xa2\x964]}\xe4\xe4\x96\xc8\xf2\xf7g1Y\\\xc2.=\xb6\xb7\x01\x9b\xbb\xb8\xd8\xaa\x99'), bytearray(b'a\xe9\xf0W\xf7\x0c\x8a\xd9}\xa7\xd8w\xcf\xdaFp\xc7\xe0\x03\xf6\xf01\x04v4\xa5V\x96\xcf\xa6@\xf1'), bytearray(b'\xc1\x90\xf0\xd0\x00q\xc7\x95a\x9d\xbc\x11\xe0\xadXm\xf71\xedU\xa1\x1b\x1d\x07\x94>.\xa8T\xec\xe8\x90'), bytearray(b'\xf5q\xe9>\x0e\xf7\x92\x06Z\xe9 \xe3\xd2\xaf\xe9\x81R\xad \xf8 \xcbp\x15\x9f10\x94\x97\xe8\xdd\xaa'), bytearray(b'\xfa\xd2\x83\x0c\x1b\xc2\x04\xe7qf\x86\x99\x04\x85\xdf\x05\x08:\x01\xaa\xee\xb5\xf60*s\x83\xd9b\xcb"\xf9'), bytearray(b'}\x15}x\x07\xddk\xd2\xf7]O4\xcd\xa3\xd4\xe3\\\xd9\xf5\xd3\x07re\xdd\xc5\x86<\x87\x18N?\x91'), bytearray(b'\xd2\xc5\x08^\xdb\xce+\n\x90w\xddvSV\x8e\x92\x9f\xa9@\x16KI\x05\xce\x93Ad\x80\\\xd2,i'), bytearray(b'\xe4J\xb6m\xd9i&\xf6nn\x92P=z\x85K\xe7$\x12\xc9;\xe3G\xf6\xe2\xb2\xcdT\x85\x0e\x95\xca'), bytearray(b'N\xaa\xda>^\xf1=/\xad\x96\x1fua\x83\xdaa\xb4\x12\x88M::f`\xd8i\xbf\xa9\x87\xf3\xc5\xcb'), bytearray(b"\xdaK\xa2\xab\xdb9\x9e\x97\x1c\x90V9a\xfcY\xf7h\x90\x1a\xe8=\xb1\xcf\'\xe9\xbc\xed;\xef\x905\x93")]
    
    
    print("INITIAL TESTS RUNNING...")
    i = 0
        
    sample_data_len = len(sample_data)
    while i < 256:
        j = 0
        while j < sample_data_len:
            sample_data[j] = sample_data[j] ^ i
            j = j + 1
    
        sample_data[5] = i
        
        if hash_block_for_testing( sample_data )[::-1] != hash_arr[i]:
        
            print("!!!!!!!!!!!! ERROR !!!!!!!!!!!!")
            print("Test calculation could not be performed correctly!")
            print("We recommend using Python 3.6 and OpenCV 3.2")
            
            
            print("Your OpenCV version: "+cv2.__version__)
            print("Your Python version: "+platform.python_version())
            
            print("Please install Python 3.6 first. Then run the following command.")
            print("pip3 install opencv-python==3.2.0.6 --force-reinstall")
            exit()        
        
        
        i = i + 1
    
    
    print("INITIAL TESTS SUCCESSFULLY COMPLETED")
        
    standalone_miner(addr, paddr, stlxaddr, mining_id)
