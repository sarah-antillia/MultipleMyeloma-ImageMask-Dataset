# Copyright 2024 (C) antillia.com. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

#
# MultipleMyelomaImageDataGenerator.py
# 2024/02/26 : Toshiyuki Arai antillia.com
# Generate 512x512 jpg image mask for train and valid,
# originalsize jpg test dataset
#    
#from email.mime import image
from ctypes import c_byte
import sys
import os
import glob
import random
import shutil
import numpy as np

import traceback
import cv2
from PIL import Image, ImageOps, ImageDraw, ImageFilter
from ConfigParser import ConfigParser

GENERATOR = "generator"
AUGMENTOR = "augmentor"

class MultipleMyelomaImageDatasetGenerator:
  # Constructor
  def __init__(self, config_file):
    config = ConfigParser(config_file)
    self.input_dir  = config.get(GENERATOR, "input_dir",  dvalue=None)
    self.output_dir = config.get(GENERATOR, "output_dir", dvalue=None)
    if not os.path.exists(self.input_dir):
      raise Exception("Not found input_dir" + self.input_dir)
    if os.path.exists(self.output_dir):
      shutil.rmtree(self.output_dir)
    if not os.path.exists(self.output_dir):
      os.makedirs(self.output_dir)
                    
    self.W = config.get(GENERATOR, "width",  dvalue=256)
    self.H = config.get(GENERATOR, "height", dvalue=256)
    self.datasets = config.get(GENERATOR, "datasets", dvalue=["train", "valid"])

    self.crop    = config.get(GENERATOR,  "crop",    dvalue=False)
    self.augment = config.get(GENERATOR,  "augment", dvalue=False)
    self.flip   = config.get(AUGMENTOR,   "flip",    dvalue=True)
    self.mirror   = config.get(AUGMENTOR, "mirror",  dvalue=True)
    self.ANGLES  = config.get(AUGMENTOR,  "angles",  dvalue=True)
    self.mask_merge = config.get(GENERATOR,  "mask_merge",  dvalue=True)
    self.backgrounds = []
  
  # dir = "./train/x
  # target = "./test" "./train", "./valid"
  def get_image_filepaths(self, images_dir ="./train/x"):
    pattern = images_dir + "/*.bmp"
    print("--- pattern {}".format(pattern))
    all_files  = glob.glob(pattern)
    image_filepaths = []
    for file in all_files:
      basename = os.path.basename(file)
      if basename.find("_") == -1:
        image_filepaths.append(file)
    return image_filepaths

  def get_mask_filepaths(self, image_filepath, mask_dir):
    basename = os.path.basename(image_filepath)
    name     = basename.split(".")[0]
    mask_filepattern  = mask_dir + "/" + name + "_*.bmp"
    mask_filepaths    = glob.glob(mask_filepattern)
    return mask_filepaths

  def create_backgrounds(self, image_filepaths, num):
    background_files = random.sample(image_filepaths, num)
    for background_file in background_files:
      img = Image.open(background_file)
      img = img.resize((self.W, self.H))
      
      blurred = img.filter(filter=ImageFilter.BLUR)
      self.backgrounds.append(blurred)

  def generate(self):
    for dataset in self.datasets:
      input_subdir  = os.path.join(self.input_dir, dataset)
      output_subdir = os.path.join(self.output_dir, dataset)

      self.create(input_subdir, output_subdir, crop_ellipse=False, debug=False)

  def create(self, input_dir, output_dir, crop_ellipse=False, debug=False):
    images_dir = input_dir + "/x/"
    masks_dir  = input_dir + "/y/"
    image_filepaths  = self.get_image_filepaths(images_dir)
    if os.path.exists(output_dir):
      shutil.rmtree(output_dir)
    if not os.path.exists(output_dir):
      os.makedirs(output_dir)
    
    #self.create_backgrounds(image_filepaths, 20)

    output_images_dir = os.path.join(output_dir, "images")
    output_masks_dir  = os.path.join(output_dir, "masks")
    if not os.path.exists(output_images_dir):
      os.makedirs(output_images_dir)
    if not os.path.exists(output_masks_dir):
      os.makedirs(output_masks_dir)
    
    for image_filepath in image_filepaths:
      basename = os.path.basename(image_filepath)
      name     = basename.split(".")[0]
      if name == "610":
        print("Skipping unmatched {}".format(image_filepath))
        continue

      img         = Image.open(image_filepath)
      # 1 Create resize_image of size 256x256
      img_resized = self.create_resized_images(image_filepath, mask=False)
      
      output_img_filepath = os.path.join(output_images_dir, name + ".jpg")
      # 2 Save the img_resized as a jpg file.
      #img_resized.save(output_img_filepath)
      print("=== Saved image_filepath {} as {}".format(image_filepath, output_img_filepath))

      # 3 Get some mask_filepaths corresponding to the image_filepath
      mask_filepaths = self.get_mask_filepaths(image_filepath, masks_dir)

      if  mask_filepaths ==None or len(mask_filepaths) ==0 :
       print("---Input_dir {}".format(input_dir))
       img.save(output_img_filepath)
       print("==== Saved image file only without resizing")
       continue
      else:
        img_resized.save(output_img_filepath)
      mask = np.zeros((self.W, self.H, 3), dtype =np.uint8)
      output_mask_filepath =  os.path.join(output_masks_dir, name + ".jpg")

      for mask_filepath in mask_filepaths:
        mask_basename = os.path.basename(mask_filepath)
        print(mask_basename)
        mask_filename   = mask_basename.split(".")[0]
        print("-------mask_filename {}".format(mask_filename))
        # 4 Create mask_image of size 256x256
        print("=== Create mask_image_resized from {}".format(mask_filepath))
        #PIL image format
        mask_img_resized   = self.create_resized_images(mask_filepath, mask=True)
        if self.mask_merge:
          mask_x = np.array(mask_img_resized, dtype=np.uint8)
          mask += mask_x
        else:
          pass
      if self.mask_merge:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)
        mask_img = Image.fromarray(mask)
        mask_img.save(output_mask_filepath)
        print("=== Save mask_image     {}".format(output_mask_filepath))

      if self.augment:
        self.create_augmented_image_mask(name, img_resized, mask_img , output_images_dir, output_masks_dir)

  def create_augmented_image_mask(self, name, resized_image, resized_mask , output_images_dir, output_masks_dir):
    for angle in self.ANGLES:
        rotated_image = resized_image.rotate(angle)
        rotated_mask  = resized_mask.rotate(angle)
        output_filename = "rotated_" + str(angle) + "_" + name + ".jpg"

        rotated_image_file = os.path.join(output_images_dir, output_filename)
        rotated_image.save(rotated_image_file)
        rotated_mask_file = os.path.join(output_masks_dir, output_filename)
        rotated_mask.save(rotated_mask_file)
      
    # flipp
    if self.flip:
      flipped_image =  ImageOps.flip(resized_image)
      flipped_mask  =  ImageOps.flip(resized_mask)
      output_filename = "flipped_" + name + ".jpg"

      flipped_image_file = os.path.join(output_images_dir, output_filename)
      flipped_image.save(flipped_image_file)
      flipped_mask_file = os.path.join(output_masks_dir, output_filename)
      flipped_mask.save(flipped_mask_file)

    # mirror
    if self.mirror:
      mirrored_image = ImageOps.mirror(resized_image)
      mirrored_mask  = ImageOps.mirror(resized_mask)
    
      output_filename = "mirrored_"  + name + ".jpg"
      mirrored_image_file = os.path.join(output_images_dir, output_filename)
      mirrored_image.save(mirrored_image_file)
      mirrored_mask_file = os.path.join(output_masks_dir, output_filename)
      mirrored_mask.save(mirrored_mask_file)

  def crop_ellipse(self, img):
     img = img.convert("RGB")  
     height,width = img.size
     mask = Image.new('L', [height,width] , 0)
     draw = ImageDraw.Draw(mask)
     draw.ellipse([(0,0), (height,width)], fill=255) #, outline="white")
     #mask = mask.filter(ImageFilter.GaussianBlur(10))
     img_arr  = np.array(img)
     mask_arr = np.array(mask)
     final_img_arr = np.dstack((img_arr, mask_arr))
     final_img_arr = final_img_arr.copy()
     cropped = Image.fromarray(final_img_arr)
     return cropped

  # Create a resized_resized_image from each original file in image_filepaths
  def create_resized_images(self, image_filepath, mask=False):
    img = Image.open(image_filepath)
    print("---create_resized_resized_images {}".format(image_filepath))
    #pixel = img.getpixel((128, 128))
    # We use the following fixed pixel for a background image.
    pixel = (207, 196, 208)
    pixel = (200, 180, 180)
    pixel = (207, 196, 208)
    if mask:
      pixel = (0, 0, 0)
    print("----pixel {}".format(pixel))
    w, h = img.size
    max = w
    if h > w:
      max = h
    if max < self.W:
      max = self.W
    # 1 Create a black background image
    background = Image.new("RGB", (max, max), pixel) # (0, 0, 0))
    #input("----HIT")
    # 2 Paste the original img to the background image at (x, y) position.
    print(img.format, img.size, img.mode)
    print(background.format, background.size, background.mode)

    x = int( (max - w)/2 )
    y = int( (max - h)/2 )
    background.paste(img, (x, y))

    background_resized = background.resize((self.W, self.H))
    if mask:
      background_resized = self.convert2WhiteMask(background_resized)

    return background_resized

  # 2023.05/15
  def get_boundinbox(self, pil_mask_img_resized):
        mask_img = np.array(pil_mask_img_resized)

        mask_img= cv2.cvtColor(mask_img,  cv2.COLOR_RGB2GRAY)
      
        H, W = mask_img.shape[:2]
       
        contours, hierarchy = cv2.findContours(mask_img, 
           cv2.RETR_EXTERNAL, 
           cv2.CHAIN_APPROX_SIMPLE)
       
        contours = max(contours, key=lambda x: cv2.contourArea(x))
        x, y, w, h = cv2.boundingRect(contours)
        print("---x {} y {} w {} h {}".format(x, y, w, h))
        #Compute bouding box of YOLO format.
        return (x, y, w, h)
  
  def convert2WhiteMask(self, image):
    w, h = image.size
    for y in range(h):
      for x in range(w):
        pixel = image.getpixel((x, y))
        if pixel != (0, 0, 0):
          pixel = (255, 255, 255) #White
          image.putpixel((x, y), pixel) 
    return image

"""
INPUT:

./TCIA_SegPC_dataset
├─test
├─train
└─valid


Output:
./MultipleMyeloma_ImageMask-Dataset_V2
├─test
├─train
└─valid
 
"""

# 
# python MultipleMyelomaImageDatasetGenerator generator.config
#
if __name__ == "__main__":
  try: 
    config_file = "./generator.config"
    if not os.path.exists(config_file):
      raise Exception("Not found config_file " + config_file) 
    generator = MultipleMyelomaImageDatasetGenerator(config_file)
    generator.generate()
  except:
    traceback.print_exc()

      