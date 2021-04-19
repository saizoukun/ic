from __future__ import division

import argparse
import os 
import os.path as osp
import time
import cv2 
import numpy as np
import pandas as pd
import random 
import pickle as pkl
import itertools
import torch 
import torch.nn as nn
from torch.autograd import Variable
import logging

from Darknet import Darknet
import ObjectDetectionUtil as util
from ObjectDetectionPreprocess import prep_image, inp_to_image

logger = logging.getLogger(__name__)

class test_net(nn.Module):
    def __init__(self, num_layers, input_size):
        super(test_net, self).__init__()
        self.num_layers= num_layers
        self.linear_1 = nn.Linear(input_size, 5)
        self.middle = nn.ModuleList([nn.Linear(5,5) for x in range(num_layers)])
        self.output = nn.Linear(5,2)
    
    def forward(self, x):
        x = x.view(-1)
        fwd = nn.Sequential(self.linear_1, *self.middle, self.output)
        return fwd(x)
        
class ObjectDetectionAPI:
    def __init__(self, base_directory, config_file="cfg/yolov3.cfg", weights_file="data/yolov3.weights", classes_file="data/coco.names", pallet_file="data/pallete"):
        self.base_directory = base_directory
        self.config_file = osp.join(base_directory, config_file)
        self.weights_file = osp.join(base_directory, weights_file)
        self.CUDA = torch.cuda.is_available()
        self.classes = util.load_classes(osp.join(base_directory, classes_file))
        self.num_classes = len(self.classes)
        self.pallete = osp.join(base_directory, pallet_file)

    def get_test_input(self, input_dim):
        img = os.path.join(self.base_directory, "dog-cycle-car.png")
        cwd = os.getcwd()
        os.chdir(os.path.dirname(img))
        img = cv2.imread(os.path.basename(img))
        os.chdir(cwd)
        img = cv2.resize(img, (input_dim, input_dim)) 
        img_ =  img[:,:,::-1].transpose((2,0,1))
        img_ = img_[np.newaxis,:,:,:]/255.0
        img_ = torch.from_numpy(img_).float()
        img_ = Variable(img_)
        
        if self.CUDA:
            img_ = img_.cuda()
        return img_

    def write(self, x, batches, results):
        c1 = tuple(x[1:3].int())
        c2 = tuple(x[3:5].int())
        img = results[int(x[0])]
        cls = int(x[-1])
        label = "{0}".format(self.classes[cls])
        color = random.choice(self.colors)
        cv2.rectangle(img, c1, c2,color, 1)
        t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 1 , 1)[0]
        c2 = c1[0] + t_size[0] + 3, c1[1] + t_size[1] + 4
        cv2.rectangle(img, c1, c2,color, -1)
        cv2.putText(img, label, (c1[0], c1[1] + t_size[1] + 4), cv2.FONT_HERSHEY_PLAIN, 1, [225,255,255], 1)
        return img

    def main(self, images, output_dir="", keyword="", keyword_limit=1, batch_size=1, confidence=0.5, nms_thresh=0.4, resolution=416, scales="1,2,3"):
        start = 0

        #Set up the neural network
        logger.info("Model Loading...")

        model = Darknet(self.config_file)
        model.load_weights(self.weights_file)
        model.net_info["height"] = resolution
        inp_dim = int(model.net_info["height"])
        assert inp_dim % 32 == 0 
        assert inp_dim > 32

        logger.debug(f"Model loaded: {inp_dim}")

        if self.CUDA:
            model.cuda()
       
        model.eval()
        
        #Detection phase
        load_batch = time.time()
        
        cwd = os.getcwd()
        os.chdir(os.path.dirname(images[0]))
        batches = list(map(prep_image, images, [inp_dim for x in range(len(images))]))
        os.chdir(cwd)

        im_batches = [x[0] for x in batches]
        orig_ims = [x[1] for x in batches]
        im_dim_list = [x[2] for x in batches]
        im_dim_list = torch.FloatTensor(im_dim_list).repeat(1,2)
        
        if self.CUDA:
            im_dim_list = im_dim_list.cuda()
        
        leftover = 0
        
        if (len(im_dim_list) % batch_size):
            leftover = 1
            
        logger.info(f"taget images: {len(im_batches)}")

        if batch_size != 1:
            num_batches = len(images) // batch_size + leftover            
            im_batches = [torch.cat((im_batches[i*batch_size : min((i +  1)*batch_size,
                                len(im_batches))]))  for i in range(num_batches)]        

        i = 0

        write = False
        # Test きっと1個目は時間かかるから、1つテスト的にロードして時間を平均化したい？
        model(self.get_test_input(inp_dim), self.CUDA)
        
        start_det_loop = time.time()
        
        objs = {}
        
        logger.info(f"taget batches: {len(im_batches)}")
        results = []
        for batch in im_batches:
            #load the image 
            start = time.time()
            if self.CUDA:
                batch = batch.cuda()

            #Apply offsets to the result predictions
            #Tranform the predictions as described in the YOLO paper
            #flatten the prediction vector 
            # B x (bbox cord x no. of anchors) x grid_w x grid_h --> B x bbox x (all the boxes) 
            # Put every proposed box as a row.
            with torch.no_grad():
                prediction = model(Variable(batch), self.CUDA)
            
            #prediction = prediction[:,scale_indices]
            
            #get the boxes with object confidence > threshold
            #Convert the cordinates to absolute coordinates
            #perform NMS on these boxes, and save the results 
            #I could have done NMS and saving seperately to have a better abstraction
            #But both these operations require looping, hence 
            #clubbing these ops in one loop instead of two. 
            #loops are slower than vectorised operations. 
            
            prediction = util.write_results(prediction, confidence, self.num_classes, nms = True, nms_conf = nms_thresh)
            
            if type(prediction) == int:
                i += 1
                continue

            end = time.time()
            
            prediction[:,0] += i*batch_size
            
            if not write:
                output = prediction
                write = 1
            else:
                output = torch.cat((output, prediction))

            for im_num, image in enumerate(images[i*batch_size: min((i +  1)*batch_size, len(images))]):
                im_id = i*batch_size + im_num
                objs = [self.classes[int(x[-1])] for x in output if int(x[0]) == im_id]
                logger.debug("{0:20s} predicted in {1:6.3f} seconds".format(image.split("/")[-1], (end - start)/batch_size))
                logger.debug("{0:20s} {1:s}".format("Objects Detected:", " ".join(objs)))
                logger.debug("----------------------------------------------------------")
                if len(keyword) > 0:
                    result = objs.count(keyword)
                    result = True if result > 0 and result <= keyword_limit else False
                    results.append([image, result, objs])

            i += 1

            if self.CUDA:
                torch.cuda.synchronize()
            
            time.sleep(0.005)
        
        try:
            output
        except NameError:
            logger.error("No detections were made")
            return results
            
        im_dim_list = torch.index_select(im_dim_list, 0, output[:,0].long())
        scaling_factor = torch.min(inp_dim/im_dim_list,1)[0].view(-1,1)
        
        output[:,[1,3]] -= (inp_dim - scaling_factor*im_dim_list[:,0].view(-1,1))/2
        output[:,[2,4]] -= (inp_dim - scaling_factor*im_dim_list[:,1].view(-1,1))/2
        
        output[:,1:5] /= scaling_factor
        
        for i in range(output.shape[0]):
            output[i, [1,3]] = torch.clamp(output[i, [1,3]], 0.0, im_dim_list[i,0])
            output[i, [2,4]] = torch.clamp(output[i, [2,4]], 0.0, im_dim_list[i,1])
            
        output_recast = time.time()
        
        class_load = time.time()

        self.colors = pkl.load(open(self.pallete, "rb"))
        
        draw = time.time()

        if len(output_dir) != 0:
            os.makedirs(output_dir, exist_ok=True)
            list(map(lambda x: self.write(x, im_batches, orig_ims), output))
            det_names = pd.Series(images).apply(lambda x: "{}/{}/{}".format(output_dir, osp.basename(osp.dirname(x)), osp.basename(x)))
            list(map(util.write_im_dim, det_names, orig_ims))
        
        end = time.time()
        
        logger.debug("")
        logger.debug("SUMMARY")
        logger.debug("----------------------------------------------------------")
        logger.debug("{:25s}: {}".format("Task", "Time Taken (in seconds)"))
        logger.debug("")
        logger.debug("{:25s}: {:2.3f}".format("Loading batch", start_det_loop - load_batch))
        logger.debug("{:25s}: {:2.3f}".format("Detection (" + str(len(images)) +  " images)", output_recast - start_det_loop))
        logger.debug("{:25s}: {:2.3f}".format("Output Processing", class_load - output_recast))
        logger.debug("{:25s}: {:2.3f}".format("Drawing Boxes", end - draw))
        logger.debug("{:25s}: {:2.3f}".format("Average time_per_img", (end - load_batch)/len(images)))
        logger.debug("----------------------------------------------------------")

        torch.cuda.empty_cache()

        return results
        
