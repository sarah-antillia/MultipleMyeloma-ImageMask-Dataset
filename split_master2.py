# Copyright 2024 antillia.com Toshiyuki Arai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# split_master.py
# 2024/01/28
# 2024/02/20 Added random.seed(137)

"""
./Hippocampus-base/train
 ├─images
 └─masks

"""
# into test, train and valid dataset.

"""
../Hippocampus-ImageMask-Dataset/├─test
│  ├─images
│  └─masks
├─train
│  ├─images
│  └─masks
└─valid
  ├─images
  └─masks
"""


import os
import sys
import glob
import shutil

import traceback
import random

def split_master(images_dir, masks_dir, output_dir):
  image_files = glob.glob(images_dir + "/*.jpg")
  
  random.seed(137)

  random.shuffle(image_files)
  num = len(image_files)
  num_valid = int(num * 0.9)
  num_test  = int(num * 0.1)
  print("num_valid {}".format(num_valid))
  print("num_test  {}".format(num_test ))

  valid_files = image_files[:num_valid]
  test_files  = image_files[num_valid:]
  valid_dir   = os.path.join(output_dir, "valid")
  test_dir    = os.path.join(output_dir, "test")
  copy(valid_files, masks_dir, valid_dir)
  copy(test_files,  masks_dir, test_dir )


def copy(image_files, masks_dir, dataset_dir):
  out_images_dir = os.path.join(dataset_dir, "images")
  out_masks_dir  = os.path.join(dataset_dir, "masks")

  if not os.path.exists(out_images_dir):
    os.makedirs(out_images_dir)
  if not os.path.exists(out_masks_dir):
    os.makedirs(out_masks_dir)

  for image_file in image_files:
    shutil.copy2(image_file, out_images_dir)
    print("Copied {} to {}".format(image_file, out_images_dir))

    basename = os.path.basename(image_file)
    mask_filepath = os.path.join(masks_dir, basename)
    shutil.copy2(mask_filepath, out_masks_dir)
    print("Copied {} to {}".format(mask_filepath, out_masks_dir))


if __name__ == "__main__":
  try:
    train_dir = "./MultipleMyeloma/train"

     
    images_dir = "./MultipleMyeloma//valid/images/"
    masks_dir  = "./MultipleMyeloma//valid/masks/"
    output_dir = "./MultipleMyeloma-ImageMask-Dataset_V1/"
    if os.path.exists(output_dir):
      shutil.rmtree(output_dir)    
    # 1 Copy original train to new output_dir
    shutil.copytree(train_dir, output_dir + "/train")

    if not os.path.exists(output_dir):
      os.makedirs(output_dir)

    # 2 Split original valid to new valid and test in new output_dir
    split_master(images_dir, masks_dir, output_dir)

  except:
    traceback.print_exc()

