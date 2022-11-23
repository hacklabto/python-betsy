
from tkinter import *
import tkinter as tk
from PIL import Image, ImageTk,ImageDraw
import json
import io
from numpy import tile
from betsy.protocol import CommandSocket
from itertools import product
import time
from PIL import GifImagePlugin

# Opening JSON file
f = open('inventory.json')
inventory = json.load(f)
tile_size = inventory["settings"]["dimensions"]
dims = [  len(inventory["mapping"][0]), len(inventory["mapping"]) ] 

sn_to_ip = {}
for x in inventory["inventory"]:
  sn_to_ip[ x["serial_number"] ] = x["ipv6_link_local"]



# Tile images returns a 2d array of an input image split into tiles of given size.
# Note: It crpos
def tile_img(img, tilesize=18, matrix_dims=[9,6], crop=True):


    if crop: # Crop image to matrix size before anything else:
      img = img.crop((0,0,tilesize*matrix_dims[0],tilesize*matrix_dims[1]))
    else:
      img = img.resize((tilesize*matrix_dims[0],tilesize*matrix_dims[1]))

    w, h = img.size
    imgs = []  
    grid = product(range(0, h-h%tilesize, tilesize), range(0, w-w%tilesize, tilesize))
    for i, j in grid:
        idx_i = int(i/tilesize)
        idx_j = int(j/tilesize)

        box = (j, i, j+tilesize, i+tilesize)
        if len(imgs) < idx_i+1:
          imgs.append([])
        if len(imgs[idx_i]) < idx_j+1:
          imgs[idx_i].append([])
        imgs[idx_i][idx_j]=img.crop(box)
    return imgs



# draw_imgs prints tile arrays
def draw_imgs(imgs):
    app = tk.Tk()
    app.geometry("%dx%d"%(dims[0]*tile_size[0]*1.3,   dims[1]*tile_size[1]*1.3))
    tkImg = []
    x = 0
    for i in range( dims[1] ):
      for j in range (dims[0]):
        tkImg.append(ImageTk.PhotoImage(imgs[i][j]))
        lbl = tk.Label(master=app, image=tkImg[x])
        lbl.grid(row=i, column=j)
        x+=1
    app.mainloop()



# Returns a tile-sized image of the serial #
def serial_img(sn, i=255, j=0):
  image1 = Image.new("RGB", tile_size, (0, 0, 0))
  draw = ImageDraw.Draw(image1)
  draw.text([2,6],sn,fill=(i, j, 0), align=CENTER)
  return image1


# draw_mapping prints the current inventory mapping layout (panel serials) in tk
def draw_mapping(inv = inventory):
    app = tk.Tk()
    app.geometry("%dx%d"%(dims[0]*tile_size[0]*1.3,   dims[1]*tile_size[1]*1.3))

    tkImg = []
    x = 0
    for i in range( dims[1] ):
      for j in range (dims[0]):
        
        img = serial_img("%d"%inv["mapping"][i][j], 255-i*30,  255-j*30)
        img.tobytes("hex", "rgb")
        tkImg.append(ImageTk.PhotoImage(img))
        lbl = tk.Label(master=app, image=tkImg[x])
        lbl.grid(row=i, column=j)
        x+=1
    app.mainloop()


# Simple function to send the Serial number to each panel:
def send_sn_image(inv=inventory):
 csock = CommandSocket("wlp3s0")
 for i in range(len(inv["mapping"])):
   for j in range(len(inv["mapping"][i])):

    sn=inv["mapping"][i][j]
    img = serial_img("%d"%sn, 255-i*30,  255-j*30)
    img_byte_arr = img.tobytes("raw", "RGB")

    img2 = [0]*1944
    for x in range(972):
      img2[x*2] = img_byte_arr[x]


    destaddr = csock.get_ipv6_addr_info(sn_to_ip[sn])
    csock.dpc_data(destaddr,1,bytes(img2))
    # Finally upload the frame buffer to LEDs:
    csock.dpc_upload(destaddr, 1)


# Sends an image array
def send_images(imgs, inv=inventory):
 csock = CommandSocket("wlp3s0")
 for i in range(len(inv["mapping"])):
   for j in range(len(inv["mapping"][i])):
    sn=inv["mapping"][i][j]
    img = imgs[i][j]
    # Note: This is exactly half the bytes 972 as the example shows (1944 bytes)
    # What is the actual format transmitted? Poop.
    img_byte_arr = img.tobytes("raw", "RGB") # https://pillow.readthedocs.io/en/stable/handbook/concepts.html
    # each consisting of little endian 16-bit per pixel-channel values (48-bit per pixel) arranged left to right, top to bottom. Each buffer is thus 18*18*3*2 or 1944 bytes in size. The high order 4 bits of each 16-bit channel value are ignored.
    # OMG WHYYY
    img2 = [0]*1944
    for x in range(int(972)):
      img2[x*2] = img_byte_arr[x]

    destaddr = csock.get_ipv6_addr_info(sn_to_ip[sn])
    #destaddr=sn_to_ip[sn]
    csock.dpc_data(destaddr,1,bytes(img2))
    # Finally upload the frame buffer to LEDs:
    csock.dpc_upload(destaddr, 1)


# Simple function to send the Serial number to each panel:
def send_reset(inv=inventory):
 csock = CommandSocket("wlp3s0")
 for i in range(len(inv["mapping"])):
   for j in range(len(inv["mapping"][i])):
    sn=inv["mapping"][i][j]
    destaddr = csock.get_ipv6_addr_info(sn_to_ip[sn])
    csock.send_commands("reset firmware",destaddr)



def handle_gif(filename, sleep=0.25):
  imageObject = Image.open(filename)
  # Display individual frames from the loaded animated GIF file
  for frame in range(0,imageObject.n_frames):
      imageObject.seek(frame)

      mypalette = imageObject.getpalette()
      imageObject.putpalette(mypalette)
      new_im = Image.new("RGB", imageObject.size)
      new_im.paste(imageObject)
      hl = tile_img(new_im, 18, crop=False) # False = scale.
      send_images(hl)
      time.sleep(sleep)

## TK Visualization for fun:
#raw_mapping()  # Call this to visualize the current SNs ( GUI )
#draw_imgs(hl)
#draw_mapping()

### Use to reset on bootup; call just once:
#send_reset()
#time.sleep(3)

# Call this to call the SNs to the screen and ensure they're in the right order
send_sn_image() 

# Here, draw a picture!
img = Image.open("nyan2.jpg")
hl = tile_img(img, 18, crop=False) # False = scale.
#send_images(hl)

while 1:
  handle_gif("./nyan.gif",0.025)