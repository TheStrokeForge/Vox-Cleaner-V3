
#   ██╗░░░██╗░█████╗░██╗░░██╗   ░█████╗░██╗░░░░░███████╗░█████╗░███╗░░██╗███████╗██████╗░    ██╗░░░██╗██████╗░
#   ██║░░░██║██╔══██╗╚██╗██╔╝   ██╔══██╗██║░░░░░██╔════╝██╔══██╗████╗░██║██╔════╝██╔══██╗    ██║░░░██║╚════██╗
#   ╚██╗░██╔╝██║░░██║░╚███╔╝░   ██║░░╚═╝██║░░░░░█████╗░░███████║██╔██╗██║█████╗░░██████╔╝    ╚██╗░██╔╝░░███╔═╝
#   ░╚████╔╝░██║░░██║░██╔██╗░   ██║░░██╗██║░░░░░██╔══╝░░██╔══██║██║╚████║██╔══╝░░██╔══██╗    ░╚████╔╝░░░╚══██╗
#   ░░╚██╔╝░░╚█████╔╝██╔╝╚██╗   ╚█████╔╝███████╗███████╗██║░░██║██║░╚███║███████╗██║░░██║    ░░╚██╔╝░░██████╔╝
#   ░░░╚═╝░░░░╚════╝░╚═╝░░╚═╝   ░╚════╝░╚══════╝╚══════╝╚═╝░░╚═╝╚═╝░░╚══╝╚══════╝╚═╝░░╚═╝    ░░░╚═╝░░░╚═════╝░
#
#                                                    █▄▄ █▄█   █▀▀ ▄▀█ █▀█ █ █ ▄▀█ █▄ █   █▀ █ █ ▄▀█ █ █▄▀ █ █
#                                                    █▄█  █    █▀  █▀█ █▀▄ █▀█ █▀█ █ ▀█   ▄█ █▀█ █▀█ █ █ █ █▀█
#

'''
VoxCleaner © 2024 by Farhan Shaikh is licensed under GPL 3.0 or later. 

License: GPL 3.0 or later
Everyone is permitted to copy and distribute verbatim copies of this license document, but changing it is not allowed. Giving credit to the Creator is appreciated but not required.
Read more about the license: https://spdx.org/licenses/GPL-3.0-or-later.html

Thanks so much for your purchase and please feel free to tag me @TheStrokeForge on Instagram/Twitter & I’d love to see your work! Cheers!

''' 

import os, sys, subprocess

import math
import numpy as np
import struct
from decimal import Context
from logging import error, exception

import bpy
import bmesh
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, CollectionProperty, EnumProperty
from bpy.types import Operator
from mathutils import Matrix

import webbrowser

class FlowData:
    ModelType = None
    MainObj = 0
    MainObjName = None
    DupeObj = 0
    DupeObjName = None
    ObjArray = None
    CommonUVObjects = []
    CommonUVDupeObjects = []
    CommonUVOrigins = {}

    VertexCountInitialX = 0
    VertexCountFinalX = 0

    SmallestEdge = None
    SmallestEdgeLength = 10000000.0

    LargestEdge = None
    LargestEdgeLength = 0.0
    LargestEdgeBlocks = 0
    LargestUVEdgeLengthInPixels = 0.0
    ResizeFactor = 0.0

    ApproxLen = 0.0
    AutoRes = 0
    FinalTextureSize = 0.0
    Bleed = 0.0

    MaterialMaps = []
    GeneratedTex_Active = None
    BakeList = []
    
    GeneratedTex_Color = None
    GeneratedTex_Roughness = None
    GeneratedTex_Metallic = None
    GeneratedTex_Emisson = None
    GeneratedTex_Transmission = None
    
    BakeTimes = 0
    CleanTimes = 0
    CleanType = None
    TwoStepCommonUV = False
    ProcessRunning = False
    MissingActors = False

    ImportNameIndex = 0
 

class StaticData:
    #Default Numbers ----------------------------------------
    StandardBakeResolutions = [8,16,32,64,128,256,512,1024,2048,4096,8192]
    TriangulateLoops = 8
    
    #Default Preferences ---------------------------------------
    # Importer
    RoughnessDefault = 0.5   # default roughness for diffuse materials
    
    # Cleaner
    ResolutionDefault = "Mini"
    UpscalingDefault = "1"
    UVMethodDefault = "cube"
    RotateUVDefault = False
    MCNVResDefault = "1024"
    NVDecimationDefault = 70

    BaseColorDefault = (0.6,0.0,0.2,1.0)
    AlphaDefault = False
    EmitStrengthDefault = 8.0

    ModelBackupDefault = True
    OrganiseDefault = True  # Organise model backups

    # Exporter
    TriangulateDefault = True

    #UI Data --------------------------------------------------
    BigButtonHeight = 1.5
    ButtonHeightMedium = 1.2
    CleanModePaneHeight = 1

    RowSpacing = 1

    SeperatorSpacing1 = 0.5
    SeperatorSpacing2 = 0.2
    SeperatorSpacing3 = 0.1
    SeperatorSpacing4 = 0.05

    VerticalSplitFactor = 0.5


class VoxProperties(bpy.types.PropertyGroup):
    # Clean related ###########################################################################################################################################################################################################################
    BaseColor : bpy.props.FloatVectorProperty(name='',subtype='COLOR_GAMMA',size=4, min=0.0, max=1.0, precision=4, default = StaticData.BaseColorDefault, description="""Base color of the generated image.
Set this to white before cleaning, if you wish to pixel texture paint on the model!

Ps, This color won't be visible on the final cleaned model, is just for easier visibility""") # type: ignore
    
    ResolutionSet : bpy.props.EnumProperty(
        name = "",default = StaticData.ResolutionDefault,
        items = [("Stan", "8,16,32,64,128...", "The Set of Standard image sizes like [8,16,32,64,128,256...]"),
                 ("Mini", "Smallest Possible", "The smallest image size possible, not following any set.")],
        description="""Resolution Set for Voxel Models.
"Smallest Possible" option for the smallest possible resolutions.
"8,16,32,64..." option for industry standard resolutions.

Selected Resolution Set""") # type: ignore
    
    #Scale multiplier for the baked texture
    TextureScaleMultiplier : bpy.props.EnumProperty(
        name = "",default= StaticData.UpscalingDefault,
        items = [("1", "1x", "", 0),
                 ("2", "2x", "", 2),
                 ("4", "4x", "", 4),
                 ("8", "8x", "", 8),
                 ("16", "16x", "", 16),
                 ("32", "32x", "", 32),
                 ("64", "64x", "", 64),],
        description="""Texture uspcaling for Voxel Models. 
More upscaling takes more time to clean. 

Current upscaling""") # type: ignore
    
    MCNVResolution : bpy.props.EnumProperty(
        name = "",default= StaticData.MCNVResDefault,
        items = [("64", "64 px", "", 1),
                 ("128", "128 px", "", 2),
                 ("256", "256 px", "", 3),
                 ("512", "512 px", "", 4),
                 ("1024", "1024 px", "", 5),
                 ("2048", "2048 px", "", 6),
                 ("4096", "4096 px", "", 7),
                 ("8192", "8192 px", "", 8)],
        description="""Texture Resolution for MC & Non-Voxel models. 
        
Selected Resolution""") # type: ignore
    
    CleanMode : bpy.props.EnumProperty(
        items = [("ez", "Lazy Clean", "Used for fast, one-click cleaning. Cleaned models have automatic Pixel-Perfect UVs", 1),
                 ("hard", "2-Step Clean", "Used on a single object for detail oriented cleaning. Allows you to have control over aspects like custom UVs.", 2),],
        description="""Mode of Cleaning.
● Use lazy clean for fast, one-click cleaning.
● Use 2-Step clean for more controlled cleaning like custom UVs.

Mode of cleaning you're hovering on""",default = "ez") # type: ignore
    
    UVMethod : bpy.props.EnumProperty(name = "",
        items = [("cube", "Cube (Recommended)", "The standard method for voxel UV projection. Might give some errors in very small models (15 voxels or less)", 1),
                 ("smart", "Smart", "Works better on small models when Cube projection fails", 2),],
        description="""UV Projection method used for Voxel models.
        
Choose 'Smart' ONLY when a model is showing errors with the Cube method. The 'Smart' method doesn't work very well on bigger models.

Usually such errors(like Overlapping UVs) are present only in pretty small models, making it a good place to try out the 'Smart' projection method!

UV Projection method you're hovering on""",default = "cube") # type: ignore
    
    NVDecimation : bpy.props.FloatProperty(name="", default=StaticData.NVDecimationDefault, subtype="PERCENTAGE",min=0.0, max=100.0, description="""Vertex Reduction Percentage for Non-Voxel Models.
More will result in more cleaning""") # type: ignore

    AlphaBool: bpy.props.BoolProperty(name="", default = False, description="Should the generated image have alpha?") # type: ignore
    
    CleanGeo: bpy.props.BoolProperty(name="Clean Geometry", default = True, description="""Clean Geometry while cleaning. 
Disable if you wish to preserve the geometry for better mesh flexing""") # type: ignore
    
    BakeTex: bpy.props.BoolProperty(name="Apply Texture", default = True, description="""Generate & bake textures while cleaning. 
Disable if you don't want textures or a material on your model""") # type: ignore
    
    CommonUV: bpy.props.BoolProperty(name="Shared UVs", default = False, description="""Shared UV Cleaning.
Enabling this will make all the selected models have a shared UV map layout after cleaning. Helpful if you want to have multiple objects having the same texture. 

E.g., You can use this option for a character with multiple parts. This way you'll have one texture for the entire character instead of having one texture for all of it's individual parts""") # type: ignore
    
    RotateUV: bpy.props.BoolProperty(name="", default = False, description="""Enables cardinal rotations of UV islands. 
Disabling will not rotate the UV islands
                                     
Affects only Voxel models""") # type: ignore

    EmitStrength : bpy.props.FloatProperty(name="", default=StaticData.EmitStrengthDefault,min=0.0, max=100.0, description="""Default emission strength if emission is enabled.
This can be tweaked later in the shader nodes""") # type: ignore

    CreateBackup: bpy.props.BoolProperty(name="Create model backup", default = StaticData.ModelBackupDefault, description="Enabling preserves a version of the original model in the scene") # type: ignore

    OrganiseBackups: bpy.props.BoolProperty(name="Organise backups into Collections", default = StaticData.ModelBackupDefault, description="""Enabling will organise your backups in a Blender collection 
called 'Vox Cleaner Backups', not cluttering your Blender outliner""") # type: ignore
    

    #Export related ######################################################################################################################################################################################################################################################
    ExportLocation : bpy.props.StringProperty(name="",default = "", description="Directory where your objects will be exported", subtype="DIR_PATH") # type: ignore

    TriangulatedExport: bpy.props.BoolProperty(name="Export Triangulated model", default = StaticData.TriangulateDefault, description="Enabling triangulates the model before exporting. (Enabling is highly recommended)") # type: ignore
    
    
    
    ExportColor: bpy.props.BoolProperty(name="Color (C)", description="""Export color texture if available""", default = True) # type: ignore
    ExportRoughness: bpy.props.BoolProperty(name="Roughness (R)", description="""Export roughness texture if available""", default = True) # type: ignore
    ExportMetallic: bpy.props.BoolProperty(name="Metallic (M)", description="""Export metallic texture if available""", default = True) # type: ignore
    ExportEmission: bpy.props.BoolProperty(name="Emission (E)", description="""Export emission mask texture if available""", default = True) # type: ignore
    ExportTransmission: bpy.props.BoolProperty(name="Transmission (T)", description="""Export transparency mask texture if available""", default = True) # type: ignore
    

    # Import related #########################################################################################################################################################
    Organize: bpy.props.BoolProperty(name = "Organize into Collections", description = "Organize imported objects into collections based on their Vox file names", default = False) # type: ignore
    
    ImportHidden: bpy.props.BoolProperty(name = "Also import hidden objects", description = "Import hidden objects in the Vox file as well",default = True) # type: ignore
    
    OriginsAtBottom: bpy.props.BoolProperty(name = "Origins at bottom",description = "Set model origins at it's bottom-center. Disable to set origins in the center instead",default = True) # type: ignore

    MaxMaps: bpy.props.BoolProperty(name = "Max-out Material Properties",description = '''Materials Maps like Transmission, Emission etc perform much better in Blender if their values are set to 1 in MagicaVoxel.This checkbox does that automatically for you, saving you effort of going back and editing every material property in Magicavoxel.

Recommended for Materials containing Map Values like 0.1.

Affects: Emission & Transmission values''',default = False) # type: ignore
    
    ImportColor: bpy.props.BoolProperty(name="Color (C)", description="""Import color map""", default = True) # type: ignore
    ImportRoughness: bpy.props.BoolProperty(name="Roughness (R)", description="""Import roughness map""", default = True) # type: ignore
    ImportMetallic: bpy.props.BoolProperty(name="Metallic (M)", description="""Import metallic map""", default = True) # type: ignore
    ImportEmission: bpy.props.BoolProperty(name="Emission (E)", description="""Import emission map""", default = True) # type: ignore
    ImportTransmission: bpy.props.BoolProperty(name="Transmission (T)", description="""Import transparency map""", default = True) # type: ignore
    
class Vec3:
    def __init__(self, X, Y, Z):
        self.x, self.y, self.z = X, Y, Z
    
    def _index(self):
        return self.x + self.y*256 + self.z*256*256

class VoxelObject:
    def __init__(self, Voxels, Size):
        self.size = Size
        self.voxels = {}
        self.used_colors = []
        self.position = Vec3(0, 0, 0)
        self.rotation = Vec3(0, 0, 0)
        
        for vox in Voxels:
            #              x       y       z
            pos = Vec3(vox[0], vox[1], vox[2])
            self.voxels[pos._index()] = (pos, vox[3])
            
            if vox[3] not in self.used_colors:
                self.used_colors.append(vox[3])
            
    
    def getVox(self, pos):
        key = pos._index()
        if key in self.voxels:
            return self.voxels[key][1]
        
        return 0
    
    def compareVox(self, colA, b):
        colB = self.getVox(b)
        
        if colB == 0:
            return False
        return True
    
    
    def generate(self, file_name, palette, materials, collections,TransformMatrix4x4):
        objects = []
        
        mytool = bpy.context.scene.vox_tool

        self.materials = materials  # For helper functions.
        
        mesh_col = collections
        
        if len(self.used_colors) == 0: # Empty Object
            return
        
        for Col in self.used_colors: # Create an object for each color and then join them.
            
            mesh = bpy.data.meshes.new(file_name) # Create mesh
            obj = bpy.data.objects.new(file_name, mesh) # Create object
            
            
            # Link Object to Scene
            if mesh_col == None:
                bpy.context.scene.collection.objects.link(obj)
            else:
                mesh_col.objects.link(obj)
            
            objects.append(obj) # Keeps track of created objects for joining.
            
            verts = []
            faces = []
            
            for key in self.voxels:
                pos, colID = self.voxels[key]
                x, y, z = pos.x, pos.y, pos.z
                
                if colID != Col:
                    continue
                
    
                            
                if not self.compareVox(colID, Vec3(x+1, y, z)):
                    verts.append( (x+1, y, z) )
                    verts.append( (x+1, y+1, z) )
                    verts.append( (x+1, y+1, z+1) )
                    verts.append( (x+1, y, z+1) )
                    
                    faces.append( [len(verts)-4,
                                    len(verts)-3,
                                    len(verts)-2,
                                    len(verts)-1] )
                
                if not self.compareVox(colID, Vec3(x, y+1, z)):
                    verts.append( (x+1, y+1, z) )
                    verts.append( (x+1, y+1, z+1) )
                    verts.append( (x, y+1, z+1) )
                    verts.append( (x, y+1, z) )
                    
                    faces.append( [len(verts)-4,
                                    len(verts)-3,
                                    len(verts)-2,
                                    len(verts)-1] )
                
                if not self.compareVox(colID, Vec3(x, y, z+1)):
                    verts.append( (x, y, z+1) )
                    verts.append( (x, y+1, z+1) )
                    verts.append( (x+1, y+1, z+1) )
                    verts.append( (x+1, y, z+1) )
                    
                    faces.append( [len(verts)-4,
                                    len(verts)-3,
                                    len(verts)-2,
                                    len(verts)-1] )
                
                if not self.compareVox(colID, Vec3(x-1, y, z)):
                    verts.append( (x, y, z) )
                    verts.append( (x, y+1, z) )
                    verts.append( (x, y+1, z+1) )
                    verts.append( (x, y, z+1) )
                    
                    faces.append( [len(verts)-4,
                                    len(verts)-3,
                                    len(verts)-2,
                                    len(verts)-1] )
                
                if not self.compareVox(colID, Vec3(x, y-1, z)):
                    verts.append( (x, y, z) )
                    verts.append( (x, y, z+1) )
                    verts.append( (x+1, y, z+1) )
                    verts.append( (x+1, y, z) )
                    
                    faces.append( [len(verts)-4,
                                    len(verts)-3,
                                    len(verts)-2,
                                    len(verts)-1] )
                
                if not self.compareVox(colID, Vec3(x, y, z-1)):
                    verts.append( (x, y, z) )
                    verts.append( (x+1, y, z) )
                    verts.append( (x+1, y+1, z) )
                    verts.append( (x, y+1, z) )
                    
                    faces.append( [len(verts)-4,
                                    len(verts)-3,
                                    len(verts)-2,
                                    len(verts)-1] )
                                        
            mesh.from_pydata(verts, [], faces)
            
            # Add materials
            if ImportVox.VMaterial == "NoMatNeeded" or ImportVox.VMaterial == None: pass
            else: obj.data.materials.append(ImportVox.VMaterial)

            
            # Create Vertex Colors & add data
            bpy.context.view_layer.objects.active = obj

            # Add color attributes for all selected maps, and also make variables for em
            if mytool.ImportColor:
                bpy.ops.geometry.color_attribute_add(name = "Color", domain='CORNER', data_type='BYTE_COLOR')
                ColorLayer = mesh.vertex_colors["Color"]
                i = 0
                for poly in mesh.polygons:
                    for idx in poly.loop_indices:
                        ColorLayer.data[i].color = palette[Col-1]
                        i+=1 

            if mytool.ImportRoughness:
                bpy.ops.geometry.color_attribute_add(name = "Roughness", domain='CORNER', data_type='BYTE_COLOR')
                RoughnessLayer = mesh.vertex_colors["Roughness"]
                i = 0
                for poly in mesh.polygons:
                    for idx in poly.loop_indices:
                        RoughnessLayer.data[i].color = [materials[Col-1][0], materials[Col-1][0], materials[Col-1][0], 1]
                        i+=1 

            if mytool.ImportMetallic:
                bpy.ops.geometry.color_attribute_add(name = "Metallic", domain='CORNER', data_type='BYTE_COLOR')
                MetallicLayer = mesh.vertex_colors["Metallic"]
                i = 0
                for poly in mesh.polygons:
                    for idx in poly.loop_indices:
                        MetallicLayer.data[i].color = [materials[Col-1][1], materials[Col-1][1], materials[Col-1][1], 1]
                        i+=1 

            if mytool.ImportEmission:
                bpy.ops.geometry.color_attribute_add(name = "Emission", domain='CORNER', data_type='BYTE_COLOR')
                EmissionLayer = mesh.vertex_colors["Emission"]
                i = 0
                for poly in mesh.polygons:
                    for idx in poly.loop_indices:
                        EmissionLayer.data[i].color = [materials[Col-1][2], materials[Col-1][2], materials[Col-1][2], 1]
                        i+=1 

            if mytool.ImportTransmission:
                bpy.ops.geometry.color_attribute_add(name = "Transmission", domain='CORNER', data_type='BYTE_COLOR')
                TransmissionLayer = mesh.vertex_colors["Transmission"]
                i = 0
                for poly in mesh.polygons:
                    for idx in poly.loop_indices:
                        TransmissionLayer.data[i].color = [materials[Col-1][3], materials[Col-1][3], materials[Col-1][3], 1]
                        i+=1
            '''
            if mytool.ImportSubSurface:
                bpy.ops.geometry.color_attribute_add(name = "SubSurface", domain='CORNER', data_type='BYTE_COLOR')
                SSSLayer = mesh.vertex_colors["SubSurface"]
                i = 0
                for poly in mesh.polygons:
                    for idx in poly.loop_indices:
                        SSSLayer.data[i].color = [materials[Col-1][4], materials[Col-1][4], materials[Col-1][4], 1]
                        i+=1
'''
            

        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True) # Select all objects that were generated.
        
        obj = objects[0]
        bpy.context.view_layer.objects.active = obj # Make the first one active.
        bpy.ops.object.join() # Join selected objects.
        
        # Sets the origin of object to be the same as in MagicaVoxel so that its location can be set correctly.
        bpy.context.scene.cursor.location = [0, 0, 0]
        obj.location = [int(-self.size.x/2), int(-self.size.y/2), int(-self.size.z/2)]
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        
        # Set scale, position & rotation.

        # Rescale value
        RescaleValue = 0.1

        TransformMatrix4x4[0][3] = TransformMatrix4x4[0][3]*RescaleValue
        TransformMatrix4x4[1][3] = TransformMatrix4x4[1][3]*RescaleValue
        TransformMatrix4x4[2][3] = TransformMatrix4x4[2][3]*RescaleValue
        
        obj.matrix_world = TransformMatrix4x4

        bpy.ops.transform.resize(value=(RescaleValue, RescaleValue, RescaleValue))
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        

        # Remove Doubles & fix normals
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode = 'OBJECT')

        #Origin to Bottom, if specified
        if mytool.OriginsAtBottom:
            
            def Find_Min_Max_Verts(obj):
                bpy.ops.mesh.reveal()
                bm = bmesh.from_edit_mesh(obj.data)
                bm.verts.ensure_lookup_table()
                
                if len(bm.verts) == 0: result = None
                else:
                    min_co = (obj.matrix_world @ bm.verts[0].co)[2]
                    for v in bm.verts:
                        if (obj.matrix_world @ v.co)[2] < min_co:
                            min_co = (obj.matrix_world @ v.co)[2]
                return min_co	

            # Save selected objects and current position of 3D Cursor
            SelectedObjs = bpy.context.selected_objects
            ActiveObj = bpy.context.active_object
            CursorLoc = bpy.context.scene.cursor.location.copy()

            bpy.ops.object.mode_set(mode = 'OBJECT')

            # Set origins to bottom
            for Obj in SelectedObjs:
                # Select only current object (for setting origin)
                bpy.ops.object.select_all(action='DESELECT')
                Obj.select_set(True);
                bpy.context.view_layer.objects.active = Obj
                # Save current origin and relocate 3D Cursor
                OriginLoc = Obj.location.copy() 
                if Obj.type == 'MESH':
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    min_co = Find_Min_Max_Verts(Obj)
                    if min_co == None:
                        min_co = OriginLoc[2]
                    
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    bpy.context.scene.cursor.location = [OriginLoc[0], OriginLoc[1], min_co]
                    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
                    
                    # Reset 3D Cursor  
                    bpy.context.scene.cursor.location = CursorLoc
                    
            # Select objects again
            for Obj in SelectedObjs:
                Obj.select_set(True);
                
            bpy.context.view_layer.objects.active = ActiveObj


class ImportVox(Operator, ImportHelper):
    
    """Import a VOX file with the selected settings"""
    bl_idname = "voxcleaner.importvox"
    bl_label = "Import Vox Files"
    bl_options = {'UNDO'}

    MaterialName = None
    VMaterial = None

    files: CollectionProperty(name="File Path", description="File path used for importing the VOX file", type=bpy.types.OperatorFileListElement) # type: ignore

    directory: StringProperty() # type: ignore
    
    filename_ext = ".vox"
    filter_glob: StringProperty(default="*.vox",options={'HIDDEN'},) # type: ignore
    

    def execute(self, context):
        paths = [os.path.join(self.directory, name.name) for name in self.files]
        #print("Firstline whtvr",paths)

        if not paths:
            paths.append(self.filepath)
            print("SELF.fp",paths)
        
        def read_chunk(buffer):
            *name, h_size, h_children = struct.unpack('<4cii', buffer.read(12))
            name = b"".join(name)
            content = bytearray(buffer.read(h_size))
            return name, content

        def read_content(content, size):
            out = content[:size]
            del content[:size]
            
            return out

        def read_dict(content):
            dict = {}
            
            dict_size, = struct.unpack('<i', read_content(content, 4))
            for _ in range(dict_size):
                key_bytes, = struct.unpack('<i', read_content(content, 4))
                key = struct.unpack('<'+str(key_bytes)+'c', read_content(content, key_bytes))
                key = b"".join(key)
                
                value_bytes, = struct.unpack('<i', read_content(content, 4))
                value = struct.unpack('<'+str(value_bytes)+'c', read_content(content, value_bytes))
                value = b"".join(value)
                
                dict[key] = value
            
            return dict

        def import_vox(path):
            
            mytool = bpy.context.scene.vox_tool

            def IntTo3x3Matrix(rotation):

                RotMatrix = Matrix( ((0, 0, 0),
                                    (0, 0, 0),
                                    (0, 0, 0)) )

                # Get indices of first, second and third=
                first_index = rotation & 0b0011
                second_index = (rotation & 0b1100) >> 2
                array = [-1, -1, -1]
                index = 0

                array[first_index] = 0
                array[second_index] = 0

                for i in range(len(array)):
                    if array[i] == -1:
                        index = i
                        break

                third_index = index

                # Get negatives
                negative_first = ((rotation & 0b0010000) >> 4) == 1
                negative_second = ((rotation & 0b0100000) >> 5) == 1
                negative_third = ((rotation & 0b1000000) >> 6) == 1

                print("rotation", rotation)
                print("NEGATIVES", negative_first, negative_second, negative_third)

                '''
                for row in matrix.elements:
                    print(' '.join(map(str, row)))
                '''
                RotMatrix[0][first_index] = -1 if negative_first else 1
                RotMatrix[1][second_index] = -1 if negative_second else 1
                RotMatrix[2][third_index] = -1 if negative_third else 1
                
                print("Matrix", RotMatrix)

                return RotMatrix
            
            with open(path, 'rb') as file:
                file_name = os.path.basename(file.name).replace('.vox', '')
                file_size = os.path.getsize(path)

                palette = []
                materials = [[0.0, 0.0, 0.0, 0.0] for _ in range(255)] # [roughness, metallic, emission, glass] * 255
                
                # Makes sure it's supported vox file
                VoxFileVersionData = struct.unpack('<4ci', file.read(8))

                try: assert (VoxFileVersionData == (b'V', b'O', b'X', b' ', 200))
                except AssertionError as AE:
                    print(AE, "Vox File Version", VoxFileVersionData)
                    stmt = "Older Magicavoxel Files like '"+file_name+".vox' are not supported. Please update your Magicavoxel & try again with newer files."
                    self.report({'WARNING'}, stmt)
                    
                    return {'CANCELLED'}

                
                # MAIN chunk
                assert (struct.unpack('<4c', file.read(4)) == (b'M', b'A', b'I', b'N'))
                N, M = struct.unpack('<ii', file.read(8))
                assert (N == 0)
                

                # Nested dictionaries with all the properties.

                LayerIDs = {}      # [lID][Name] = "name", Visible = 1/0]
                TransformIDs = {}  # [tID][ChildID = sID/gID, Name = "name", Visible = 0/1, "Transform" = TransformMatrix4x4]
                GroupIDs = {}      # [gID] = tIDs
                ShapeIDs = {}      # [sID] = mIDs
                ModelIDs = {}      # [mID] = Model ie VoxelObject
                mID = 0
                

                ### Parse File ###
                while file.tell() < file_size:
                    name, content = read_chunk(file)

                    
                    if name == b'SIZE': # Size of object.
                        x, y, z = struct.unpack('<3i', read_content(content, 12))
                        size = Vec3(x, y, z)
                    
                    elif name == b'XYZI': # Location and color id of voxel.
                        voxels = []
                        
                        num_voxels, = struct.unpack('<i', read_content(content, 4))
                        for voxel in range(num_voxels):
                            voxel_data = struct.unpack('<4B', read_content(content, 4))
                            voxels.append(voxel_data)
                        
                        model = VoxelObject(voxels, size)
                        ModelIDs[mID] = model
                        #print("ModelID",mod_id)
                        #ModelData[mod_id] = {}
                        mID += 1
                        #print("read XYZI #########################################")
                    
                    elif name == b'LAYR':
                        lID, = struct.unpack('<i', read_content(content, 4))
                        if lID > 255: continue # Why are there material values for id 256?
                        LayerIDs[lID] = {}
                        
                        LayerInfo = read_dict(content)

                        if b'_hidden' in LayerInfo:
                            LayerIDs[lID]["Visible"] = 0
                        else:
                            LayerIDs[lID]["Visible"] = 1

                        if b'_name' in LayerInfo:
                            LayerIDs[lID]["Name"] = LayerInfo[b'_name'].decode('utf-8')
                        else:
                            LayerIDs[lID]["Name"] = "NoName"+str(lID)
                            
                    elif name == b'nTRN': # Position and rotation of object.
                        tID, = struct.unpack('<i', read_content(content, 4))
                        TransformIDs[tID] = {}
                        TransformNodeAttributes = read_dict(content)

                        # initialise transform matrix
                        TransformIDs[tID]["Transform"] = Matrix( ((1, 0, 0, 0),(0, 1, 0, 0),(0, 0, 1, 0),(0, 0, 0, 1)) )

                        if b'_name' in TransformNodeAttributes:
                            TransformIDs[tID]["Name"] = TransformNodeAttributes[b'_name'].decode('utf-8')
                        else: TransformIDs[tID]["Name"] = "XYZ"

                        if b'_hidden' in TransformNodeAttributes:
                            TransformIDs[tID]["Visible"] = 0
                        else: TransformIDs[tID]["Visible"] = 1
                        
                        ChildID, ResID, = struct.unpack('<2i', read_content(content, 8))
                        TransformIDs[tID]["ChildID"] = ChildID
                        #TransformChildRelations[id] = [child_id]
                        
                        LayerID, = struct.unpack('<i', read_content(content, 4))
                        TransformIDs[tID]["lID"] = LayerID

                        FrameCount, = struct.unpack('<i', read_content(content, 4))

                        #Apply Translation & Rotation
                        frames = read_dict(content)

                        # position
                        if b'_t' in frames:
                            value = frames[b'_t'].decode('utf-8').split()
                            #Pos = np.array([int(value[0]), int(value[1]), int(value[2])])

                            TransformIDs[tID]["Transform"][0][3] = int(value[0])
                            TransformIDs[tID]["Transform"][1][3] = int(value[1])
                            TransformIDs[tID]["Transform"][2][3] = int(value[2])


                        # Rotation
                        if b'_r' in frames:
                            value = frames[b'_r']
                            RotMatrix3x3 = IntTo3x3Matrix(int(value))

                            for i in range(3):
                                TransformIDs[tID]["Transform"][i][0] = RotMatrix3x3[i][0]
                                TransformIDs[tID]["Transform"][i][1] = RotMatrix3x3[i][1]
                                TransformIDs[tID]["Transform"][i][2] = RotMatrix3x3[i][2]
                            
                            #Rot = Vec3(int(x), int(y), int(z))
                        #TransformIDs[tID]["Rotation"] = RotMatrix4x4
                    
                    elif name == b'nGRP':
                        gID, = struct.unpack('<i', read_content(content, 4))
                        GroupIDs[gID] = {}
                        GroupAttributes = read_dict(content)

                        NoOf_tIDs, = struct.unpack('<i', read_content(content, 4))
                        Child_tIDs = []
                        
                        for k in range(NoOf_tIDs):
                            Child_tIDs.append(struct.unpack('<i', read_content(content, 4))[0])
                        
                        GroupIDs[gID] = Child_tIDs
                    
                    elif name == b'nSHP':
                        sID, = struct.unpack('<i', read_content(content, 4))
                        ShapeIDs[sID] = {}
                        
                        ShpAttributes = read_dict(content)
                        
                        NoOf_mIDs, = struct.unpack('<i', read_content(content, 4))
                        Connected_mIDs = []
                        
                        for k in range(NoOf_mIDs):
                            Connected_mIDs.append(struct.unpack('<i', read_content(content, 4))[0])
                        
                        ShapeIDs[sID] = Connected_mIDs

                    elif name == b'RGBA':
                        for _ in range(255):
                            rgba = struct.unpack('<4B', read_content(content, 4))
                            palette.append([float(col)/255 for col in rgba])
                        del content[:4] # Contains a 256th color for some reason.
                    
                    elif name == b'MATL':
                        id, = struct.unpack('<i', read_content(content, 4))
                        if id > 255: continue # Why are there material values for id 256?
                        
                        mat_dict = read_dict(content)
                        
                        type = None
                        TypeDecided = False
                        SubSurfaceType = False
                        #OgId = -1000

                        for key in mat_dict:
                            value = mat_dict[key]
                            
                            #Fix on a type of material
                            if TypeDecided== False:
                                if key == b'_type':
                                    # if type of material is from metal, glass, emit or blend, set type to it
                                    if value == b'_metal' or value == b'_emit' or value == b'_glass' or value == b'_blend': 
                                        type = value
                                        TypeDecided = True
                                    else:
                                        type = b'_diffuse'
                                        TypeDecided = True
                                    
                                else:
                                    materials[id-1][0] = float(StaticData.RoughnessDefault) #default roughness value
                                    TypeDecided = True

                            # then assign different properties based on the type of the material, if type is decided
                            if TypeDecided == True:
                                    
                                # Metal type material
                                if type == b'_metal':

                                    if key == b'_rough':
                                        materials[id-1][0] = float(value) # Roughness
                                    if key == b'_metal':
                                        materials[id-1][1] = float(value) # Metalic
                                        
                                    
                                # Glass type material
                                elif type == b'_glass':
                                    if key == b'_rough':
                                        materials[id-1][0] = float(value) # Roughness

                                    if key == b'_media_type':
                                        if value == b'_sss': SubSurfaceType = True
                                        else: SubSurfaceType = False

                                    if key == b'_alpha':
                                        k = 1 if mytool.MaxMaps == True else float(value)
                                        if SubSurfaceType == False:
                                            materials[id-1][3] = k # Glass
                                        
                                    
                                    '''
                                    Glass Keys b'_type' b'_glass'
                                    Glass Keys b'_media_type' b'_sss'
                                    Glass Keys b'_media' b'3'
                                    Glass Keys b'_alpha' b'0.912209'
                                    Glass Keys b'_trans' b'0.912209'
                                    Glass Keys b'_rough' b'0.800245'
                                    Glass Keys b'_ior' b'0.3'
                                    Glass Keys b'_ri' b'1.3'
                                    Glass Keys b'_g' b'0.47'
                                    Glass Keys b'_d' b'0.017936'
                                    '''


                                # Emission type material
                                elif type == b'_emit':
                                    
                                    if key == b'_rough':
                                        materials[id-1][0] = float(value) # Roughness                                
                                    
                                    if key == b'_emit':
                                        k = 1 if mytool.MaxMaps == True else float(value)
                                        materials[id-1][2] = k # Emission value only
                                        
                                    if key == b'_flux':
                                        P = float(value)
                                        
                                    
                                # Blend type material
                                elif type == b'_blend':
                                    if key == b'_rough':
                                        materials[id-1][0] = float(value) # Roughness                                
                                    if key == b'_metal':
                                        materials[id-1][1] = float(value) # Metalic
                                    if key == b'_media_type':
                                        if value == b'_sss':
                                            SubSurfaceType = True
                                        else:
                                            SubSurfaceType = False

                                    if key == b'_alpha':
                                        k = 1 if mytool.MaxMaps == True else float(value)
                                        if SubSurfaceType == False:
                                            materials[id-1][3] = k # Glass

            # Post process the acquired data
            for tID in TransformIDs:
                if tID == 0:
                    TransformIDs[tID]["Name"] = "ROOT"
                if TransformIDs[tID]["lID"] != -1:
                    TransformIDs[tID]["OverallVisibility"] = LayerIDs[TransformIDs[tID]["lID"]]["Visible"] and TransformIDs[tID]["Visible"]
                else:
                    TransformIDs[tID]["OverallVisibility"] = 1
                if TransformIDs[tID]["ChildID"] in GroupIDs:
                    TransformIDs[tID]["Type"] = "Group"
                if TransformIDs[tID]["ChildID"] in ShapeIDs:
                    TransformIDs[tID]["Type"] = "Shape"

                
                        
            # get a material made from the parameters provided
            if any([mytool.ImportColor, mytool.ImportRoughness, mytool.ImportMetallic, mytool.ImportEmission, mytool.ImportTransmission]) == False: ImportVox.VMaterial = "NoMatNeeded"
            else: ImportVox.VMaterial = VoxMethods.CreateCRMETS(context, mytool.ImportColor, mytool.ImportRoughness, mytool.ImportMetallic, mytool.ImportEmission, mytool.ImportTransmission)
                
            # Create Collections
            collections = (None)
            if mytool.Organize:
                FileCollection = bpy.data.collections.new(file_name)
                bpy.context.scene.collection.children.link(FileCollection)
                
                collections = FileCollection
            
            # TransformIDs[tID] = {"Name":name, "Visible":0/1, "lID":lID, "Transform":TransformMatrix4x, "ChildID":sID/gID}
            # Defining the traverse function
            def Traverse(tID, visible, TransformMatrix):
                if TransformIDs[tID]["Type"] == "Group":
                    if visible == True or mytool.ImportHidden == True: 
                        for child in GroupIDs[TransformIDs[tID]["ChildID"]]:
                            Traverse(child, visible and TransformIDs[child]["OverallVisibility"], TransformMatrix @ TransformIDs[child]["Transform"])

                else:
                    #generate model
                    if visible == True or mytool.ImportHidden == True:
                        #print(tID, TransformIDs[tID]["Name"], visible, pos)
                        CurrentName = None
                        # check if the name in the id is not XYZ
                        if TransformIDs[tID]["Name"] != "XYZ":
                            CurrentName = TransformIDs[tID]["Name"]
                        else:
                            FlowData.ImportNameIndex += 1
                            CurrentName = file_name + "_" + str(FlowData.ImportNameIndex)
                        
                        # stuff to be intersected with the group attributes - Hidden, Pos, Rot
                        ModelIDs[ShapeIDs[TransformIDs[tID]["ChildID"]][0]].generate(CurrentName, palette, materials, collections, TransformMatrix)
            
            # finally generating the models using traverse
            Traverse(0, TransformIDs[0]["OverallVisibility"], TransformIDs[0]["Transform"])

            # Print out the Import Summary in the console!
            print("\n")

            Visible = "●"
            Hidden = "○"

            print('''● IMPORT DATA''')
            print('''———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————''')
            print("  File     (","Name: "+str(file_name)+".vox )"+"                        Legend   (●: Visible , ○: Hidden)")
            print("\n")
            print("  Layers —————————————————————————————————————————————")

            Rows = 10

            Columns = math.ceil(len(LayerIDs)/Rows)

            for key in range(0,Rows):
                for i in range(0,Columns):
                    if i != Columns-1:
                        try: print("   "+str(Hidden if LayerIDs[i*Rows+key]["Visible"] == 0 else Visible) +" "+ str(i*Rows+key).zfill(2)+". "+str(LayerIDs[i*Rows+key]["Name"]).ljust(15), end = "    ")
                        except: continue
                    else:
                        if i*Rows+key >= len(LayerIDs):
                            print("")
                        else : 
                            try: print("   "+str(Hidden if LayerIDs[i*Rows+key]["Visible"] == 0 else Visible) +" "+ str(i*Rows+key).zfill(2)+". "+str(LayerIDs[i*Rows+key]["Name"]).ljust(15))
                            except: continue

            print("\n")
            
            print("  Models ———————————————————————————————————————————————————————————————————————————————————————")
            print("       ●  tID Name                        Layer          Pos             Rot          Shape/Group Data")
            print("   ---------------------------------------------------------------------------------------------")

            ShiftValues = {}

            # Model lists
            for tid in TransformIDs:

                # Prefix. R or G for Root & groups
                prefix = str("      ").rjust(7) if tid != 0 else str("R ").rjust(7)
                #add shift values
                if TransformIDs[tid]["Type"] == "Group" and tid != 0:
                    prefix = str("G ").rjust(7)
                    for groupchild in GroupIDs[TransformIDs[tid]["ChildID"]]:
                        if tid in ShiftValues.keys(): 
                            ShiftValues[groupchild] = ShiftValues[tid] + 1
                        else:
                            ShiftValues[groupchild] = 1

                Visibility = str(Hidden if TransformIDs[tid]["OverallVisibility"] == 0 else Visible).ljust(2)

                tID = str(tid).ljust(3)

                name = str(TransformIDs[tid]["Name"]).ljust(20)
                
                #Shift & name section
                if tid in ShiftValues.keys():NameSection = str(str(">"*ShiftValues[tid])+" "+Visibility+tID+name).ljust(35)
                else:NameSection = str(Visibility+tID+name).ljust(35)

                #layer
                if tid == 0: layer = str("-").ljust(15)
                else: layer = str(LayerIDs[TransformIDs[tid]["lID"]]["Name"]).ljust(15)

                pos = str(str(TransformIDs[tid]["Transform"][0][3])+","+str(TransformIDs[tid]["Transform"][1][3])+","+str(TransformIDs[tid]["Transform"][2][3])).ljust(16)

                p = int(math.degrees(math.atan2(TransformIDs[tid]["Transform"][2][1], TransformIDs[tid]["Transform"][2][2])))
                q = int(math.degrees(math.asin(-TransformIDs[tid]["Transform"][2][0])))
                r = int(math.degrees(math.atan2(TransformIDs[tid]["Transform"][1][0], TransformIDs[tid]["Transform"][0][0])))
                rot = str(str(p)+","+str(q)+","+str(r)).ljust(13)

                if TransformIDs[tid]["Type"] == "Group":ChildData = str(str(TransformIDs[tid]["ChildID"])+" - "+str(GroupIDs[TransformIDs[tid]["ChildID"]])).ljust(20)
                else:ChildData = str(TransformIDs[tid]["ChildID"]).ljust(20)
                #ChildID = str(TransformIDs[tid]["ChildID"]).ljust(8)+"  "



                stmt = prefix+NameSection+layer+pos+rot+ChildData
                print(stmt)

            print("\n")   
            print("\n  Process Ended GGs ———————————————————————————————————————————————————————")
            print("\n\n")

            # Reset Parameters --------------------------------------------------------------------------
            MaterialName = None
            VMaterial = None


            palette = []
            materials = [[0.0, 0.0, 0.0, 0.0] for _ in range(255)] # [roughness, metallic, glass, emission] * 255
            
            LayerIDs = {}      # [lID][Name] = "name", Visible = 1/0]
            TransformIDs = {}  # [tID][ChildID = sID/gID, Name = "name", Visible = 0/1, Transform = TransformMatrix4x4]
            GroupIDs = {}      # [gID] = tIDs
            ShapeIDs = {}      # [sID] = mIDs
            ModelIDs = {}      # [mID] = Model ie VoxelObject
            mID = 0

            ShiftValues = {}

            stmt = "Magicavoxel File imported" if len(paths) == 1 else str(len(paths))+" Magicavoxel Files imported"
            self.report({'INFO'}, stmt)

        for path in paths:
            import_vox(path)
        
        
        
        return {"FINISHED"}

    def draw(self, context):
        mytool = bpy.context.scene.vox_tool
        
        layout = self.layout

        # Import Maps
        BracketText = ""
        if mytool.ImportColor: BracketText+="C"
        if mytool.ImportRoughness: BracketText+="R"
        if mytool.ImportMetallic: BracketText+="M"
        if mytool.ImportEmission: BracketText+="E"
        if mytool.ImportTransmission: BracketText+="T"
        
        if BracketText == "CRMET": BracketText = "All"
        if BracketText == "": BracketText = "None"


        row = layout.row()
        row.label(icon='NODE_COMPOSITING',text = str("Map Imports (" + BracketText + ")"))
        row = layout.row()
        boks = row.box()
        row = boks.row()
        col = row.column(align = True)
        col.prop(mytool, "ImportColor")
        col.prop(mytool, "ImportRoughness")
        col.prop(mytool, "ImportMetallic")

        # Spacing
        row = col.row()      
        row.label(text = "   ")               
        row.scale_y = StaticData.SeperatorSpacing2

        col.prop(mytool, "ImportEmission")
        col.prop(mytool, "ImportTransmission")
        
        # Spacing
        row = layout.row()      
        row.label(text = "   ")               
        row.scale_y = StaticData.SeperatorSpacing1

        # Import Options
        row = layout.row()
        row.label(icon='OPTIONS',text = "Import Options")
        row = layout.row()
        boks = row.box()
        row = boks.row()
        col = row.column(align = True)
        col.prop(mytool, "ImportHidden")
        col.prop(mytool, "OriginsAtBottom")
        col.prop(mytool, "Organize")
        col.prop(mytool, "MaxMaps")

class VoxMethods():        

    def MrChecker(context):
        #Checks whether the selected 'things' are cleanable and exportable. Realtime.
        #Outputs in the form of CleaningStatus, StepStatus, ExportStatus
        mytool = context.scene.vox_tool

        # Check for object mode
        if bpy.context.mode == 'OBJECT': pass
        else: return "Enter object mode to clean","Enter object mode to clean","Enter object mode for exports"

        # Check for 2 step process running
        if FlowData.ProcessRunning == False: pass
        else: return "2 Step Process is running. Finish that first.", 1, "2 Step Process is running. Finish that first."

        # No object selected
        if len(bpy.context.selected_objects) == 0: return "Please select an object","Please select an object","Please select an object"

        # multiple objects selected
        #if len(bpy.context.selected_objects) > 1: return "Please select a single object","Please select a single object","Please select a single object"

        # active Object not in selected
        if bpy.context.active_object not in bpy.context.selected_objects:
            if len(bpy.context.selected_objects) == 1: k = "Select the object properly"
            else: k = "Select the objects properly"
            return k, k, k
        
        # Mesh Check
        NonMeshPresent = False
        for object in bpy.context.selected_objects:
            if object.type != 'MESH':
                NonMeshPresent = True 
                break
        if NonMeshPresent:
            if len(bpy.context.selected_objects) == 1: k = "Select object of type MESH"
            else: k = "Not all selected objects are MESHES"
            return k, k, k


        # Clean or Bake Check for Lazy Clean
        if len(bpy.context.selected_objects) > 1: Lazy = "Please select a single object"

        SharedStatus = len(bpy.context.selected_objects) if mytool.CommonUV or len(bpy.context.selected_objects) == 1 else "Select a single object or Enable Shared UVs"
        Lazy = SharedStatus if mytool.CleanGeo or mytool.BakeTex else "Select atleast one options above to clean"
        
        # Common UV Check for 2Step
        if len(bpy.context.selected_objects) == 1:TwoStep = 1
        else:
            if mytool.CommonUV:TwoStep = len(bpy.context.selected_objects)
            else:TwoStep = "Select a single object or Enable Shared UVs"

        return Lazy, TwoStep, len(bpy.context.selected_objects) if len(bpy.context.selected_objects) == 1 else "Please select a single object"
        
        
    def MrModelTypeChecker(ObjectList):
        #Checks and returns the model type for solo and list of models. Removes doubles and fixes normals in the process too! Not realtime.

        if len(ObjectList)>0:
            ActiveObj = bpy.context.active_object
            TypeList = set()
            FlowData.VertexCountInitialX = 0

            for obj in ObjectList:
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = None

                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                
                FlowData.VertexCountInitialX += len(obj.data.vertices)

                bpy.ops.object.mode_set(mode = 'EDIT')

                #Change color att domain, merge verts, Fix normals
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.object.mode_set(mode = 'OBJECT')
                bpy.ops.geometry.attribute_convert(domain='CORNER', data_type='FLOAT_COLOR')
                bpy.ops.object.mode_set(mode = 'EDIT')

                bpy.ops.mesh.remove_doubles()
                bpy.ops.mesh.normals_make_consistent(inside=False)

                #Find ModelType
                bm = bmesh.from_edit_mesh(bpy.context.active_object.data)

                Type = "Voxel"
                try:
                    for e in bm.edges:
                        EdgeAngle = round(math.degrees(e.calc_face_angle()),3)
                        
                        if EdgeAngle == 0.0 or 89 < EdgeAngle < 91:
                            continue
                        elif 44 < EdgeAngle < 46.0 or 0 < EdgeAngle < 1 or 34 < EdgeAngle < 36 or 53 < EdgeAngle < 55 or 70 < EdgeAngle < 71:
                            Type = "MC"
                        else:
                            Type = "Non Voxel"
                            print(EdgeAngle, end = "   ")
                            break 
                except ValueError:
                    pass
                bm.free()

                TypeList.add(Type)            
                bpy.ops.object.mode_set(mode = 'OBJECT')

                # Fix Shading
                if Type == "Voxel" or "MC":
                    bpy.ops.object.shade_flat()


                if len(TypeList) > 1:
                    #select all selected objects & set the active object
                    bpy.context.view_layer.objects.active = ActiveObj
                    for obj in ObjectList:
                        obj.select_set(True)
                    return "Mixed"
                
            #select all selected objects & set the active object
            bpy.context.view_layer.objects.active = ActiveObj
            for obj in ObjectList:
                obj.select_set(True)
            return list(TypeList)[0]
    
    def ExportSummaries(context):
        #Gives out a summary of what I'm about to export along with the number of textures.

        scene = context.scene
        mytool = scene.vox_tool
        CleanStatus,StepStatus, ExportStatus = VoxMethods.MrChecker(context)

        if type(ExportStatus) == int:
            NoOfTextures = len(VoxMethods.GetTextures(context))

            ExportableMeshes = str(ExportStatus) + " Mesh" if ExportStatus == 1 else str(ExportStatus) + " Meshes"
            ExportableTextures = str(NoOfTextures) + " Texture" if NoOfTextures == 1 else str(NoOfTextures) + " Textures"
            stmt = "Export "+str(ExportableMeshes)+" with "+str(ExportableTextures)
            return stmt
        else:
            return "No Summary"
    

    def NextNamePlease(name):
        if name.rfind("_Backup") != -1:
            trail = name[name.rfind("_Backup")+7:]
            if trail == "":
                name = name[:name.rfind("_Backup")+7]+"2"
                return name
            else:
                if trail.isnumeric():
                    trail = str(int(trail)+1)
                    name = name[:name.rfind("_Backup")+7]+trail
                    return name
                else:
                    name = name + "_Backup"
                    return name
        else:
            name = name + "_Backup"
            return name

    def TriangulateModel(context):
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.object.mode_set(mode = 'OBJECT')

    def CreateCRMETS(context,C,R,M,E,T):
        mytool = bpy.context.scene.vox_tool

        # calculate the name for the CRMET material
        MaterialName = "VCMat"
        Suffix1 = "_"

        if any([C,R,M,E,T]) == False:Suffix1 += "0"
        else:
            if C:Suffix1+="C"
            if R:Suffix1+="R"
            if M:Suffix1+="M"
            if E:Suffix1+="E"
            if T:Suffix1+="T"

        MaterialName+=Suffix1
        print(MaterialName)
        print("No mat" if bpy.data.materials.get(MaterialName) is None else "Mat")
        # check material's availability
        if bpy.data.materials.get(MaterialName) is None:
            # Create New VMat, the one of this kind isn't there
            VMaterial = bpy.data.materials.new(name = MaterialName)

            VMaterial.use_nodes = True
            nodes = VMaterial.node_tree.nodes
            links = VMaterial.node_tree.links
            
            bsdf = nodes["Principled BSDF"]
            bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
            bsdf.inputs['Roughness'].default_value = 0.5
            bsdf.inputs['Metallic'].default_value = 0.0
            bsdf.inputs['Emission Strength'].default_value = 0.0
            bsdf.inputs['Transmission Weight'].default_value = 0.0

            # Create and hookup nodes if the parameters say so 
            if C:
                ColAtt_Color = nodes.new("ShaderNodeVertexColor")
                ColAtt_Color.layer_name = "Color"
                ColAtt_Color.name = "Color"
                ColAtt_Color.location = (-324,466)

                links.new(ColAtt_Color.outputs["Color"], bsdf.inputs[0])

            if M:
                ColAtt_Metallic = nodes.new("ShaderNodeVertexColor")
                ColAtt_Metallic.layer_name = "Metallic"
                ColAtt_Metallic.name = "Metallic"
                ColAtt_Metallic.location = (-324,352)

                links.new(ColAtt_Metallic.outputs["Color"], bsdf.inputs[1])

            if R:
                ColAtt_Roughness = nodes.new("ShaderNodeVertexColor")
                ColAtt_Roughness.layer_name = "Roughness"
                ColAtt_Roughness.name = "Roughness"
                ColAtt_Roughness.location = (-324,238)

                links.new(ColAtt_Roughness.outputs["Color"], bsdf.inputs[2])

            if T:
                ColAtt_Transmission = nodes.new("ShaderNodeVertexColor")
                ColAtt_Transmission.layer_name = "Transmission"
                ColAtt_Transmission.name = "Transmission"
                ColAtt_Transmission.location = (-324,10)

                links.new(ColAtt_Transmission.outputs["Color"], bsdf.inputs[17])

            if E:
                ColAtt_Emission = nodes.new("ShaderNodeVertexColor")
                ColAtt_Emission.layer_name = "Emission"
                ColAtt_Emission.name = "Emission"
                ColAtt_Emission.location = (-324,-104)

                links.new(ColAtt_Emission.outputs["Color"], bsdf.inputs[27])
                if C:
                    links.new(ColAtt_Color.outputs["Color"], bsdf.inputs[26])
        else: 
            # if the material is already there
            VMaterial = bpy.data.materials.get(MaterialName)
        
        return VMaterial


    def JoinModels(context):
        bpy.ops.object.mode_set(mode = 'OBJECT')
        ObjArray = bpy.context.selected_objects
        ObjActive = bpy.context.view_layer.objects.active
        
        OG3DCursorPos = [round(bpy.context.scene.cursor.location.x,2),round(bpy.context.scene.cursor.location.y,2),round(bpy.context.scene.cursor.location.z,2)]

        # Run the loop of making vertex groups & Storing OriginPositionData
        for Obj in ObjArray:
            bpy.ops.object.select_all(action='DESELECT')
            Obj.select_set(True)
            bpy.context.view_layer.objects.active = Obj
            
            bpy.ops.object.mode_set(mode = 'EDIT')
            
            Obj.vertex_groups.new(name = Obj.name)
            
            # assiggn the whole object in there
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode = 'OBJECT')

            #Set the cursor to the obj origin, store the location
            FlowData.CommonUVOrigins[str(Obj.name)] = [round(Obj.location.x,2),round(Obj.location.y,2),round(Obj.location.z,2)]

        bpy.context.scene.cursor.location = OG3DCursorPos

        
        #before joining, add VCMat_0 on objects that dont have any material
        for obj in ObjArray:
            if obj.type == 'MESH':
                if len(obj.data.materials) == 0:
                    # No material slots
                    obj.data.materials.append(VoxMethods.CreateCRMETS(context,False,False,False,False,False))
                else:
                    # check for empty mat slots - if present, kill em
                    VoxMethods.ClearEmptyMaterialSlots(obj)
        
        # join all them objects
        bpy.ops.object.select_all(action='DESELECT')
        for Obj in ObjArray:
            Obj.select_set(True)
        bpy.context.view_layer.objects.active = ObjActive
        
        bpy.ops.object.join()
        
        # Rename as The Set 
        bpy.context.view_layer.objects.active.name = ObjActive.name+"Set"


    def SplitModels(context,):
        # Set the active object to the one you want to work with
        obj = bpy.context.active_object

        # Ensure the object is in object mode
        #bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='OBJECT')

        # Get the vertex groups
        vertex_groups = obj.vertex_groups

        OG3DCursorPos2 = [round(bpy.context.scene.cursor.location.x,2),round(bpy.context.scene.cursor.location.y,2),round(bpy.context.scene.cursor.location.z,2)]

        # Iterate through all vertex groups
        SplitUpModels = []
        for Vgroup in vertex_groups:
            VertGrupName = Vgroup.name
            
            # Create a new object by duplicating the original object
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()
            bpy.context.collection.objects.link(new_obj)
            
            # Select the geo first based on the Vgroups
            bpy.ops.object.select_all(action='DESELECT')
            new_obj.select_set(True)
            bpy.context.view_layer.objects.active = new_obj

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group=VertGrupName)
            bpy.ops.object.vertex_group_select()

            # delete the unnecessary geo 
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Clear out all vertex groups in the new obj
            for v_group in new_obj.vertex_groups:
                new_obj.vertex_groups.remove(v_group)

            # set the cursor location to the dict vector
            bpy.context.scene.cursor.location = FlowData.CommonUVOrigins[str(Vgroup.name)]
            # set the origin loation to the cursor location
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')


            # remove VCMat_0 if present on the model
            if len(new_obj.data.materials) > 0:
                # check for emptyVCMat_0 mat slots - if present, kill em
                for slot in new_obj.material_slots:
                    if slot.name == "VCMat_0": new_obj.data.materials.pop(index = slot.slot_index)
            
            # Rename the new object with the vertex group name
            new_obj.name = VertGrupName
            SplitUpModels.append(new_obj)

        bpy.context.scene.cursor.location = OG3DCursorPos2

        # Delete the OG Obj
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.delete(use_global=False)

        return SplitUpModels
    
    def ApplySplitToBothObjects(context):
        scene = context.scene
        mytool = scene.vox_tool
        #If no backup, just add the dupe to the global list
        if mytool.CreateBackup == False: FlowData.CommonUVDupeObjects = [FlowData.DupeObj]
        else:
            # make the dupe active & visible
            FlowData.DupeObj.hide_set(False)
            bpy.ops.object.select_all(action='DESELECT')
            FlowData.DupeObj.select_set(True)
            bpy.context.view_layer.objects.active = FlowData.DupeObj
            
            # split & rename dupes & add it to the global dupes list
            ObjectsToBeRenamed = VoxMethods.SplitModels(context)
            for obj in ObjectsToBeRenamed: obj.name = VoxMethods.NextNamePlease(obj.name)

            FlowData.CommonUVDupeObjects = ObjectsToBeRenamed
            
        # split the main models as well
        bpy.ops.object.select_all(action='DESELECT')
        FlowData.MainObj.select_set(True)
        bpy.context.view_layer.objects.active = FlowData.MainObj
        VoxMethods.SplitModels(Context)

    def ClearEmptyMaterialSlots(objekt):
        if len(objekt.material_slots) == 1:
            if objekt.material_slots[0].name == "": objekt.data.materials.clear()
        else:
            i = 0
            while i<len(objekt.material_slots):
                if objekt.material_slots[i].name == "":
                    objekt.data.materials.pop(index = i)
                else:
                    i+= 1

        # if all were emptied, There wll remain a single empty one. Get rid of it.
        if len(objekt.material_slots) == 1:
            if objekt.material_slots[0].name == "": objekt.data.materials.clear()


    def ModelFixing(context):
        
        FlowData.ProcessRunning = True
        
        # set main object and its name
        FlowData.MainObj = bpy.context.active_object
        FlowData.MainObjName = bpy.context.active_object.name
        FlowData.MainObj.hide_render = False

        for ColAtt in FlowData.MainObj.data.color_attributes:
            FlowData.MaterialMaps.append(ColAtt.name)

        # Clear empty material slots
        VoxMethods.ClearEmptyMaterialSlots(FlowData.MainObj)
        
        # duplicate the main obj, set and name dupe
        bpy.ops.object.duplicate()
        FlowData.DupeObj = bpy.context.active_object

        #Backup Name calculation
        FlowData.DupeObj.name = VoxMethods.NextNamePlease(FlowData.MainObjName)
        FlowData.DupeObjName = FlowData.DupeObj.name

        #Hide Dupe obj
        FlowData.DupeObj.hide_set(True)

        bpy.ops.object.select_all(action='DESELECT')

        # Remove color attributes from the main
        while FlowData.MainObj.data.color_attributes: FlowData.MainObj.data.color_attributes.remove(FlowData.MainObj.data.color_attributes[0])
        

        FlowData.MainObj.select_set(True)
        bpy.context.view_layer.objects.active = FlowData.MainObj

    def MaterialSetUp(context):
        
        scene = context.scene
        mytool = scene.vox_tool

        # analyse the current material on MainObj. make a bakelist based on the colAtt nodes present
        for mat in FlowData.MainObj.data.materials:
            if mat is None: continue
            else:  mat.use_nodes == True

            for node in mat.node_tree.nodes:
                if node.type == 'VERTEX_COLOR' and node.mute == False:
                    if node.layer_name != None:
                        if node.layer_name == "Color" or node.layer_name == "Col":
                            FlowData.BakeList.append("Color")
                        if node.layer_name == "Roughness":
                            FlowData.BakeList.append("Roughness")
                        if node.layer_name == "Metallic":
                            FlowData.BakeList.append("Metallic")
                        if node.layer_name == "Emission":
                            FlowData.BakeList.append("Emission")
                        if node.layer_name == "Transmission":
                            FlowData.BakeList.append("Transmission")

        FlowData.BakeList.append("Color")   # Color should always be present)
        FlowData.BakeList = list(set(FlowData.BakeList))
                        
                        

        # remove then add a new material
        FlowData.MainObj.data.materials.clear()

        ImageMaterial = bpy.data.materials.new(name = FlowData.MainObj.name + "_Material")
        #bpy.ops.object.material_slot_add()

        FlowData.MainObj.data.materials.append(ImageMaterial)

        # edit the material
        ImageMaterial.use_nodes = True
        nodes = ImageMaterial.node_tree.nodes

        #PrincipledBSDF
        PrincipledBSDF = nodes.get('Principled BSDF')
        PrincipledBSDF.location = (370,195)

        # MaterialOutput
        MO = nodes.get('Material Output')
        MO.location = (680,220)

        # All the Image Texture Nodes & their links
        Links = ImageMaterial.node_tree.links
        
        #print("MaterialMaps ",FlowData.MaterialMaps)
        #print("BakeList ",FlowData.BakeList)

        # Make image tex nodes for every map in Bakelist
        for Map in FlowData.BakeList:
            if Map == "Color":
                ImageTextureNode = nodes.new(type = 'ShaderNodeTexImage')
                ImageTextureNode.name = "Color"
                ImageTextureNode.interpolation = 'Closest' if FlowData.ModelType == "Voxel" else 'Linear'
                ImageTextureNode.location = (-434,695)

                Links.new(ImageTextureNode.outputs[0], PrincipledBSDF.inputs[0])

                Links.new(ImageTextureNode.outputs[0], PrincipledBSDF.inputs['Emission Color'])

            if Map == "Roughness":
                ImageTextureNode = nodes.new(type = 'ShaderNodeTexImage')
                ImageTextureNode.name = "Roughness"
                ImageTextureNode.interpolation = 'Closest'
                ImageTextureNode.location = (-434,143)

                Links.new(ImageTextureNode.outputs[0], PrincipledBSDF.inputs[2])

            if Map == "Metallic":
                ImageTextureNode = nodes.new(type = 'ShaderNodeTexImage')
                ImageTextureNode.name = "Metallic"
                ImageTextureNode.interpolation = 'Closest'
                ImageTextureNode.location = (-434,419)

                Links.new(ImageTextureNode.outputs[0], PrincipledBSDF.inputs[1])

            if Map == "Emission":
                ImageTextureNode = nodes.new(type = 'ShaderNodeTexImage')
                ImageTextureNode.name = "Emission"
                ImageTextureNode.interpolation = 'Closest'
                ImageTextureNode.location = (-115,-496)

                MathNode = nodes.new(type = 'ShaderNodeMath')
                MathNode.name = "EmissionMultiplier"
                MathNode.label = "Emission Strength"
                MathNode.operation = 'MULTIPLY'
                MathNode.location = (144,-496)

                Links.new(ImageTextureNode.outputs[0], MathNode.inputs[0])
                Links.new(MathNode.outputs[0], PrincipledBSDF.inputs[27])

                MathNode.inputs[1].default_value = mytool.EmitStrength
            
            if Map == "Transmission":
                ImageTextureNode = nodes.new(type = 'ShaderNodeTexImage')
                ImageTextureNode.name = "Transmission"
                ImageTextureNode.interpolation = 'Closest'
                ImageTextureNode.location = (-115,-220)

                Links.new(ImageTextureNode.outputs[0], PrincipledBSDF.inputs[17])
            



        #l3 = Links.new(ImageTextureNode.outputs[0], MixRGB.inputs[1])
        l4 = Links.new(PrincipledBSDF.outputs[0], MO.inputs[0])
        
        # Link Set Default emit strength at the start

            
    def UVProjection(context):

        scene = context.scene
        mytool = scene.vox_tool
        
        bpy.ops.object.select_all(action='DESELECT')
        
        FlowData.MainObj.select_set(True)
        bpy.context.view_layer.objects.active = FlowData.MainObj

        #remove the base material on main if no bake texture is going on
        if FlowData.CleanType == "Lazy" and mytool.BakeTex == False:
            FlowData.MainObj.data.materials.clear()
        
        # Project UVs based on the selected Method
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        if FlowData.ModelType == "Voxel" and mytool.UVMethod == "smart": 
            bpy.ops.uv.smart_project(margin_method='SCALED', island_margin=0)
        else:bpy.ops.uv.cube_project(cube_size=1)


        bpy.ops.uv.select_all(action='SELECT')

        if FlowData.ModelType == "Voxel": bpy.ops.uv.pack_islands(rotate=mytool.RotateUV,scale = True, rotate_method='CARDINAL', margin=0, shape_method='CONVEX')
        elif FlowData.ModelType == "MC": bpy.ops.uv.pack_islands(rotate=True,rotate_method='CARDINAL',scale = True, margin=1/128, shape_method='CONCAVE')
        else: bpy.ops.uv.pack_islands(rotate=True, rotate_method='ANY', scale = True, margin=1/128, shape_method='CONCAVE')

        bpy.ops.object.mode_set(mode = 'OBJECT')

        # Decide texture size for different model
        if FlowData.ModelType == "Voxel":

            bpy.ops.object.mode_set(mode = 'EDIT')

            ob = FlowData.MainObj
            bm = bmesh.from_edit_mesh(ob.data)


            bpy.ops.mesh.select_all(action='DESELECT')

            FlowData.SmallestEdge = None
            FlowData.SmallestEdgeLength = 1000000000000.0

            for e in bm.edges:
                if e.calc_length() < FlowData.SmallestEdgeLength:
                    bpy.ops.mesh.select_all(action='DESELECT')
                    FlowData.SmallestEdgeLength = e.calc_length()
                    e.select = True
                    FlowData.SmallestEdge = e

            uv_layer = bm.loops.layers.uv.active

            a = FlowData.SmallestEdge.link_loops[0][uv_layer].uv
            b = FlowData.SmallestEdge.link_loops[0].link_loop_next[uv_layer].uv

            FractionDistance = math.dist(a, b)

            #print("Fractal Dist",FractionDistance)
            FlowData.ApproxLen = 1/FractionDistance
            bm.free()

            bpy.ops.object.mode_set(mode = 'OBJECT')

            # Pick an image resolution
            if mytool.ResolutionSet == 'Stan':
                for resolution in StaticData.StandardBakeResolutions:
                    if FlowData.ApproxLen <= resolution:
                        FlowData.AutoRes = resolution
                        break
            else:
                FlowData.AutoRes = math.ceil(FlowData.ApproxLen)
            #print(FlowData.AutoRes)

            #Apply Multiplier to get the final result
            FlowData.FinalTextureSize = FlowData.AutoRes * int(mytool.TextureScaleMultiplier)
            bpy.ops.object.mode_set(mode = 'OBJECT')
        else:
            FlowData.FinalTextureSize = int(mytool.MCNVResolution)

        # Generate textures & assign them their nodes, if image baking is enabled
        if (FlowData.CleanType == "Lazy" and mytool.BakeTex == True) or (FlowData.CleanType == "2Step"):
            #print("UV Proj", FlowData.CleanType, mytool.BakeTex)
            for Map in FlowData.BakeList:
                if Map == "Color":
                    FlowData.GeneratedTex_Color = bpy.data.images.new(FlowData.MainObj.name + "_Color", int(FlowData.FinalTextureSize), int(FlowData.FinalTextureSize), alpha = mytool.AlphaBool)
                    bpy.data.images[FlowData.MainObj.name + "_Color"].generated_color = (mytool.BaseColor[0],mytool.BaseColor[1],mytool.BaseColor[2],mytool.BaseColor[3])
                    
                    FlowData.MainObj.data.materials[0].node_tree.nodes["Color"].image = FlowData.GeneratedTex_Color

                if Map == "Roughness":
                    FlowData.GeneratedTex_Roughness = bpy.data.images.new(FlowData.MainObj.name + "_Roughness", int(FlowData.FinalTextureSize), int(FlowData.FinalTextureSize), alpha = False)
                    bpy.data.images[FlowData.MainObj.name + "_Roughness"].generated_color = (0,0,0,1)
                    
                    FlowData.MainObj.data.materials[0].node_tree.nodes["Roughness"].image = FlowData.GeneratedTex_Roughness
                    FlowData.MainObj.data.materials[0].node_tree.nodes["Roughness"].image.colorspace_settings.name = 'Non-Color'


                if Map == "Metallic":
                    FlowData.GeneratedTex_Metallic = bpy.data.images.new(FlowData.MainObj.name + "_Metallic", int(FlowData.FinalTextureSize), int(FlowData.FinalTextureSize), alpha = False)
                    bpy.data.images[FlowData.MainObj.name + "_Metallic"].generated_color = (0,0,0,1)
                    
                    FlowData.MainObj.data.materials[0].node_tree.nodes["Metallic"].image = FlowData.GeneratedTex_Metallic
                    FlowData.MainObj.data.materials[0].node_tree.nodes["Metallic"].image.colorspace_settings.name = 'Non-Color'

                if Map == "Emission":
                    FlowData.GeneratedTex_Emisson = bpy.data.images.new(FlowData.MainObj.name + "_Emission", int(FlowData.FinalTextureSize), int(FlowData.FinalTextureSize), alpha = False)
                    bpy.data.images[FlowData.MainObj.name + "_Emission"].generated_color = (0,0,0,1)
                    
                    FlowData.MainObj.data.materials[0].node_tree.nodes["Emission"].image = FlowData.GeneratedTex_Emisson
                    FlowData.MainObj.data.materials[0].node_tree.nodes["Emission"].image.colorspace_settings.name = 'Non-Color'
                
                if Map == "Transmission":
                    FlowData.GeneratedTex_Transmission = bpy.data.images.new(FlowData.MainObj.name + "_Transmission", int(FlowData.FinalTextureSize), int(FlowData.FinalTextureSize), alpha = False)
                    bpy.data.images[FlowData.MainObj.name + "_Transmission"].generated_color = (0,0,0,1)
                    
                    FlowData.MainObj.data.materials[0].node_tree.nodes["Transmission"].image = FlowData.GeneratedTex_Transmission
                    FlowData.MainObj.data.materials[0].node_tree.nodes["Transmission"].image.colorspace_settings.name = 'Non-Color'


        #  Pick an active texture to be put up in the uv editor
            if FlowData.GeneratedTex_Color != None:
                FlowData.GeneratedTex_Active = FlowData.GeneratedTex_Color
            elif FlowData.GeneratedTex_Roughness != None:
                FlowData.GeneratedTex_Active = FlowData.GeneratedTex_Roughness
            elif FlowData.GeneratedTex_Metallic != None:
                FlowData.GeneratedTex_Active = FlowData.GeneratedTex_Metallic
            elif FlowData.GeneratedTex_Emisson != None:
                FlowData.GeneratedTex_Active = FlowData.GeneratedTex_Emisson
            elif FlowData.GeneratedTex_Transmission != None:
                FlowData.GeneratedTex_Active = FlowData.GeneratedTex_Transmission

        else:
            # No texture seems to be there
            print("lol no texture")
            pass

        #Set the active texture in the uv editor, if uv editor is available and is not being used by a Viewer Node.
        for Screen in bpy.data.screens:
            for area in Screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    if area.spaces.active.image != None and area.spaces.active.image.name == 'Viewer Node':
                        pass
                    else:
                        area.spaces.active.image = FlowData.GeneratedTex_Active

    def GeometryCleanUp(context):

        if FlowData.ModelType == "Voxel" or "MC":
            # Voxel/MC Model
            #Add and apply modifiers
            bpy.ops.object.mode_set(mode = 'OBJECT')
            FlowData.MainObj.modifiers.new("MrCleaner",'DECIMATE')
            FlowData.MainObj.modifiers["MrCleaner"].decimate_type = 'DISSOLVE'
            FlowData.MainObj.modifiers["MrCleaner"].delimit = {'SHARP'}
            FlowData.MainObj.data = FlowData.MainObj.data.copy()
            bpy.ops.object.modifier_apply(modifier="MrCleaner", report=True)

            # select main
            FlowData.MainObj.select_set(False)
            FlowData.DupeObj.select_set(False)
            bpy.context.view_layer.objects.active = FlowData.MainObj
            
            # Triangulate Dissolve Loop
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            
            i = 0
            while i<StaticData.TriangulateLoops:
                bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
                bpy.ops.mesh.dissolve_limited(angle_limit=0.0872665, delimit={'SHARP'}, use_dissolve_boundaries=False)
                i+=1
            
            bpy.ops.object.mode_set(mode = 'OBJECT')
        else:
            # Non-Voxel Model
            #Add and apply modifiers
            FlowData.MainObj.modifiers.new("MrCleaner",'DECIMATE')
            FlowData.MainObj.modifiers["MrCleaner"].decimate_type = 'COLLAPSE'
            if FlowData.VertexCountInitialX > 3000:
                DecimationRatio = 0.25
            else:
                DecimationRatio = 3000/FlowData.VertexCountInitialX

            bpy.context.object.modifiers["MrCleaner"].ratio = DecimationRatio
            bpy.ops.object.modifier_apply(modifier="MrCleaner", report=True)

            # select main
            FlowData.MainObj.select_set(False)
            FlowData.DupeObj.select_set(False)
            bpy.context.view_layer.objects.active = FlowData.MainObj
           
        FlowData.VertexCountFinalX = len(FlowData.MainObj.data.vertices)

    def UVScaling(context):
        scene = context.scene
        mytool = scene.vox_tool
        #actually scale the UVs according to ScaleFactor n cursor location-------------------------------------can be done with lighter detail

        bpy.ops.object.mode_set(mode = 'EDIT')
        ob = FlowData.MainObj
        bm = bmesh.from_edit_mesh(ob.data)

        bpy.ops.mesh.select_all(action='DESELECT')

        #The NonDiagonal Function
        def NonDiagonal(v1,v2):
            if v1.x != v2.x:
                if v1.y != v2.y or v1.z != v2.z:
                    return False
                
            elif v1.y != v2.y:
                if v1.x != v2.x or v1.z != v2.z:
                    return False
                
            elif v1.z != v2.z:
                if v1.x != v2.x or v1.y != v2.y:
                    return False
            return True

        # Make a set of NonDiagonal edges
        NonDiagonalEdges = []
        for edge in bm.edges:
            v1,v2 = edge.verts
            v1co = v1.co
            v2co = v2.co
            if NonDiagonal(v1co,v2co):
                NonDiagonalEdges.append(edge)

        #Check the lengths in them if one is the longest
        bpy.ops.mesh.select_all(action='DESELECT')
        for le in NonDiagonalEdges:
            if le.calc_length() > FlowData.LargestEdgeLength:
                bpy.ops.mesh.select_all(action='DESELECT')
                FlowData.LargestEdgeLength = le.calc_length()
                le.select = True
                FlowData.LargestEdge = le

        FlowData.LargestEdgeBlocks = round(FlowData.LargestEdgeLength/FlowData.SmallestEdgeLength,0)

        uv_layer = bm.loops.layers.uv.active

        p = FlowData.LargestEdge.link_loops[0][uv_layer].uv*FlowData.AutoRes
        q = FlowData.LargestEdge.link_loops[0].link_loop_next[uv_layer].uv*FlowData.AutoRes

        FlowData.LargestUVEdgeLengthInPixels = math.dist(p, q)

        FlowData.ResizeFactor = FlowData.LargestEdgeBlocks/FlowData.LargestUVEdgeLengthInPixels
        
        bpy.ops.object.mode_set(mode = 'OBJECT')

        ob = FlowData.MainObj

        bpy.ops.object.mode_set(mode = 'EDIT')
        
        bpy.ops.uv.select_all(action='SELECT')
        bm = bmesh.from_edit_mesh(ob.data)
        uv_layer = bm.loops.layers.uv.verify()
        
        for Screen in bpy.data.screens:
            for area in Screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    area.spaces.active.cursor_location[0] = 0
                    area.spaces.active.cursor_location[1] = 0
                    area.spaces.active.pivot_point = 'CURSOR'
        
        for face in bm.faces:
            for loop in face.loops:
                loop_uv = loop[uv_layer]
                
                loop_uv.uv *= FlowData.ResizeFactor
        
        bm.free()
        bpy.ops.object.mode_set(mode = 'OBJECT')


        
        # Snap UV islands to Pixels
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        CurrentAreaType  = bpy.context.area.type
        CurrentUIType = bpy.context.area.ui_type

        bpy.context.area.type = 'IMAGE_EDITOR'
        bpy.context.area.ui_type = 'UV'

        if(FlowData.GeneratedTex_Active != None):
            bpy.context.area.spaces.active.image = FlowData.GeneratedTex_Active

            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.uv.select_all(action='SELECT')
            bpy.ops.uv.snap_selected(target='PIXELS')
        else:
            #print("NO Texture")
            pass

        bpy.context.area.type = CurrentAreaType
        bpy.context.area.ui_type = CurrentUIType

        bpy.ops.object.mode_set(mode = 'OBJECT')
        
    def TextureBake(context):

        #No material on Dupe - bake aise hi
        #Some random material on Dupe - bake diffuse aise hi
        #CRMET material on Dupe(detect using presence of image texture nodes) - bake all channels present 

        scene = context.scene
        mytool = scene.vox_tool

        # Copy Bake settings
        RenderEngine = bpy.context.scene.render.engine

        # set bake settings
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.device = 'GPU'

        bpy.context.scene.cycles.bake_type = 'EMIT'
        bpy.context.scene.render.bake.use_pass_color = True
        bpy.context.scene.render.bake.use_pass_direct = False
        bpy.context.scene.render.bake.use_pass_indirect = False

        bpy.context.scene.render.bake.use_clear = False
        bpy.context.scene.render.bake.use_selected_to_active = True
        if FlowData.ModelType == "Voxel": bpy.context.scene.render.bake.cage_extrusion = 0.001
        else: bpy.context.scene.render.bake.cage_extrusion = 0.01
        bpy.context.scene.render.bake.max_ray_distance = 0.1
        
        if FlowData.ModelType == "Voxel":
            bpy.context.scene.render.bake.margin = 0      #margin
        else:
            bpy.context.scene.render.bake.margin = FlowData.Bleed = int(int(FlowData.FinalTextureSize)/128)     # Some calculated Bleed
            bpy.context.scene.render.bake.margin_type = 'EXTEND'

        # Unhide the Dupe object
        FlowData.DupeObj.hide_set(False)

        # Select objects in order
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        FlowData.MainObj.select_set(True)
        FlowData.DupeObj.select_set(True)
        bpy.context.view_layer.objects.active = FlowData.MainObj      

        # Get mainObj NodeTree
        FlowData.MainObj.material_slots[0].material.use_nodes = True
        NodeTree = FlowData.MainObj.material_slots[0].material.node_tree

        # 1. Copy
        # 2. Clean slate
        # 3. Bake
        # 4. Reset


        # Get DupeObj Material Stats
        if len(FlowData.DupeObj.data.materials) > 0:
            # Store all the color sources from all the dupe materials into a dictionary.
            SourceData = {}

            for mat in FlowData.DupeObj.data.materials:

                # 1. Copy values - copy the PBSDF values in a dict, that would be changing during the process
                mat.use_nodes = True

                MaterialInputs = mat.node_tree.nodes['Principled BSDF'].inputs
                SourceData[mat.name] = {}
                SourceData[mat.name]["Color"] = MaterialInputs['Base Color'].links[0].from_socket if len(MaterialInputs['Base Color'].links)>0 else [MaterialInputs['Base Color'].default_value[0],MaterialInputs['Base Color'].default_value[1],MaterialInputs['Base Color'].default_value[2],1]    # bpyNode or Vec4 
                SourceData[mat.name]["Roughness"] = MaterialInputs['Roughness'].links[0].from_socket if len(MaterialInputs['Roughness'].links)>0 else MaterialInputs['Roughness'].default_value      # bpyNode or float
                SourceData[mat.name]["Metallic"] = MaterialInputs['Metallic'].links[0].from_socket if len(MaterialInputs['Metallic'].links)>0 else MaterialInputs['Metallic'].default_value      # bpyNode or float
                SourceData[mat.name]["Emission"] = MaterialInputs['Emission Strength'].links[0].from_socket if len(MaterialInputs['Emission Strength'].links)>0 else MaterialInputs['Emission Strength'].default_value    # bpyNode or float
                SourceData[mat.name]["Transmission"] = MaterialInputs["Transmission Weight"].links[0].from_socket if len(MaterialInputs["Transmission Weight"].links)>0 else MaterialInputs["Transmission Weight"].default_value    # bpyNode or float


                # 2. Clean slate - Gotta remove things which are commected to the BSDF and will cause inaccuracies in bake. (for eg, weird roughness values(plugged in or an actual value) 
                #So, kill all the links and set the values to default from the StaticData values
                if len(MaterialInputs['Base Color'].links)>0:mat.node_tree.links.remove(MaterialInputs['Base Color'].links[0]) 
                MaterialInputs['Base Color'].default_value = (1.0,1.0,1.0,1.0)

                if len(MaterialInputs['Roughness'].links)>0:mat.node_tree.links.remove(MaterialInputs['Roughness'].links[0]) 
                MaterialInputs['Roughness'].default_value = 0.5

                if len(MaterialInputs['Metallic'].links)>0:mat.node_tree.links.remove(MaterialInputs['Metallic'].links[0]) 
                MaterialInputs['Metallic'].default_value = 0.0

                if len(MaterialInputs['Emission Strength'].links)>0:mat.node_tree.links.remove(MaterialInputs['Emission Strength'].links[0]) 
                MaterialInputs['Emission Strength'].default_value = 0.0

                if len(MaterialInputs['Transmission Weight'].links)>0:mat.node_tree.links.remove(MaterialInputs['Transmission Weight'].links[0]) 
                MaterialInputs['Transmission Weight'].default_value = 0.0
                
            #print("SourceData: ",SourceData) 
        else:
            print("No Materials on Dupe")
            

        def HandleBothTheMaterialsAndBake(Map):

            # Select the Image node in Main NodeTree
            for node in NodeTree.nodes:
                if node.name == Map:
                    node.select = True
                    NodeTree.nodes.active = node
                else:
                    node.select = False

            # Make a new link in all Dupe materials from whatever is connected in the source to PBSDF color
            for mat in FlowData.DupeObj.data.materials:
                Source = SourceData[mat.name][Map]
                PlugInHere = 0

                #remove whatever is connected first
                if len(mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].links)>0: mat.node_tree.links.remove(mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].links[0]) 

                if type(Source) == list:
                    mat.node_tree.nodes['Principled BSDF'].inputs[PlugInHere].default_value = Source
                elif type(Source) == float:
                    mat.node_tree.nodes['Principled BSDF'].inputs[PlugInHere].default_value[0] = Source
                    mat.node_tree.nodes['Principled BSDF'].inputs[PlugInHere].default_value[1] = Source
                    mat.node_tree.nodes['Principled BSDF'].inputs[PlugInHere].default_value[2] = Source
                    mat.node_tree.nodes['Principled BSDF'].inputs[PlugInHere].default_value[3] = 1
                else:                      #type(Source) == bpy.types.NodeSocketColor possibly some bpy node type like color, shader, float etc
                    try: mat.node_tree.links.new(Source, mat.node_tree.nodes['Principled BSDF'].inputs[PlugInHere])
                    except: pass
            
            # Diffuse Bake
            bpy.ops.object.bake(type='DIFFUSE')

        # 3. Bake - Baking all the maps using the function
        for Key in FlowData.BakeList:
            HandleBothTheMaterialsAndBake(Key)

        def LoadGivenDatainGivenMaterialMap(GivenData, DestinationMap):
            if type(SourceData[mat.name][GivenData]) == list : MatNodes['Principled BSDF'].inputs[DestinationMap].default_value = SourceData[mat.name][GivenData]    # Plug in a Vec4
            elif type(SourceData[mat.name][GivenData]) == float : MatNodes['Principled BSDF'].inputs[DestinationMap].default_value = SourceData[mat.name][GivenData]   # Plug in a float
            else:
                try: MatLinks.new(SourceData[mat.name][GivenData],  MatNodes['Principled BSDF'].inputs[DestinationMap])     # plug in a bpyNode
                except: pass
                
        # 4. Reset - Load all the data from the dictiomary, plug those values back in the diffuse channel. Do this for all materials
        for mat in FlowData.DupeObj.data.materials:
            MatLinks = mat.node_tree.links
            MatNodes = mat.node_tree.nodes

            LoadGivenDatainGivenMaterialMap("Color", "Base Color")
            LoadGivenDatainGivenMaterialMap("Roughness", "Roughness")
            LoadGivenDatainGivenMaterialMap("Metallic", "Metallic")
            LoadGivenDatainGivenMaterialMap("Emission", "Emission Strength")
            LoadGivenDatainGivenMaterialMap("Transmission", "Transmission Weight")

        #Pack the images for safety
        try:
            for Node in NodeTree.nodes:
                if Node.name in FlowData.BakeList:
                    Node.image.pack()
        except:
            pass

        # Hide the Dupe
        FlowData.DupeObj.hide_set(True)
        
        bpy.context.scene.render.engine = RenderEngine
        
    def EndProcess(context):

        scene = context.scene
        mytool = scene.vox_tool
        
        #clear existing VColor Data in the object if it exists
        try:
            if FlowData.MainObj.data.vertex_colors.active != None:
                FlowData.MainObj.data.vertex_colors.remove(FlowData.MainObj.data.vertex_colors.active)
        except Exception: 
            pass

        
        #Print Existing FlowData n MetaData
        if FlowData.ProcessRunning:
            try:
                print('''
● CLEAN DATA
——————————————————————————————————————————————————————————————————————————''')
                if FlowData.CleanType == "2Step" and FlowData.MissingActors:
                    print("  - 2-STEP PROCESS TERMINATED DUE TO MISSING OBJECTS -")
                print("  Model    (","Target:",FlowData.MainObjName,", Source:",FlowData.DupeObjName,", ModelType:",FlowData.ModelType,")")

                if mytool.CommonUV and len(FlowData.CommonUVObjects) >0: stmt = ", CommonUV: True "+str(FlowData.CommonUVObjects)
                else:stmt = ", CommonUV: False"
                print("  Options  ( CleanType:",FlowData.CleanType,stmt,", CleanGeo/BakeTex:",mytool.CleanGeo,"/",mytool.BakeTex,", Clean/BakeTimes:",FlowData.CleanTimes,"/",FlowData.BakeTimes,")")

                print("  Cleaning (","Initial:",FlowData.VertexCountInitialX,", Final:",FlowData.VertexCountFinalX,", Reduction:",round(100-(FlowData.VertexCountFinalX*100/FlowData.VertexCountInitialX),1),"%",")")

                if FlowData.ModelType == "Voxel":
                    print("  Geometry (","SmallestEdge:",FlowData.SmallestEdgeLength,", LargestEdge:",FlowData.LargestEdgeLength,", BlocksInLargestEdge:",FlowData.LargestEdgeBlocks,")")

                    print("  Image    (","ApproxLen:",round(FlowData.ApproxLen,2),", ResolutionSet:",mytool.ResolutionSet,", AutoRes:",FlowData.AutoRes,", UpscaleFactor:",mytool.TextureScaleMultiplier,", FinalTextureSize:",FlowData.FinalTextureSize,")")
                
                    print("  UV       (","LargestUVEdgeLength(px):",FlowData.LargestUVEdgeLengthInPixels,", ResizeFactor:",FlowData.ResizeFactor,", RescaledLength(px):",FlowData.LargestUVEdgeLengthInPixels*FlowData.ResizeFactor,")","")
                else:
                    print("  Image    (","FinalTextureSize:",FlowData.FinalTextureSize," , Margin: 1/128 , Bleed:",FlowData.Bleed,")")
                
                print("  Bakelist (",str(FlowData.BakeList),")")
                #print("\n")
                print("\n  Process Ended GGs ———————————————————————————————————————————————————————")
                print("\n\n")

            except Exception as e: 
                print(e)

        #Handle the backup
        if (FlowData.CleanType == "2Step" and not FlowData.MissingActors) or (FlowData.CleanType == "Lazy"):
            
            # if the backup is to be preserved
            if mytool.CreateBackup == False: 
                FlowData.DupeObj.hide_set(False)
                bpy.ops.object.select_all(action='DESELECT')
                FlowData.DupeObj.select_set(True)
                bpy.context.view_layer.objects.active = FlowData.DupeObj
                bpy.ops.object.delete(use_global=False)
            else:

                # check for the the organisation option.
                if mytool.OrganiseBackups: #Organise models in a backup collection
                    # Find the backup collection. 
                    BackupModelCollection = bpy.data.collections.get("Vox Cleaner Backups")

                    # handle the BackupCollection instnace
                    if BackupModelCollection:   # it exists
                        try: bpy.context.scene.collection.children.link(BackupModelCollection)
                        except: pass
                    else:   # create & link to scene collection
                        BackupModelCollection = bpy.data.collections.new("Vox Cleaner Backups")
                        bpy.context.scene.collection.children.link(BackupModelCollection)
                        bpy.context.view_layer.layer_collection.children.get("Vox Cleaner Backups").exclude = True

                    # add dupe models/model to the collection
                    for Model in FlowData.CommonUVDupeObjects:
                        for OtherCollections in Model.users_collection: OtherCollections.objects.unlink(Model)
                        if Model.name not in BackupModelCollection.objects: BackupModelCollection.objects.link(Model)
                else: #just hide all them models
                    for Model in FlowData.CommonUVDupeObjects: 
                        Model.hide_set(True)
                
                        
            
        # Clear Existing FlowData n MetaData
        FlowData.ModelType = None
        FlowData.MainObj = None
        FlowData.MainObjName = None
        FlowData.DupeObj = None
        FlowData.DupeObjName = None
        FlowData.ObjArray = None
        FlowData.CommonUVObjects = []
        FlowData.CommonUVDupeObjects = []
        FlowData.CommonUVOrigins = {}

        FlowData.VertexCountInitialX = 0
        FlowData.VertexCountFinalX = 0
        
        FlowData.SmallestEdge = None
        FlowData.SmallestEdgeLength = 10000000.0

        FlowData.LargestEdge = None
        FlowData.LargestEdgeLength = 0.0
        FlowData.LargestEdgeBlocks = 0
        FlowData.LargestUVEdgeLengthInPixels = 0.0
        FlowData.ResizeFactor = 0.0
        
        FlowData.ApproxLen = 0.0
        FlowData.AutoRes = 0
        FlowData.FinalTextureSize = 0.0
        FlowData.Bleed = 0.0

        FlowData.MaterialMaps = []
        FlowData.GeneratedTex_Active = None
        FlowData.BakeList = []

        FlowData.GeneratedTex_Color = None
        FlowData.GeneratedTex_Roughness = None
        FlowData.GeneratedTex_Metallic = None
        FlowData.GeneratedTex_Emisson = None
        FlowData.GeneratedTex_Transmission = None

        FlowData.CleanTimes = 0
        FlowData.BakeTimes = 0
        FlowData.CleanType = None
        FlowData.TwoStepCommonUV = False
        FlowData.ProcessRunning = False
        FlowData.MissingActors = False
        

    def GetTextures(context):
        #Get a list of exportable textures on a model ready. No duplicates. 
        
        NodeList = []
        mytool = context.scene.vox_tool

        def CheckforTexturesWithinModels(obj,MapKey):
            try:
                if obj.data.materials[0] != None:
                    if obj.data.materials[0].node_tree.nodes[MapKey] != None:
                        if obj.data.materials[0].node_tree.nodes[MapKey].type == 'TEX_IMAGE':
                            if obj.data.materials[0].node_tree.nodes[MapKey].image != None:
                                NodeList.append(obj.data.materials[0].node_tree.nodes[MapKey])
            except: pass

        for obj in bpy.context.selected_objects:
            if mytool.ExportColor == True:
                CheckforTexturesWithinModels(obj,"Color")
            
            if mytool.ExportRoughness == True:
                CheckforTexturesWithinModels(obj,"Roughness")

            if mytool.ExportMetallic == True:
                CheckforTexturesWithinModels(obj,"Metallic")

            if mytool.ExportEmission == True:
                CheckforTexturesWithinModels(obj,"Emission")

            if mytool.ExportTransmission == True:
                CheckforTexturesWithinModels(obj,"Transmission")

        return list(set(NodeList))

    def TextureExport(context):

        scene = context.scene
        mytool = scene.vox_tool

        NodeList = VoxMethods.GetTextures(context)
        

        for Node in NodeList:
            try:
                #TargetNode = bpy.context.active_object.active_material.node_tree.nodes[MapKey]
                ObjectTexture = Node.image
                ObjectTexture.alpha_mode = 'STRAIGHT'
                FilePath = os.path.join(mytool.ExportLocation, str(ObjectTexture.name)+".png")
                ObjectTexture.file_format='PNG'
                AreaType = bpy.context.area.type
                bpy.context.area.type = 'IMAGE_EDITOR'
                bpy.context.area.spaces.active.image = ObjectTexture 
                bpy.ops.image.save_as(save_as_render=False, copy=False, filepath=FilePath,show_multiview=False, use_multiview=False)
                bpy.context.area.type = AreaType
            except error as e:
                print("Texture Export Error",e)
        
        return len(NodeList)

class ApplyVColors(bpy.types.Operator):
    """Apply the mesh's vertex colors as the base color.
Specifically made for .PLY meshes, as they have vertex color data present.

This button is context sensitive & will only appear if you have a .PLY mesh selected that has vertex color data"""
    bl_idname = "voxcleaner.applyvertexcolors"
    bl_label = "Apply Vertex Colors"
    bl_options = {'UNDO'}

    def execute(self, context):

        VMaterial = VoxMethods.CreateCRMETS(context,True, False, False, False, False)
        
        if len(bpy.context.selected_objects) > 0:
            #remove then add the material to everyone
            for x in bpy.context.selected_objects:
                if x.type == 'MESH':
                    try:
                        if len(x.data.color_attributes)==1:
                            x.data.materials.clear()
                            x.data.materials.append(VMaterial)
                            VMaterial.node_tree.nodes["Color"].layer_name = x.data.color_attributes[0].name
                            #print("Added VC Mat")
                    except:
                        pass
                    
            
            if len(bpy.context.selected_objects) == 1:
                self.report({'INFO'}, "Vertex colors applied to selected object")
            else:
                self.report({'INFO'}, "Vertex colors applied to selected objects")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Select an object first")
            return {'CANCELLED'}


class LazyClean(bpy.types.Operator):
    """Lazy Clean selected models"""
    bl_idname = "voxcleaner.lazyclean"
    bl_label = "Easy Clean"
    bl_options = {'UNDO'}

    def execute(self, context):
        
        mytool = context.scene.vox_tool
        CleanStatus,StepStatus,ExportStatus = VoxMethods.MrChecker(context)
        
        if type(CleanStatus) == int:
            pass
        else:
            self.report({'WARNING'}, CleanStatus)
            return {'CANCELLED'}


        if CleanStatus > 1 & mytool.CommonUV == True:
            
            #Check for a mixed model set
            ModelType = VoxMethods.MrModelTypeChecker(context.selected_objects)
            if ModelType == "Mixed":
                self.report({'WARNING'}, "Mixed model set, select only one type of models")
                return {'CANCELLED'}
            
            # lazy Common UV
            FlowData.CleanType = "Lazy"
            FlowData.CommonUVObjects = [obj.name for obj in context.selected_objects]

            # continue Common UV
            FlowData.ModelType = ModelType
            VoxMethods.JoinModels(context)
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.object.mode_set(mode = 'OBJECT')

            # clean Selected Object ie Object Set 
            VoxMethods.ModelFixing(context)

            if mytool.BakeTex == True:
                VoxMethods.MaterialSetUp(context)
            
            if FlowData.ModelType == "Voxel":
                VoxMethods.UVProjection(context)

                if mytool.CleanGeo == True:
                    VoxMethods.GeometryCleanUp(context)
                
                VoxMethods.UVScaling(context)
            else:
                if mytool.CleanGeo == True:
                    VoxMethods.GeometryCleanUp(context)

                VoxMethods.UVProjection(context)
                
            #Get a vert count dammit
            FlowData.VertexCountFinalX = len(FlowData.MainObj.data.vertices)

            if mytool.BakeTex == True:
                VoxMethods.TextureBake(context)

            # Split both the objects
            VoxMethods.ApplySplitToBothObjects(context)

            #Give out a feedback
            PercentageCleaning = round(100-(FlowData.VertexCountFinalX*100/FlowData.VertexCountInitialX),1)
            if FlowData.ModelType == "Voxel": stmnt = "Model Set cleaned! "+str(PercentageCleaning)+"% avg vertex reduction!"
            else: stmnt = str(FlowData.ModelType)+" Model Set cleaned! "+str(PercentageCleaning)+"% avg vertex reduction!"
            self.report({'INFO'}, stmnt)
            
            #Clean The Plate
            VoxMethods.EndProcess(context)
            
            return {'FINISHED'}
        
    
        else:
            # solo clean

            CleanPercentageArray = []
            ModelTypeSet = set()
            ObjArray = bpy.context.selected_objects
            if len(ObjArray)==1:
                
                FlowData.CleanType = "Lazy"

                # deselect everything
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = None
                
                #select ith obj
                bpy.context.view_layer.objects.active = ObjArray[0]
                ObjArray[0].select_set(True)
                FlowData.ModelType = VoxMethods.MrModelTypeChecker(context.selected_objects)
                
                # clean Selected Object
                VoxMethods.ModelFixing(context)
                ModelTypeSet.add(FlowData.ModelType)

                if mytool.BakeTex == True:
                    print("Material Set Up")
                    VoxMethods.MaterialSetUp(context)
                
                if FlowData.ModelType == "Voxel":
                    VoxMethods.UVProjection(context)

                    if mytool.CleanGeo == True:
                        VoxMethods.GeometryCleanUp(context)
                    
                    VoxMethods.UVScaling(context)
                else:
                    if mytool.CleanGeo == True:
                        VoxMethods.GeometryCleanUp(context)

                    VoxMethods.UVProjection(context)
                
                if mytool.BakeTex == True:
                    VoxMethods.TextureBake(context)
                
                #Get a vert count dammit
                FlowData.VertexCountFinalX = len(FlowData.MainObj.data.vertices)

                CleanPercentageArray.append(round(100-(FlowData.VertexCountFinalX*100/FlowData.VertexCountInitialX),1))

                VoxMethods.EndProcess(context)

            # select the object
            bpy.context.view_layer.objects.active = None
            bpy.context.view_layer.objects.active = ObjArray[0]
            bpy.ops.object.select_all(action='DESELECT')
            ObjArray[0].select_set(True)
                

            #Give out a feedback
            if len(CleanPercentageArray) == 1:     #Only one object was there
                PercentageCleaning = round(sum(CleanPercentageArray)/len(CleanPercentageArray),2)
                if list(ModelTypeSet)[0] == "Voxel": stmnt = "Model cleaned! "+str(PercentageCleaning)+"% vertex reduction!"
                else: stmnt = str(list(ModelTypeSet)[0])+" Model cleaned! "+str(PercentageCleaning)+"% vertex reduction!"
                self.report({'INFO'}, stmnt)
                return {'FINISHED'}

            elif len(CleanPercentageArray) > 1:    #Multiple objects were there
                AverageCleaning = round(sum(CleanPercentageArray)/len(CleanPercentageArray),1)
                if len(ModelTypeSet) >1: stmnt = "All Models cleaned! "+str(AverageCleaning)+"% avg vertex reduction!"
                else:
                    if list(ModelTypeSet)[0] == "Voxel": stmnt = "Models cleaned! "+str(AverageCleaning)+"% avg vertex reduction!"
                    else: stmnt = str(list(ModelTypeSet)[0]) + " Models cleaned! "+str(AverageCleaning)+"% avg vertex reduction!"
                    self.report({'INFO'}, stmnt)
            
            return {'FINISHED'}
            
class PrepareForBake(bpy.types.Operator):
    """Clean the model geometry, set-up a material and generate a new image texture and finally project pixel-perfect UVs"""
    
    bl_idname = "voxcleaner.prepareforbake"
    bl_label = "Prepare For Bake"
    bl_options = {'UNDO'}

    def execute(self, context):
        mytool = context.scene.vox_tool
        CleanStatus,StepStatus,ExportStatus = VoxMethods.MrChecker(context)
        
        # warnings & errors
        if type(StepStatus) != int:
            self.report({'WARNING'}, StepStatus)
            return {'CANCELLED'}
        
        if FlowData.ProcessRunning == True and FlowData.CleanTimes>=1:
            self.report({'WARNING'}, "A 2 Step Process is running. Finish that first.")
            return {'CANCELLED'}
        
        # Set vertex snapping to disabled before starting process
        for Screen in bpy.data.screens:
            for area in Screen.areas:
                if area.type == 'IMAGE_EDITOR' and area.ui_type == 'UV':
                    area.spaces.active.uv_editor.pixel_round_mode = 'DISABLED'

        if StepStatus > 1:
            #Check for a mixed model set
            ModelType = VoxMethods.MrModelTypeChecker(context.selected_objects)
            if ModelType == "Mixed":
                self.report({'WARNING'}, "Mixed model set, select only one type of models")
                return {'CANCELLED'}
            
            # Common UV cleaning
            FlowData.TwoStepCommonUV = True
            FlowData.CleanType = "2Step"
            FlowData.ProcessRunning = True
            FlowData.CommonUVObjects = [obj.name for obj in context.selected_objects]
            
            # COntinue Common UV
            FlowData.ModelType = ModelType
            VoxMethods.JoinModels(context)
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.object.mode_set(mode = 'OBJECT')

            # clean Selected Object ie Object Set 
            VoxMethods.ModelFixing(context)

            VoxMethods.MaterialSetUp(context)
            
            if FlowData.ModelType == "Voxel":
                VoxMethods.UVProjection(context)

                if mytool.CleanGeo == True:
                    VoxMethods.GeometryCleanUp(context)
                
                VoxMethods.UVScaling(context)
            else:
                if mytool.CleanGeo == True:
                    VoxMethods.GeometryCleanUp(context)

                VoxMethods.UVProjection(context)
                
            #Get a vert count dammit
            FlowData.VertexCountFinalX = len(FlowData.MainObj.data.vertices)

            # Set vertex snapping to pixel
            for Screen in bpy.data.screens:
                for area in Screen.areas:
                    if area.type == 'IMAGE_EDITOR' and area.ui_type == 'UV':
                        area.spaces.active.uv_editor.pixel_round_mode = 'CORNER'

            FlowData.CleanTimes = FlowData.CleanTimes+1
            # Give out a feedback
            stmnt = "Ready For Shared Texture Bake! "+str(round(100-(FlowData.VertexCountFinalX*100/FlowData.VertexCountInitialX),1))+"% vertex reduction!"
            self.report({'INFO'}, stmnt)
            return {'FINISHED'}


        if StepStatus == 1:
            # Single Model Cleaning
            FlowData.CleanType = "2Step"
            FlowData.ProcessRunning = True

            FlowData.ModelType = VoxMethods.MrModelTypeChecker(context.selected_objects)
            VoxMethods.ModelFixing(context)
            VoxMethods.MaterialSetUp(context)
            
            if FlowData.ModelType == "Voxel":
                VoxMethods.UVProjection(context)
                if mytool.CleanGeo == True: VoxMethods.GeometryCleanUp(context)
                VoxMethods.UVScaling(context)
            else:
                if mytool.CleanGeo == True: VoxMethods.GeometryCleanUp(context)
                VoxMethods.UVProjection(context)
            
            FlowData.VertexCountFinalX = len(FlowData.MainObj.data.vertices)

            # Set vertex snapping to pixel
            for Screen in bpy.data.screens:
                for area in Screen.areas:
                    if area.type == 'IMAGE_EDITOR' and area.ui_type == 'UV':
                        area.spaces.active.uv_editor.pixel_round_mode = 'CORNER'

            FlowData.CleanTimes = FlowData.CleanTimes+1
            # Give out a feedback
            stmnt = "Ready For Texture Bake! "+str(round(100-(FlowData.VertexCountFinalX*100/FlowData.VertexCountInitialX),1))+"% vertex reduction!"
            self.report({'INFO'}, stmnt)
            return {'FINISHED'}

class PostUVBake(bpy.types.Operator):
    """Bake the texture from the Source model to the Target model.
Might take some time depending on the model's voxel density"""
    bl_idname = "voxcleaner.postuvbake"
    bl_label = "Bake Texture"
    bl_options = {'UNDO'}

    def execute(self, context):
        mytool = context.scene.vox_tool
        CleanStatus,StepStatus,ExportStatus = VoxMethods.MrChecker(context)

        # warnings & errors
        if not FlowData.ProcessRunning:
            self.report({'WARNING'}, "Prepare a model for bake first!")
            return {'CANCELLED'}
            
        if FlowData.CleanTimes == 0:
            self.report({'WARNING'}, "Prepare a model for bake first!")
            return {'CANCELLED'}

        if FlowData.MissingActors:
            self.report({'WARNING'}, "Missing Objects! Re-do The process!")
            return {'CANCELLED'}
        
        # Texture Bake
        VoxMethods.TextureBake(context)
        FlowData.BakeTimes = FlowData.BakeTimes+1

        # Give out a feedback
        stmt = "Shared Texture Bake Done!" if FlowData.TwoStepCommonUV else "Texture Bake Done!"
        self.report({'INFO'}, stmt)
        return {'FINISHED'}

            
        
class VoxTerminate(bpy.types.Operator):
    """Finish the ongoing 2-Step process"""
    bl_idname = "voxcleaner.terminate"
    bl_label = "Finish Cleaning"
    bl_options = {'UNDO'}

    def execute(self, context):
        
        # warnings & errors
        if not FlowData.ProcessRunning:
            self.report({'WARNING'}, "2-Step Process is not running!")
            return {'CANCELLED'}
        
        if FlowData.TwoStepCommonUV and FlowData.MissingActors == False:
            # Split models and make a Dupe Set as well - errors possible due to missing objects
            try:
                # Split both the objects
                VoxMethods.ApplySplitToBothObjects(context)
            except error as e: print(e)
        
        # terminate cleaning
        if FlowData.MissingActors == True: stmt = "Cleaning process terminated Due to Missing Objects!"
        else: stmt = "Cleaning Done! Enjoy!"
        VoxMethods.EndProcess(context)
        self.report({'INFO'}, stmt)
        return {'FINISHED'}
        
            
        
class OpenExportFolder(bpy.types.Operator):
    """Open The specified Export Folder in OS"""
    bl_idname = "voxcleaner.openexportfolder"
    bl_label = "Open Export Folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        mytool = context.scene.vox_tool

        if len(mytool.ExportLocation) == 0:
            self.report({'WARNING'}, 'Please add an export folder')
            return {'CANCELLED'}

        ExportDirectory = os.path.realpath(bpy.path.abspath(mytool.ExportLocation))

        if not os.path.exists(ExportDirectory):
            self.report({'WARNING'}, 'Export Location does not exist, please add another location')
            return {'CANCELLED'}
            
        else:
            if sys.platform == "win32":
                os.startfile(ExportDirectory)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.call(["open",ExportDirectory])
            else:   #Linux and others
                try:
                    import subprocess
                    subprocess.Popen(['xdg-open', ExportDirectory])
                except:
                    self.report({'WARNING'}, 'Sorry, Seems like you have an unsupported Operating System')
                    return {'CANCELLED'}
                        
        return {'FINISHED'}
    

class ExportOBJ(bpy.types.Operator):
    """Export OBJ files of the selected meshes, with textures"""
    bl_idname = "voxcleaner.exportobj"
    bl_label = "Export OBJ"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        
        scene = context.scene
        mytool = scene.vox_tool
        
        #Directory checks
        if len(mytool.ExportLocation) <= 0:
            self.report({'WARNING'}, 'Please add an export location')
            return {'CANCELLED'}

        ExportDirectory = os.path.realpath(bpy.path.abspath(mytool.ExportLocation))

        if not os.path.exists(ExportDirectory):
            #mytool.ExportLocation = ""
            self.report({'WARNING'}, 'Export Location does not exist, please add another location')
            return {'CANCELLED'}

        #Mr Checker Checks
        CleanStatus,StepStatus,ExportStatus = VoxMethods.MrChecker(context)
        
        if type(ExportStatus) == int:
            ExportObjArray = bpy.context.selected_objects

            #export all Obj textures
            t=0
            try:
                TextueresExportedForThisObject = VoxMethods.TextureExport(context)
                t+=TextueresExportedForThisObject
            except Exception as e:
                print(e)
                pass
        
            #deselect everything
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = None
            
            #select ith obj
            bpy.context.view_layer.objects.active = ExportObjArray[0]
            ExportObjArray[0].select_set(True)

            #Generate file names
            FileNameOBJ=ExportObjArray[0].name+'.obj'
            #ImageFileName=ExportObjArray[i].name+'.png'

            
            
            #export Obj
            TargetFile = os.path.join(ExportDirectory, FileNameOBJ)
            bpy.ops.wm.obj_export(filepath=TargetFile, 
                                    check_existing=True, 
                                    forward_axis='NEGATIVE_Z', up_axis ='Y', 
                                    filter_glob="*.obj;*.mtl", 
                                    export_selected_objects =True, 
                                    export_animation=False, 
                                    apply_modifiers=True, 
                                    #use_edges=True, 
                                    #keep_smooth_curves=False, 
                                    #use_smooth_groups_bitflags=False,
                                    export_normals=True, 
                                    #use_uvs=True, 
                                    export_materials=True, 
                                    export_triangulated_mesh=mytool.TriangulatedExport, 
                                    export_vertex_groups=False, 
                                    #use_blen_objects=True, 
                                    export_object_groups=False, 
                                    #keep_vertex_order=False, 
                                    global_scale=1, 
                                    path_mode='AUTO')
                
            
            for obj in ExportObjArray:
                obj.select_set(True)

            MeshText = str(len(ExportObjArray)) + str(" OBJs" if len(ExportObjArray) > 1 else " OBJ")
            TextureText = str(int(t)) + str(" textures" if int(t) > 1 else " texture")

            stmt = MeshText+" with "+TextureText+" exported!"

            self.report({'INFO'}, stmt)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, ExportStatus)
            return {'CANCELLED'}

class ExportFBX(bpy.types.Operator):
    """Export FBX files of the selected meshes, with textures"""
    bl_idname = "voxcleaner.exportfbx"
    bl_label = "Export FBX"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        
        scene = context.scene
        mytool = scene.vox_tool
        
        #Directory checks
        if len(mytool.ExportLocation) <= 0:
            self.report({'WARNING'}, 'Please add an export location')
            return {'CANCELLED'}

        ExportDirectory = os.path.realpath(bpy.path.abspath(mytool.ExportLocation))

        if not os.path.exists(ExportDirectory):
            #mytool.ExportLocation = ""
            self.report({'WARNING'}, 'Export Location does not exist, please add another location')
            return {'CANCELLED'}

        #Mr Checker Checks
        CleanStatus,StepStatus, ExportStatus = VoxMethods.MrChecker(context)


        
        
        if type(ExportStatus) == int:
            ExportFbxArray = bpy.context.selected_objects

            #export fbx texture
            t = 0
            try:
                TextueresExportedForThisObject = VoxMethods.TextureExport(context)
                t+=TextueresExportedForThisObject
            except Exception as e:
                pass
            
            i = 0
            while i < len(ExportFbxArray):
                #deselect everything
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = None
                
                #select ith obj
                bpy.context.view_layer.objects.active = ExportFbxArray[i]
                ExportFbxArray[i].select_set(True)

                #Generate file names
                FileNameOBJ=ExportFbxArray[i].name+'.fbx'
                #ImageFileName=ExportFbxArray[i].name+'.png'

                
                #Export FBX
                if mytool.TriangulatedExport:
                    #Dupe n do that triangulation
                    bpy.ops.object.duplicate()
                    TriaDommi = bpy.context.active_object
                    VoxMethods.TriangulateModel(context)
                    TargetFile = os.path.join(ExportDirectory, FileNameOBJ)
                    bpy.ops.export_scene.fbx(filepath=str(TargetFile), use_selection=True, apply_scale_options = 'FBX_SCALE_ALL')
                    TriaDommi.select_set(True)
                    bpy.context.view_layer.objects.active = TriaDommi
                    bpy.ops.object.delete(use_global=False)
                else:
                    TargetFile = os.path.join(ExportDirectory, FileNameOBJ)
                    bpy.ops.export_scene.fbx(filepath=str(TargetFile), use_selection=True, apply_scale_options = 'FBX_SCALE_ALL')

                i = i+1
            
            for obj in ExportFbxArray:
                obj.select_set(True)

            MeshText = str(len(ExportFbxArray)) + str(" FBXs" if len(ExportFbxArray) > 1 else " FBX")
            TextureText = str(int(t)) + str(" textures" if int(t) > 1 else " texture")

            stmt = MeshText+" with "+TextureText+" exported!"

            self.report({'INFO'}, stmt)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, ExportStatus)
            return {'CANCELLED'}
    
class ResetSettings(bpy.types.Operator):
    """Reset all settings in this add-on"""
    bl_idname = "voxcleaner.resetsettings"
    bl_label = "Reset Settings"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        mytool = context.scene.vox_tool
        mytool.BaseColor = StaticData.BaseColorDefault
        mytool.AlphaBool = StaticData.AlphaDefault
        mytool.ResolutionSet = StaticData.ResolutionDefault
        mytool.TextureScaleMultiplier = StaticData.UpscalingDefault
        mytool.UVMethod = StaticData.UVMethodDefault
        mytool.RotateUV = StaticData.RotateUVDefault

        mytool.MCNVResolution = StaticData.MCNVResDefault
        mytool.NVDecimation = StaticData.NVDecimationDefault

        mytool.CreateBackup = StaticData.ModelBackupDefault
        mytool.OrganiseBackups = StaticData.OrganiseDefault
        mytool.TriangulatedExport = StaticData.TriangulateDefault
        mytool.EmitStrength = StaticData.EmitStrengthDefault

        return {'FINISHED'} 
    
class CheckForUpdates(bpy.types.Operator):
    """Check for add-on updates on Vox Cleaner's Official Gumroad page!
All V3.x updates are FREE!"""
    bl_idname = "voxcleaner.checkforupdates"
    bl_label = "Check For Updates!  (v3.0 current)"

    def execute(self, context):

        webbrowser.open('https://thestrokeforge.gumroad.com/l/VoxCleanerV3')

        return {'FINISHED'} 



# UI Panels  ######################################################################################################################################################################################################## UI Panels
    
class VoxImport(bpy.types.Panel):
    #bl_parent_id = "VoxCleaner_PT_main_panel"
    bl_label = "Import"
    bl_idname = "IMPORT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vox Cleaner"
    
    
    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='IMPORT')

    def draw(self, context):
        layout = self.layout

        # MainButton Box
        box = layout.box()
        row = box.row()
        row.scale_y = StaticData.BigButtonHeight
        row.operator("voxcleaner.importvox",icon = 'FILE_3D')


class VoxClean(bpy.types.Panel):
    #bl_parent_id = "VoxCleaner_PT_main_panel"
    bl_label = "Cleaner"
    
    bl_idname = "CLEANER_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vox Cleaner"
    
    
    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='SHADERFX')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.vox_tool
        
        # Apply Vert Colors button
        ShowVertexColorsButton = False
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                if len(obj.data.color_attributes) ==1:

                    if obj.data.color_attributes[0] != None:
                    # there's an object that can have the vert color material
                        ShowVertexColorsButton = True
                        break
        else:ShowVertexColorsButton = False        
                    
        if ShowVertexColorsButton == True:
            row = layout.row()
            row.scale_y = 1.2
            row.operator("voxcleaner.applyvertexcolors", icon = 'MATERIAL')


        # Common UV Button
        CommonUVRow = layout.row()
        CommonUVRow.scale_y = 1

        CommonUVRow.prop(mytool, "CommonUV")

        CleanStatus,StepStatus, ExportStatus = VoxMethods.MrChecker(context)

        if FlowData.ProcessRunning == False:CommonUVRow.enabled = True
        else:CommonUVRow.enabled = False

        # Main Button Boox
        box = layout.box()
        row = box.row()
        row.scale_y = StaticData.CleanModePaneHeight
        row.prop(mytool, "CleanMode", expand=True)
        row.enabled = True if FlowData.ProcessRunning == False else False

        if mytool.CleanMode == 'ez':
            col = box.column()
            row = col.row(align = False)
            row.prop(mytool, "CleanGeo")
            row.prop(mytool, "BakeTex")
            if type(CleanStatus) == int or CleanStatus == "Select atleast one options above to clean": row.enabled = True
            else: row.enabled = False

            row = col.row(align = False)
            row.scale_y = StaticData.BigButtonHeight
            if type(CleanStatus) == int:
                if CleanStatus == 1:
                    row.operator("voxcleaner.lazyclean",icon = 'SOLO_ON',text = 'Clean Model')
                else:
                    if mytool.CommonUV == True:
                        row.operator("voxcleaner.lazyclean",icon = 'COLOR',text = 'Clean with Shared UVs')
            else:
                row.label(icon="ERROR", text = CleanStatus)

        if mytool.CleanMode == 'hard':

            # Process Running Live View wo Clean Geo Toggle
            if FlowData.ProcessRunning:
                try: Trg = str(FlowData.MainObj.name)
                except:
                    Trg = "- Missing Object -"
                    FlowData.MissingActors = True
                try: Src = str(FlowData.DupeObj.name)
                except:
                    Src = "- Missing Object -"
                    FlowData.MissingActors = True
                    
                # Target and Source display + Clean Geo Button
                HardCol = box.column(align = True)
                ScreenRow = HardCol.row()

                # Model Names
                labels = HardCol.column(align = True)
                labels.alignment = "EXPAND"
                labels.enabled = True if FlowData.ProcessRunning  == True else False
                
                labels.label(text = "Target:  " + Trg)
                labels.label(text = "Source:  " + Src)
            else:
                # Process Not running Stale View + Clean Geo Toggle
                
                # Target and Source display + Clean Geo Button
                HardCol = box.column(align = True)
                ScreenRow = HardCol.row()
                split = ScreenRow.split(factor = 0.5)

                # Model Names
                labels = split.column(align = True)
                labels.alignment = "EXPAND"
                labels.enabled = True if FlowData.ProcessRunning  == True else False
                
                labels.label(text = "Target:  None")
                labels.label(text = "Source:  None")

                # Clean geo toggle
                props = split.column(align = True)
                CleanToggleEnabled = not(FlowData.ProcessRunning) and type(StepStatus) == int
                props.enabled = CleanToggleEnabled
                props.label(text = "   ")
                props.prop(mytool, "CleanGeo") 

            if type(StepStatus) == int:
                
                # Spacing
                row = HardCol.row()      
                row.label(text = "   ")               
                row.scale_y = StaticData.SeperatorSpacing3
                
                # Prepare for Bake
                row = HardCol.row()
                if FlowData.ProcessRunning == True and FlowData.CleanTimes>=1: row.enabled = False
                else: row.enabled = True
                row.scale_y = StaticData.BigButtonHeight
                if mytool.CommonUV == True and StepStatus >1: row.operator("voxcleaner.prepareforbake", icon = 'TOOL_SETTINGS',text = 'Prepare for Shared UV Clean')
                else: row.operator("voxcleaner.prepareforbake", icon = 'TOOL_SETTINGS')
                
                # Spacing
                row = HardCol.row()      
                row.label(text = "   ")               
                row.scale_y = StaticData.SeperatorSpacing2
                
                # Bake Texture
                row = HardCol.row()
                if FlowData.ProcessRunning == True and FlowData.CleanTimes>=1 and FlowData.MissingActors == False: row.enabled = True
                else: row.enabled = False
                row.scale_y = StaticData.BigButtonHeight
                if mytool.CommonUV and StepStatus >1: row.operator("voxcleaner.postuvbake",icon = 'TEXTURE_DATA',text = "Bake Shared Textures")
                else: row.operator("voxcleaner.postuvbake",icon = 'TEXTURE_DATA')

                # Terminate Button
                if FlowData.ProcessRunning:
                    # spacing
                    row = HardCol.row()      
                    row.label(text = "   ")               
                    row.scale_y = StaticData.SeperatorSpacing1-StaticData.SeperatorSpacing3
                    
                    row = HardCol.row()
                    row.operator("voxcleaner.terminate",icon = 'CHECKMARK')
            else:
                # Spacing
                row = HardCol.row()      
                row.label(text = "   ")               
                row.scale_y = StaticData.SeperatorSpacing4
                
                
                row = HardCol.row()
                row.label(icon = "ERROR", text = StepStatus)  
                row.scale_y = StaticData.BigButtonHeight*2 + StaticData.SeperatorSpacing2


class VoxExport(bpy.types.Panel):
    #bl_parent_id = "VoxCleaner_PT_main_panel"
    bl_label = "Export"
    bl_idname = "EXPORT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vox Cleaner"
    bl_options = {'DEFAULT_CLOSED'}
    
    
    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='FOLDER_REDIRECT')

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        mytool = scene.vox_tool

        #Export Location & Open Folder
        col = layout.column()
        
        split = col.split(factor = StaticData.VerticalSplitFactor)

        labels = split.column()
        labels.alignment = "RIGHT"
        labels.label(text = "Export Folder:")
        props = split.column()
        props.prop(mytool, "ExportLocation")
        row = col.row()
        row.scale_y = 1.2
        row.operator("voxcleaner.openexportfolder",icon = 'FILEBROWSER')

        #Spacing needed
        spacing = col.row()
        spacing.scale_y = StaticData.SeperatorSpacing1
        spacing.label(text = " ")

        # Export Maps
        header, panel = layout.panel("ExportSub", default_closed=True)
        BracketText = ""

        if mytool.ExportColor: BracketText+="C"
        if mytool.ExportRoughness: BracketText+="R"
        if mytool.ExportMetallic: BracketText+="M"
        if mytool.ExportEmission: BracketText+="E"
        if mytool.ExportTransmission: BracketText+="T"
        
        if BracketText == "CRMET": BracketText = "All"
        if BracketText == "": BracketText = "None"
        
        header.label(icon='NODE_COMPOSITING',text = str("Map Exports (" + BracketText + ")"))
        if panel:
            row = panel.row()
            col = row.column(align = True)

            col = row.column(align = True)
            col.prop(mytool, "ExportColor")
            col.prop(mytool, "ExportRoughness")
            col.prop(mytool, "ExportMetallic")

            col = row.column(align = True)
            col.prop(mytool, "ExportEmission")
            col.prop(mytool, "ExportTransmission")

        #MainButtonBox
        box = layout.box()

        CleanStatus,StepStatus, ExportStatus = VoxMethods.MrChecker(context)
        col = box.column()

        SummaryRow = col.row()
        SummaryRow.label(text = str(VoxMethods.ExportSummaries(context)))
        SummaryRow.enabled = True if type(ExportStatus) == int else False

        row = col.row()
        row.scale_y = StaticData.BigButtonHeight
        if type(ExportStatus) == int:
            #split = box.split()
            
            if ExportStatus == 1:
                
                #row.operator("voxcleaner.exportobj",icon = 'SNAP_FACE',text = "OBJ")
                row.operator("voxcleaner.exportfbx",icon = 'SNAP_FACE',text = "FBX")
                row.operator("voxcleaner.exportobj",icon = 'SNAP_FACE',text = "OBJ")
            elif ExportStatus >1:
                #row.operator("voxcleaner.exportobj",icon = 'SNAP_VERTEX',text = "OBJs")
                row.operator("voxcleaner.exportfbx",icon = 'SNAP_VERTEX',text = "FBXs")
                row.operator("voxcleaner.exportobj",icon = 'SNAP_VERTEX',text = "OBJs")
                
        else:
            row.label(icon="ERROR", text = ExportStatus)


class VoxSettings(bpy.types.Panel):
    #bl_parent_id = "VoxCleaner_PT_main_panel"
    bl_label = "General Settings"
    
    bl_idname = "SETTINGS_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vox Cleaner"
    bl_options = {'DEFAULT_CLOSED'}
    
    
    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='PREFERENCES')

    def draw(self, context):

        # Model Settings ------------------------------------------------------------------
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        scene = context.scene
        mytool = scene.vox_tool
        
        # Model Settings Panel
        col = layout.column()
        col.label(text = "Model Settings",icon = 'OBJECT_DATA')
        
        box = col.box()
        ROW = box.row(align = True)

        split = ROW.split(factor = StaticData.VerticalSplitFactor)

        labels = split.column()
        labels.alignment = "RIGHT"
        labels.label(text = "Base Color:")
        labels.label(text = "Base Image has Aplha:")

        props = split.column()
        props.prop(mytool, "BaseColor")
        props.prop(mytool, "AlphaBool")


        # Voxel Models
        header, panel = box.panel("VoxelMods", default_closed=False)
        header.label(icon='FILE_3D',text = "Voxel Models")
        if panel:
            row = panel.row(align = True)

            split = row.split(factor = StaticData.VerticalSplitFactor)

            labels = split.column(align = True)
            labels.alignment = "RIGHT"  
            labels.label(text = "Resolution Set (px):")
            labels.label(text = "Resolution Upscaling:")
            
            #Spacing
            row = labels.row()      
            row.label(text = "   ")               
            row.scale_y = StaticData.SeperatorSpacing1
            
            labels.label(text = "UV Projection Method:")
            labels.label(text = "Rotate UV Islands:")
            
            props = split.column(align = True)
            labels.alignment = "LEFT"
            props.prop(mytool, "ResolutionSet")
            props.prop(mytool, "TextureScaleMultiplier")
            
            #Spacing
            row = props.row()      
            row.label(text = "   ")               
            row.scale_y = StaticData.SeperatorSpacing1
            
            props.prop(mytool, "UVMethod")
            props.prop(mytool, "RotateUV")

        
        # MC+Non-Voxel Models
        header, panel = box.panel("MCNVMods", default_closed=False)
        header.label(icon='MONKEY',text = "MC & Non-Voxel Models")
        if panel:
            row = panel.row(align = False)

            split = row.split(factor = StaticData.VerticalSplitFactor)

            labels = split.column()
            labels.alignment = "RIGHT"  
            labels.label(text = "Resolutions:")
            labels.label(text = "Non-Voxel Decimation:")
            
            props = split.column(align = False)
            props.prop(mytool, "MCNVResolution")
            props.prop(mytool, "NVDecimation")      
        
        spacing = col.row()
        spacing.scale_y = StaticData.SeperatorSpacing2
        spacing.label(text = " ")
        
        # Preferences ------------------------------------------------------------------
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = False
        
        col = layout.column()
        col.label(text = "Preferences",icon = 'PROPERTIES')

        box = col.box()
        COL = box.column(align = True)

        COL.prop(mytool, "CreateBackup")
        
        BackupFolderRow = COL.row()
        BackupFolderRow.prop(mytool, "OrganiseBackups")
        BackupFolderRow.enabled = True if mytool.CreateBackup == True else False

        COL.prop(mytool, "TriangulatedExport")

        split = COL.split(factor = StaticData.VerticalSplitFactor)

        labels = split.column()
        labels.alignment = "RIGHT"
        labels.label(text = "Default Emit Strength:")

        props = split.column()
        props.prop(mytool, "EmitStrength")


        row = col.row()
        row.scale_y = StaticData.ButtonHeightMedium
        row.operator("voxcleaner.resetsettings",icon = 'FILE_REFRESH')

        spacing = col.row()
        spacing.scale_y = StaticData.SeperatorSpacing2
        spacing.label(text = " ")

        row = col.row()
        row.scale_y = StaticData.BigButtonHeight
        row.operator("voxcleaner.checkforupdates",icon = 'URL')




classes = [ApplyVColors,VoxProperties,LazyClean,PrepareForBake,PostUVBake,VoxTerminate,VoxImport,VoxClean,VoxExport,VoxSettings,ImportVox,ExportOBJ,ExportFBX,OpenExportFolder,ResetSettings,CheckForUpdates]
 
def menu_func_import(self, context):
    self.layout.operator(ImportVox.bl_idname, icon = "FILE_3D",text="MagicaVoxel (.vox)")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.Scene.vox_tool = bpy.props.PointerProperty(type= VoxProperties)

        
def unregister():
    del bpy.types.Scene.vox_tool
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    
 
if __name__ == "__main__":
    register()