import math
import sys
from pathlib import Path

from matplotlib import pyplot
from matplotlib.patches import Rectangle

# import our basic, light-weight png reader library
import imageIO.png

# This is a queue class
class Queue:
    def __init__(self):
        self.items = []

    def isEmpty(self):
        return self.items == []

    def enqueue(self, item):
        self.items.insert(0,item)

    def dequeue(self):
        return self.items.pop()

    def size(self):
        return len(self.items)

# this function reads an RGB color png file and returns width, height, as well as pixel arrays for r,g,b
def readRGBImageToSeparatePixelArrays(input_filename):

    image_reader = imageIO.png.Reader(filename=input_filename)
    # png reader gives us width and height, as well as RGB data in image_rows (a list of rows of RGB triplets)
    (image_width, image_height, rgb_image_rows, rgb_image_info) = image_reader.read()

    print("read image width={}, height={}".format(image_width, image_height))

    # our pixel arrays are lists of lists, where each inner list stores one row of greyscale pixels
    pixel_array_r = []
    pixel_array_g = []
    pixel_array_b = []

    for row in rgb_image_rows:
        pixel_row_r = []
        pixel_row_g = []
        pixel_row_b = []
        r = 0
        g = 0
        b = 0
        for elem in range(len(row)):
            # RGB triplets are stored consecutively in image_rows
            if elem % 3 == 0:
                r = row[elem]
            elif elem % 3 == 1:
                g = row[elem]
            else:
                b = row[elem]
                pixel_row_r.append(r)
                pixel_row_g.append(g)
                pixel_row_b.append(b)

        pixel_array_r.append(pixel_row_r)
        pixel_array_g.append(pixel_row_g)
        pixel_array_b.append(pixel_row_b)

    return (image_width, image_height, pixel_array_r, pixel_array_g, pixel_array_b)


# a useful shortcut method to create a list of lists based array representation for an image, initialized with a value
def createInitializedGreyscalePixelArray(image_width, image_height, initValue = 0):

    new_array = [[initValue for x in range(image_width)] for y in range(image_height)]
    return new_array

#converts coloured image to greyscale
def computeRGBToGreyscale(r, g, b, image_width, image_height):
    
    greyscale_pixel_array = createInitializedGreyscalePixelArray(image_width, image_height)
    
    for y in range(0,image_height):
        for x in range(0,image_width):
            gee = 0.299*r[y][x] + 0.587*g[y][x]+0.114*b[y][x]
            greyscale_pixel_array[y][x] = int(round(gee))
    
    return greyscale_pixel_array

#Computes a contrast stretching from the minimum and maximum values of the input pixel array to the full 8 bit range of values between 0 and 255.
#Every computed value has to be rounded to the nearest integer and stored in the output pixel array as an integer
def scaleTo0And255AndQuantize(pixel_array, image_width, image_height):
    largest = -1
    smallest = 256
    for y in range(0,image_height):
        for x in range(0,image_width):
            smallest = min(pixel_array[y][x],smallest)
            largest = max(pixel_array[y][x],largest)
    grey = createInitializedGreyscalePixelArray(image_width, image_height)
    if(largest == smallest):
        for y in range(0,image_height):
            for x in range(0,image_width):
                grey[y][x] = 0
        return grey
    r = largest - smallest
    m = 255/r
        
    for y in range(0,image_height):
        for x in range(0,image_width):
            aba = round((pixel_array[y][x] - smallest) * m )
            if(aba==-1):
                aba = 0
            grey[y][x] = aba
                
    return grey

#Computes and returns an image that contains the standard deviation of pixels in a 5x5 neighbourhood of the input pixel.
#The resulting image will contain float values.
def computeStandardDeviationImage5x5(pixel_array, image_width, image_height):
    arr = createInitializedGreyscalePixelArray(image_width, image_height)
    size = image_width*image_height
    for y in range(image_height):
        for x in range(image_width):

            mylist = []
            
            for j in range(-2, 3):
                for k in range(-2, 3):
                    if(y+k>=0 and x+j>=0 and y+k<image_height and x+j<image_width):
                        mylist.append(pixel_array[y+k][x+j])

            length = len(mylist)
            
            mean = sum(mylist)/length
            
            for i in range(length):
                mylist[i] = (mylist[i] - mean) ** 2
        
            variance = sum(mylist)/length
    
            sd = math.sqrt(variance)

            arr[y][x] = sd
        
    return arr

# Computes and returns a binary image with values either 0 or 255.
# If the input pixel is smaller than the threshold value, the result pixel is 0, if it is greater or equal to the threshold value it is 255.
def computeThresholdGE(pixel_array, threshold_value, image_width, image_height):
    for y in range(0,image_height):
        for x in range(0,image_width):
            if pixel_array[y][x] < threshold_value:
                pixel_array[y][x] = 0
            else:
                pixel_array[y][x] = 255
        
    return pixel_array

def computeDilation8Nbh3x3FlatSE(pixel_array, image_width, image_height):
    hist = createInitializedGreyscalePixelArray(image_width, image_height)
    for x in range(image_width):
        for y in range(image_height):
            pix = 0
            for k in range(-1,2):
                for j in range(-1,2):
                    ynew = y + j
                    xnew = x + k
                    if min(xnew,ynew)>-1 and ynew < image_height and xnew < image_width:
                        if(pixel_array[ynew][xnew]>0):
                            pix = 1
                        
            hist[y][x] = pix
            
    return hist

def computeErosion8Nbh3x3FlatSE(pixel_array, image_width, image_height):
    hist = createInitializedGreyscalePixelArray(image_width, image_height)
    for x in range(1,image_width-1):
        for y in range(1,image_height-1):
            pix = 1
            for i in range(-1,2):
                for j in range(-1,2):
                    if(pixel_array[y+i][x+j]==0):
                        pix = 0
            hist[y][x] = pix
            
    return hist

def colourConnectedComponents(pixel_array, image_width, image_height, labelCount, startX, startY):
    count = 0
    myQ = Queue()
    myQ.enqueue([startX,startY])
    while(myQ.isEmpty()==False):
        x, y = myQ.dequeue()
        if (min(x,y)<0 or x >= image_width or y >= image_height):
            continue
        if(pixel_array[y][x]==0 or pixel_array[y][x]==labelCount):
            continue
        pixel_array[y][x] = labelCount
        count += 1
        myQ.enqueue([x,y+1])
        myQ.enqueue([x,y-1])
        myQ.enqueue([x+1,y])
        myQ.enqueue([x-1,y])
        
    return pixel_array, count

def computeConnectedComponentLabeling(pixel_array, image_width, image_height):
    
    #tracking variables
    labels = [0]
    labelCount = 0
    
    # set all non zero values to -1
    for x in range(image_width):
        for y in range(image_height):
            if (pixel_array[y][x]!=0):
                pixel_array[y][x] = -1
    
    for y in range(image_height):
        for x in range(image_width):
            if(pixel_array[y][x]==-1):
                labelCount += 1
                pixel_array, labelSize = colourConnectedComponents(pixel_array, image_width, image_height, labelCount, x, y)
                labels.append(labelSize)
    
    return pixel_array, labels

def computeBoundaryBoxBounds(image_width, image_height, connectedComponents_array, largestComponentLabel):
    bbox_min_x = image_width
    bbox_max_x = 0
    bbox_min_y = image_height
    bbox_max_y = 0
    for x in range(image_width):
        for y in range(image_height):
            if(connectedComponents_array[y][x]==largestComponentLabel):
                bbox_min_x = min(bbox_min_x,x)
                bbox_max_x = max(bbox_max_x,x)
                bbox_min_y = min(bbox_min_y,y)
                bbox_max_y = max(bbox_max_y,y)
    return bbox_min_x,bbox_max_x,bbox_min_y,bbox_max_y

# find largest component in connectedComponents_labels and set it to 1
def extractLargestLabel(connectedComponents_labels):
    largestComponentLabel = -1
    largestElement = 0
    for i in range(len(connectedComponents_labels)):
        if(connectedComponents_labels[i]>largestElement):
            largestElement = connectedComponents_labels[i]
            largestComponentLabel = i
    connectedComponents_labels[largestComponentLabel] = 1
    return largestComponentLabel

# Check box ratio
def boxHasExpectedRatio(min_x, max_x, min_y, max_y):
    xSize = max_x - min_x
    ySize = max_y - min_y
    ratio = xSize/ySize
    if(2<=ratio and ratio<=5):
        return True
    else:
        return False

# This is our code skeleton that performs the license plate detection.
# Feel free to try it on your own images of cars, but keep in mind that with our algorithm developed in this lecture,
# we won't detect arbitrary or difficult to detect license plates!
def main():

    command_line_arguments = sys.argv[1:]

    SHOW_DEBUG_FIGURES = True

    # this is the default input image filename
    input_filename = "numberplate1.png"

    if command_line_arguments != []:
        input_filename = command_line_arguments[0]
        SHOW_DEBUG_FIGURES = False

    output_path = Path("output_images")
    if not output_path.exists():
        # create output directory
        output_path.mkdir(parents=True, exist_ok=True)

    output_filename = output_path / Path(input_filename.replace(".png", "_output.png"))
    if len(command_line_arguments) == 2:
        output_filename = Path(command_line_arguments[1])


    # we read in the png file, and receive three pixel arrays for red, green and blue components, respectively
    # each pixel array contains 8 bit integer values between 0 and 255 encoding the color values
    (image_width, image_height, px_array_r, px_array_g, px_array_b) = readRGBImageToSeparatePixelArrays(input_filename)

    # setup the plots for intermediate results in a figure
    fig1, axs1 = pyplot.subplots(2, 2)
    axs1[0, 0].set_title('Input red channel of image')
    axs1[0, 0].imshow(px_array_r, cmap='gray')
    axs1[0, 1].set_title('Input green channel of image')
    axs1[0, 1].imshow(px_array_g, cmap='gray')
    axs1[1, 0].set_title('Input blue channel of image')
    axs1[1, 0].imshow(px_array_b, cmap='gray')


    # STUDENT IMPLEMENTATION here

    px_array = computeRGBToGreyscale(px_array_r, px_array_g, px_array_b, image_width, image_height)
    px_array = scaleTo0And255AndQuantize(px_array, image_width, image_height)
    px_array = computeStandardDeviationImage5x5(px_array, image_width, image_height)
    px_array = scaleTo0And255AndQuantize(px_array, image_width, image_height)
    thresholdValue = 150
    px_array = computeThresholdGE(px_array, thresholdValue, image_width, image_height)
    # dilation and erosion computed 4 times
    for x in range(4):
        px_array = computeDilation8Nbh3x3FlatSE(px_array, image_width, image_height)
    for x in range(4):
        px_array = computeErosion8Nbh3x3FlatSE(px_array, image_width, image_height)

    connectedComponents_array, connectedComponents_labels = computeConnectedComponentLabeling(px_array, image_width, image_height)


    # Find label with largest size and compute a bounding box
    largestComponentLabel = extractLargestLabel(connectedComponents_labels)
    bbox_min_x, bbox_max_x, bbox_min_y, bbox_max_y = computeBoundaryBoxBounds(image_width, image_height, connectedComponents_array, largestComponentLabel)
    
    if not (boxHasExpectedRatio(bbox_min_x, bbox_max_x, bbox_min_y, bbox_max_y)):
        for i in range(3):
            tempLabel = extractLargestLabel(connectedComponents_labels)
            min_x, max_x, min_y, max_y = computeBoundaryBoxBounds(image_width, image_height, connectedComponents_array, tempLabel)
            if(boxHasExpectedRatio(min_x, max_x, min_y, max_y)):
                largestComponentLabel = tempLabel
                bbox_min_x, bbox_max_x, bbox_min_y, bbox_max_y = min_x, max_x, min_y, max_y
                break
            

    px_array = computeRGBToGreyscale(px_array_r, px_array_g, px_array_b, image_width, image_height)

    # Draw a bounding box as a rectangle into the input image
    axs1[1, 1].set_title('Final image of detection')
    axs1[1, 1].imshow(px_array, cmap='gray')
    rect = Rectangle((bbox_min_x, bbox_min_y), bbox_max_x - bbox_min_x, bbox_max_y - bbox_min_y, linewidth=1,
                     edgecolor='g', facecolor='none')
    axs1[1, 1].add_patch(rect)



    # write the output image into output_filename, using the matplotlib savefig method
    extent = axs1[1, 1].get_window_extent().transformed(fig1.dpi_scale_trans.inverted())
    pyplot.savefig(output_filename, bbox_inches=extent, dpi=600)

    if SHOW_DEBUG_FIGURES:
        # plot the current figure
        pyplot.show()

if __name__ == "__main__":
    main()