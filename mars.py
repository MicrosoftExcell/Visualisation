# Import necessary modules
import vtk
import sys
from PIL import Image
import numpy as np

# Get file path from command line parameters
elevation_name = sys.argv[1]
texture_name = sys.argv[2]

# Extract data into array
elevation_image = Image.open(elevation_name)
elevation_data = np.array(elevation_image)

# # Get pixel values of colourmap
# scale = []
# for pixel in elevation_data[2350]:
#     if np.all(pixel != 0):
#         scale.append(list(pixel))

# # Plot colour channels to track colour changes
# import plotly.graph_objects as go

# # Plotting red colour channel
# x = [i for i in range(len(scale))]
# y = [point[0] for point in scale]

# fig = go.Figure(data=go.Scatter(x=x, y=y, mode='lines+markers'))

# fig.show()

# # Plotting green colour channel
# x = [i for i in range(len(scale))]
# y = [point[1] for point in scale]

# fig = go.Figure(data=go.Scatter(x=x, y=y, mode='lines+markers'))

# fig.show()

# # Plotting blue colour channel
# x = [i for i in range(len(scale))]
# y = [point[2] for point in scale]

# fig = go.Figure(data=go.Scatter(x=x, y=y, mode='lines+markers'))

# fig.show()

# Colour channels at each km height (without white bars)
red = [0,123,118,119,118,132,133,165,234,229,233,228,229,214,201,181,172,172,172,185,213,232,255]
green = [0,114,133,167,198,220,214,214,215,185,164,123,137,149,139,143,150,150,155,175,213,233,255]
blue = [0,142,179,204,226,184,131,123,102,91,115,95,141,158,137,124,126,132,146,171,213,233,255]

print("Processing raw data...")

# Find height for each pixel
lowest = -8
highest = 14
heights = []
# Cycling through the rows above the colormap
for i in range(151,2111):
    wrow = []
    erow = []
    if i%50==0:
        print(int(((i-151)/1960)*100),"%")
    western = False
    middle = False
    eastern = False
    # Cycling through pixels in each row
    for pixel in elevation_data[i]:
        # Only evaluate and store relevant pixels
        if sum(pixel) != 0:
            if not western:
                western = True
            elif western and middle and not eastern:
                eastern = True
            bestmatch = 0
            bestscore = sum(pixel)
            # Find difference between pixel and colour value at each km height
            for j in range(1,len(red)):
                score = abs(pixel[0]-red[j])+abs(pixel[1]-green[j])+abs(pixel[2]-blue[j])
                # Find closest match
                if score<bestscore:
                    bestscore = score
                    bestmatch = j
            # Find height for edge cases by interpolating between km heights
            if bestmatch == 0:
                red_dist = pixel[0]/red[1]
                green_dist = pixel[1]/green[1]
                blue_dist = pixel[2]/blue[1]
                average_dist = (red_dist+green_dist+blue_dist)/3
                height = lowest + average_dist
            elif bestmatch == len(red)-1:
                red_dist = (pixel[0]-red[len(red)-2])/(red[len(red)-1]-red[len(red)-2])
                green_dist = (pixel[1]-green[len(green)-2])/(green[len(green)-1]-green[len(green)-2])
                blue_dist = (pixel[2]-blue[len(blue)-2])/(blue[len(blue)-1]-blue[len(blue)-2])
                average_dist = (red_dist+green_dist+blue_dist)/3
                height = highest -1 + average_dist
            else:
                # Compare whether closer to colour of km above or below best match
                lowscore = abs(pixel[0]-red[bestmatch-1])+abs(pixel[1]-green[bestmatch-1])+abs(pixel[2]-blue[bestmatch-1])
                highscore = abs(pixel[0]-red[bestmatch+1])+abs(pixel[1]-green[bestmatch+1])+abs(pixel[2]-blue[bestmatch+1])
                if lowscore<highscore:
                    lower = bestmatch-1
                    higher = bestmatch
                else:
                    lower = bestmatch
                    higher = bestmatch+1
                
                # Calculate distance between closest km and neighbouring km for each colour channel
                red_equal = False
                if red[lower]==red[higher]:
                    red_equal = True
                elif red[lower]<red[higher]:
                    red_dist = (pixel[0]-red[lower])/(red[higher]-red[lower])
                elif red[lower]>red[higher]:
                    red_dist = (red[lower]-pixel[0])/(red[lower]-red[higher])

                # Cap maximum and minimum distance along color channel
                if red_dist>1:
                    red_dist = 1
                elif red_dist<0:
                    red_dist = 0

                green_equal = False
                if green[lower]==green[higher]:
                    green_equal = True
                elif green[lower]<green[higher]:
                    green_dist = (pixel[1]-green[lower])/(green[higher]-green[lower])
                elif green[lower]>green[higher]:
                    green_dist = (green[lower]-pixel[1])/(green[lower]-green[higher])

                if green_dist>1:
                    green_dist = 1
                elif green_dist<0:
                    green_dist = 0

                blue_equal = False
                if blue[lower]==blue[higher]:
                    blue_equal = True
                elif blue[lower]<blue[higher]:
                    blue_dist = (pixel[2]-blue[lower])/(blue[higher]-blue[lower])
                elif blue[lower]>blue[higher]:
                    blue_dist = (blue[lower]-pixel[2])/(blue[lower]-blue[higher])

                if blue_dist>1:
                    blue_dist = 1
                elif blue_dist<0:
                    blue_dist = 0

                # Average distance between km for each colour channel as estimate of height
                average_dist = 0
                count = 0
                if not red_equal:
                    average_dist+=red_dist
                    count+=1
                if not green_equal:
                    average_dist+=green_dist
                    count+=1
                if not blue_equal:
                    average_dist+=blue_dist
                    count+=1
                average_dist = average_dist/count
                if lowscore<highscore:
                    height = lowest + bestmatch -1 + average_dist
                else:
                    height = lowest + bestmatch + average_dist
            height = round(height,5)
            if western and not eastern:
                wrow.append(height)
            elif eastern:
                erow.append(height)
        else:
            if western and not middle:
                middle = True
    heights.append(wrow)
    heights.append(erow)

# create a rendering window and renderer
ren = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)

# create a renderwindowinteractor
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

# create sphere source
source = vtk.vtkSphereSource()
source.SetCenter(0,0,0)
# radius corresponds to number of pixels to make matching easier
source.SetRadius(980)

# make the surface smooth.
source.SetPhiResolution(500)
source.SetThetaResolution(500)

# get the points on the sphere
source.Update()
points = source.GetOutput().GetPoints()

# smooth out worst outliers
for row in heights:
    for i in range(len(row)):
        if row[i]>13:
            if i-1>=0 and i+1<len(row):
                if row[i-1]<10 and row[i+1]<10:
                    row[i] = (row[i-1]+row[i+1])/2
            elif i-1>=0 and row[i-1]<10:
                row[i] = row[i-1]
            elif i+1<len(row) and row[i+1]<10:
                row[i] = row[i+1]

# split heights into different hemispheres
western_heights = []
eastern_heights = []
for i in range(len(heights)):
    if i%2==0:
        western_heights.append(heights[i])
    else:
        eastern_heights.append(heights[i])

# create an array of heights corresponding to points
height_points = vtk.vtkFloatArray()
original_points = []
# cycle through points
for i in range(points.GetNumberOfPoints()):
    point = points.GetPoint(i)
    original_points.append([point[0],point[1],point[2]])
    # calculate the position of the point in the heights array
    z = round(point[2])+980
    # figure out which hemisphere
    if point[1]<0:
        if z>=len(eastern_heights):
            z=len(eastern_heights)-1
        row = eastern_heights[z][::-1]
    else:
        if z>=len(western_heights):
            z=len(western_heights)-1
        row = western_heights[z]
    midpoint = round(len(row)/2)
    x = round(point[0])+midpoint
    if x>=len(row):
        x = len(row)-1
    y = row[x]
    # add height corresponding to point to floatarray
    height_points.InsertNextTuple([y])

# adding scalar height values to sphere dataset
source.GetOutput().GetPointData().SetScalars(height_points)

# function to update elevation based on scale factor
def update_elevation(scale_factor):
    # get the points on the sphere
    for i in range(points.GetNumberOfPoints()):
        # set new point based on scale factor
        point = original_points[i]
        height = height_points.GetValue(i)
        scale = 1+scale_factor*30*(height/14)/980
        points.SetPoint(i,point[0]*scale,point[1]*scale,point[2]*scale)

# setting starting elevation
update_elevation(1)

# load and map texture to sphere
reader = vtk.vtkJPEGReader()
reader.SetFileName(texture_name)
texture = vtk.vtkTexture()
texture.SetInputConnection(reader.GetOutputPort())
texture.SetQualityTo32Bit()
mapping = vtk.vtkTextureMapToSphere()
mapping.SetInputConnection(source.GetOutputPort())
mapping.PreventSeamOff()
transform = vtk.vtkTransformTextureCoords()
transform.SetInputConnection(mapping.GetOutputPort())
transform.SetFlipS(True)

# callback function for slider 
def slider_callback(obj, event):
    slider_looks = obj.GetRepresentation()
    value = slider_looks.GetValue()
    global source
    update_elevation(value)
    points.Modified()
    source.Update()

# Create elevation scale factor slider
slider_looks = vtk.vtkSliderRepresentation2D()
slider_looks.SetMinimumValue(0)
slider_looks.SetMaximumValue(4)
slider_looks.SetValue(1)
slider_looks.SetTitleText('Elevation scale factor')

slider_looks.GetPoint1Coordinate().SetCoordinateSystemToDisplay()
slider_looks.GetPoint1Coordinate().SetValue(200,100)
slider_looks.GetPoint2Coordinate().SetCoordinateSystemToDisplay()
slider_looks.GetPoint2Coordinate().SetValue(550,100)
slider_looks.SetTitleHeight(0.025)
slider_looks.SetLabelHeight(0.02)

slider = vtk.vtkSliderWidget()
slider.SetInteractor(iren)
slider.SetRepresentation(slider_looks)
slider.KeyPressActivationOff()
slider.SetAnimationModeToAnimate()
slider.SetEnabled(True)
slider.AddObserver('InteractionEvent', slider_callback)

# create blue sphere for water
sea = vtk.vtkSphereSource()
sea.SetCenter(0,0,0)
sea.SetRadius(990)

# make the surface smooth.
sea.SetPhiResolution(100)
sea.SetThetaResolution(100)

# mappers
mapper = vtk.vtkDataSetMapper()
mapper.ScalarVisibilityOff()
mapper.SetInputConnection(transform.GetOutputPort())

sea_mapper = vtk.vtkDataSetMapper()
sea_mapper.SetInputConnection(sea.GetOutputPort())

from vtk.util.colors import *

# actors
actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.SetTexture(texture)
actor.RotateX(90)
actor.GetProperty().SetAmbient(0.25)
actor.GetProperty().SetDiffuse(0.8)

sea_actor = vtk.vtkActor()
sea_actor.SetMapper(sea_mapper)
sea_actor.GetProperty().SetColor(cobalt)
sea_actor.GetProperty().SetAmbient(0.25)
sea_actor.GetProperty().SetDiffuse(0.8)

# assign actor to the renderer
ren.AddActor(actor)
ren.AddActor(sea_actor)

renWin.SetSize(750,750)

# enable user interface interactor
iren.Initialize()
renWin.Render()
renWin.SetWindowName("Problem 2")
iren.Start()


# Problem 3

# create a rendering window and renderer
ren2 = vtk.vtkRenderer()
renWin2 = vtk.vtkRenderWindow()
renWin2.AddRenderer(ren2)

# create a renderwindowinteractor
iren2 = vtk.vtkRenderWindowInteractor()
iren2.SetRenderWindow(renWin2)

# create sphere source
source2 = vtk.vtkSphereSource()
source2.SetCenter(0,0,0)
# radius corresponds to number of pixels to make matching easier
source2.SetRadius(980)

# make the surface smooth.
source2.SetPhiResolution(500)
source2.SetThetaResolution(500)

# smooth surface of source for isolines
update_elevation(0)

# create isolines
contours = vtk.vtkContourFilter()
contours.SetInputConnection(source.GetOutputPort())
contours.GenerateValues(23,-8,14)

# wrap isolines into tubes
tubes = vtk.vtkTubeFilter()
tubes.SetInputConnection(contours.GetOutputPort())
tubes.SetRadius(0.5)
tubes.SetVaryRadiusToVaryRadiusOff()
tubes.Update()

# create colour function for isolines
import colorsys
colour_function = vtk.vtkColorTransferFunction()
colour_function.SetColorSpaceToDiverging()
for i in range(-8,0):
    rgb = colorsys.hsv_to_rgb(240/360,-i/8,1)
    colour_function.AddRGBPoint(i,rgb[0],rgb[1],rgb[2])
colour_function.AddRGBPoint(0.0,1.0,0.0,0.0)
for i in range(1,15):
    rgb = colorsys.hsv_to_rgb(60/360,i/14,1)
    colour_function.AddRGBPoint(i,rgb[0],rgb[1],rgb[2])

# map texture and transform for points
mapping2 = vtk.vtkTextureMapToSphere()
mapping2.SetInputConnection(source2.GetOutputPort())
mapping2.PreventSeamOff()
transform2 = vtk.vtkTransformTextureCoords()
transform2.SetInputConnection(mapping2.GetOutputPort())
transform2.SetFlipS(True)

# callback function for slider 
def radius_callback(obj, event):
    slider_rep = obj.GetRepresentation()
    value = slider_rep.GetValue()
    global tubes
    tubes.SetRadius(value)
    tubes.Update()

# Create tube radius slider
slider_rep = vtk.vtkSliderRepresentation2D()
slider_rep.SetMinimumValue(0)
slider_rep.SetMaximumValue(1.0)
slider_rep.SetValue(0.5)
slider_rep.SetTitleText('Tube Radius')

slider_rep.GetPoint1Coordinate().SetCoordinateSystemToDisplay()
slider_rep.GetPoint1Coordinate().SetValue(200,100)
slider_rep.GetPoint2Coordinate().SetCoordinateSystemToDisplay()
slider_rep.GetPoint2Coordinate().SetValue(550,100)
slider_rep.SetTitleHeight(0.025)
slider_rep.SetLabelHeight(0.02)

slider2 = vtk.vtkSliderWidget()
slider2.SetInteractor(iren2)
slider2.SetRepresentation(slider_rep)
slider2.KeyPressActivationOff()
slider2.SetAnimationModeToAnimate()
slider2.SetEnabled(True)
slider2.AddObserver('EndInteractionEvent', radius_callback)

# mapper
mapper2 = vtk.vtkDataSetMapper()
mapper2.SetInputConnection(transform2.GetOutputPort())

tube_mapper = vtk.vtkPolyDataMapper()
tube_mapper.SetInputConnection(tubes.GetOutputPort())
tube_mapper.SetLookupTable(colour_function)

# actors
actor2 = vtk.vtkActor()
actor2.SetMapper(mapper2)
actor2.SetTexture(texture)
actor2.RotateX(90)
actor2.GetProperty().SetAmbient(0.25)
actor2.GetProperty().SetDiffuse(0.8)

tube_actor = vtk.vtkActor()
tube_actor.SetMapper(tube_mapper)
tube_actor.RotateX(90)

# assign actor to the renderer
ren2.AddActor(actor2)
ren2.AddActor(tube_actor)

renWin2.SetSize(750,750)

# enable user interface interactor
iren2.Initialize()
renWin2.Render()
renWin2.SetWindowName("Problem 3")
iren2.Start()