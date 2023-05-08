
import os
import pickle
from tqdm import tqdm

from scipy import io
import numpy as np
import torch
import torchvision
from torch.utils.data import DataLoader

import json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'config.env'))


NUM_FEAT_MNIST = np.int32(784)
NUM_FEAT_SZ    = np.int32(900)

PATH_DATA = os.getenv('PATH_DATA')

with open(os.path.join(os.getcwd(), 'cparams.json'), 'r') as filestream:
    CPARAMS = json.load(filestream)
filestream.close()

DATASET_ID = CPARAMS['DATASET_ID']

with open(os.path.join(os.getcwd(), 'cparams.json'), 'r') as filestream:
    CPARAMS = json.load(filestream)
filestream.close()

with open(os.path.join(os.getcwd(), f'lparams-{DATASET_ID.lower()}.json'), 'r') as filestream:
    LPARAMS = json.load(filestream)
filestream.close()

BATCH_SIZE = LPARAMS['BATCH_SIZE']

if DATASET_ID == 'MNIST':
    
    mnist_train = torchvision.datasets.MNIST(PATH_DATA, train = True, download = True,
                         transform=torchvision.transforms.Compose([
                         torchvision.transforms.ToTensor()
                         ]) )
    mnist_test  = torchvision.datasets.MNIST(PATH_DATA, train = False, download = True,
                         transform=torchvision.transforms.Compose([
                         torchvision.transforms.ToTensor()
                         ]) )
    
    train_loader = DataLoader(mnist_train, batch_size = BATCH_SIZE, shuffle = True)
    test_loader  = DataLoader(mnist_test, batch_size = BATCH_SIZE, shuffle = False)
    
    num_batches = mnist_train.__len__() // BATCH_SIZE
    train_data = torch.empty(num_batches, BATCH_SIZE, NUM_FEAT_MNIST)
    train_labels = torch.empty(num_batches, BATCH_SIZE, 1)
    
    with tqdm(train_loader, unit = 'Batch') as tdata:
        
        for idx, (batch, labels) in enumerate(tdata):
            tdata.set_description(f'Train Batch {idx}\t')
            bsize = batch.shape[0]
            train_data[idx,:,:] = batch.reshape(bsize, -1).type(torch.float32)
            train_labels[idx,:,:] = labels.reshape(bsize, -1).type(torch.float32)
        #end
    #end
    
    num_batches = mnist_test.__len__() // BATCH_SIZE
    test_data = torch.empty(num_batches, BATCH_SIZE, NUM_FEAT_MNIST)
    test_labels = torch.empty(num_batches, BATCH_SIZE, 1)
    
    with tqdm(test_loader, unit = 'Batch') as tdata:
        
        for idx, (batch, labels) in enumerate(tdata):
            tdata.set_description(f'Test Batch {idx}\t')
            bsize = batch.shape[0]
            test_data[idx,:,:] = batch.reshape(bsize, -1).type(torch.float32)
            test_labels[idx,:,:] = labels.reshape(bsize, -1).type(torch.float32)
        #end
    #end
    
elif DATASET_ID == 'SZ':
    
    train_set = io.loadmat(os.path.join(PATH_DATA, DATASET_ID, 'SZ_data.mat'))
    test_set = io.loadmat(os.path.join(PATH_DATA, DATASET_ID, 'SZ_data_test.mat'))
    
    data = train_set['D'].T
    labels = train_set['N_list'].flatten()
    Nfeat = data.shape[-1]
    
    catdata = np.hstack((data, labels.reshape((-1,1))))
    np.random.shuffle(catdata)
    
    data = catdata[:, :Nfeat]
    labels = catdata[:, -1].flatten()
    
    train_data = list()
    train_labels = list()
    num_batches = data.shape[0] // BATCH_SIZE
    train_data = torch.empty(num_batches, BATCH_SIZE, NUM_FEAT_SZ)
    train_labels = torch.empty(num_batches, BATCH_SIZE, 1)
    
    with tqdm(range(num_batches), unit = 'Batch') as tdata:
        
        for n in tdata:
            tdata.set_description(f'Train Batch {n}\t')
            train_data[n,:,:] = torch.Tensor(data[n : n + BATCH_SIZE, :]).type(torch.float32)
            unsqz_labels = torch.Tensor(labels[n : n + BATCH_SIZE]).type(torch.float32)
            train_labels[n,:,:] = unsqz_labels.reshape(-1,1)
        #end
    #end
    
    data = test_set['D'].T
    labels = test_set['N_list'].flatten()
    
    catdata = np.hstack((data, labels.reshape((-1,1))))
    np.random.shuffle(catdata)
    
    data = catdata[:, :Nfeat]
    labels = catdata[:, -1].flatten()
    
    test_data = list()
    test_labels = list()
    num_batches = data.shape[0] // BATCH_SIZE
    test_data = torch.empty(num_batches, BATCH_SIZE, NUM_FEAT_SZ)
    test_labels = torch.empty(num_batches, BATCH_SIZE, 1)
    
    with tqdm(range(num_batches), unit = 'Batch') as tdata:
        
        for n in tdata:
            tdata.set_description(f'Test Batch {n}\t')
            test_data[n,:,:] = torch.Tensor(data[n : n + BATCH_SIZE, :]).type(torch.float32)
            unsqz_labels = torch.Tensor(labels[n : n + BATCH_SIZE]).type(torch.float32)
            test_labels[n,:,:] = unsqz_labels.reshape(-1,1)
        #end
    #end
    
else:
    raise ValueError('Dataset not valid')
#end

path_dump_data = os.path.join(PATH_DATA, DATASET_ID)
if not os.path.exists(path_dump_data):
    os.mkdir(path_dump_data)
#end

train_dataset = {'data' : train_data, 'labels' : train_labels}
test_dataset  = {'data' : test_data, 'labels' : test_labels}

pickle.dump( 
    train_dataset,
    open(os.path.join(path_dump_data, 'train_dataset.pkl'), 'wb')
)

pickle.dump( 
    test_dataset,
    open(os.path.join(path_dump_data, 'test_dataset.pkl'), 'wb')
)

